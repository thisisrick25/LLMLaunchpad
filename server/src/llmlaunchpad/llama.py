"""llama.cpp process management for LLMLaunchpad."""

import os
import sys
import asyncio
import logging
import platform
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
from enum import Enum

from .config import get_config, get_logs_dir
from .hardware import get_hardware_info

logger = logging.getLogger(__name__)


class LlamaServerState(Enum):
    """State of the llama-server process."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class LlamaServerConfig:
    """Configuration for llama-server."""
    model_path: str
    host: str = "127.0.0.1"
    port: int = 8080
    context_size: int = 4096
    gpu_layers: int = 0
    threads: Optional[int] = None
    batch_size: int = 512
    parallel: int = 1

    # Advanced options
    flash_attention: bool = True
    mlock: bool = False
    no_mmap: bool = False

    def to_args(self) -> List[str]:
        """Convert config to command-line arguments."""
        args = [
            "--model", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(self.context_size),
            "--n-gpu-layers", str(self.gpu_layers),
            "--batch-size", str(self.batch_size),
            "--parallel", str(self.parallel),
        ]

        if self.threads:
            args.extend(["--threads", str(self.threads)])

        if self.flash_attention:
            args.append("--flash-attn")

        if self.mlock:
            args.append("--mlock")

        if self.no_mmap:
            args.append("--no-mmap")

        return args


@dataclass
class LlamaServerStatus:
    """Status information about the llama-server."""
    state: LlamaServerState
    model_path: Optional[str] = None
    model_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    gpu_layers: int = 0
    pid: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "model_path": self.model_path,
            "model_name": self.model_name,
            "host": self.host,
            "port": self.port,
            "gpu_layers": self.gpu_layers,
            "pid": self.pid,
            "error": self.error,
        }


def find_llama_server() -> Optional[str]:
    """
    Find the llama-server binary.

    Search order:
    1. Config-specified path
    2. System PATH
    3. Common installation locations
    4. LLMLaunchpad default bin directory
    5. Download if not found and auto-download is enabled
    """
    config = get_config()

    # 1. Check config
    if config.llama_binary and Path(config.llama_binary).exists():
        return config.llama_binary

    # 2. Check system PATH
    binary_names = ["llama-server", "llama-server.exe"] if platform.system() == "Windows" else ["llama-server"]

    for name in binary_names:
        found = shutil.which(name)
        if found:
            return found

    # 3. Check common locations
    system = platform.system()
    common_paths = []

    if system == "Windows":
        home = Path(os.environ.get("USERPROFILE", "~")).expanduser()
        local_app = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        common_paths = [
            local_app / "llama.cpp" / "llama-server.exe",
            home / "llama.cpp" / "build" / "bin" / "Release" / "llama-server.exe",
            home / "llama.cpp" / "build" / "bin" / "llama-server.exe",
            Path("C:/") / "llama.cpp" / "llama-server.exe",
        ]
    elif system == "Darwin":
        home = Path.home()
        common_paths = [
            Path("/usr/local/bin/llama-server"),
            Path("/opt/homebrew/bin/llama-server"),
            home / "llama.cpp" / "build" / "bin" / "llama-server",
        ]
    else:  # Linux
        home = Path.home()
        common_paths = [
            Path("/usr/local/bin/llama-server"),
            Path("/usr/bin/llama-server"),
            home / "llama.cpp" / "build" / "bin" / "llama-server",
            home / ".local" / "bin" / "llama-server",
        ]

    for path in common_paths:
        if path.exists():
            return str(path)

    # 4. Check LLMLaunchpad default bin directory (~/.llmlaunchpad/bin)
    default_bin = Path.home() / ".llmlaunchpad" / "bin"
    candidate = default_bin / ("llama-server.exe" if platform.system() == "Windows" else "llama-server")
    if candidate.exists():
        return str(candidate)

    # 5. Download if not found and auto-download is enabled
    if config.llama_auto_download:
        logger.info("llama-server not found, attempting to download...")
        downloaded_path = download_llama_server()
        if downloaded_path:
            return downloaded_path

    return None


def download_llama_server() -> Optional[str]:
    """
    Download llama-server binary from official releases.

    Returns the path to the downloaded binary or None if failed.
    """
    import urllib.request
    import tarfile
    import zipfile
    import hashlib
    import stat
    import time

    config = get_config()
    system = platform.system()
    machine = platform.machine().lower()

    # Initialize variables to avoid unbound errors
    archive_path = None

    # Determine the appropriate binary name and URL
    if system == "Windows":
        logger.warning("Automatic download for Windows is not implemented")
        return None
    elif system == "Darwin":
        if "arm" in machine or "aarch64" in machine:
            binary_name = "llama-server"
            asset_name = "llama-server-b5122-macos-arm64.zip"
        else:
            binary_name = "llama-server"
            asset_name = "llama-server-b5122-macos-x64.zip"
    else:  # Linux
        if "arm" in machine or "aarch64" in machine:
            binary_name = "llama-server"
            asset_name = "llama-server-b5122-linux-arm64.tar.gz"
        else:
            binary_name = "llama-server"
            asset_name = "llama-server-b5122-linux-x64.tar.gz"

    version = "b5122"
    base_url = config.llama_binary_source.rstrip("/")
    url = f"{base_url}/{version}/{asset_name}"

    download_dir = Path.home() / ".llmlaunchpad" / "bin"
    download_dir.mkdir(parents=True, exist_ok=True)

    binary_path = download_dir / binary_name
    if system == "Windows":
        binary_path = binary_path.with_suffix(".exe")

    try:
        logger.info(f"Downloading llama-server from {url}")

        def reporthook(block_num, block_size, total_size):
            read_so_far = block_num * block_size
            if total_size > 0:
                percent = read_so_far * 100 / total_size
                s = f"\rDownloading: {percent:.1f}% ({read_so_far} / {total_size} bytes)"
                sys.stderr.write(s)
                if read_so_far >= total_size:
                    sys.stderr.write("\n")

        archive_path = download_dir / asset_name
        urllib.request.urlretrieve(url, archive_path, reporthook)

        # Extract based on file type
        if asset_name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(download_dir)
                for extracted_file in zip_ref.namelist():
                    if binary_name in extracted_file and not extracted_file.endswith('/'):
                        extracted_path = download_dir / extracted_file
                        if extracted_path.exists():
                            shutil.move(str(extracted_path), str(binary_path))
                            break
        elif asset_name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(download_dir)
                for member in tar_ref.getmembers():
                    if binary_name in member.name and not member.isdir():
                        extracted_path = download_dir / member.name
                        if extracted_path.exists():
                            shutil.move(str(extracted_path), str(binary_path))
                            break

        if archive_path and archive_path.exists():
            archive_path.unlink()

        if system != "Windows":
            try:
                current_permissions = binary_path.stat().st_mode
                binary_path.chmod(current_permissions | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            except Exception as e:
                logger.warning(f"Could not set executable permissions: {e}")

        logger.info(f"Successfully downloaded llama-server to {binary_path}")
        return str(binary_path)

    except Exception as e:
        logger.error(f"Failed to download llama-server: {e}")
        if archive_path and archive_path.exists():
            try:
                archive_path.unlink()
            except Exception:
                pass
        if binary_path.exists():
            try:
                binary_path.unlink()
            except Exception:
                pass
        return None


class LlamaServer:
    """Manager for the llama-server process."""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._state: LlamaServerState = LlamaServerState.STOPPED
        self._config: Optional[LlamaServerConfig] = None
        self._error: Optional[str] = None
        self._log_callbacks: List[Callable[[str], None]] = []
        self._log_file: Optional[Path] = None
        self._log_task: Optional[asyncio.Task] = None

    @property
    def state(self) -> LlamaServerState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == LlamaServerState.RUNNING

    def get_status(self) -> LlamaServerStatus:
        """Get current status."""
        model_name = None
        if self._config and self._config.model_path:
            model_name = Path(self._config.model_path).name

        return LlamaServerStatus(
            state=self._state,
            model_path=self._config.model_path if self._config else None,
            model_name=model_name,
            host=self._config.host if self._config else None,
            port=self._config.port if self._config else None,
            gpu_layers=self._config.gpu_layers if self._config else 0,
            pid=self._process.pid if self._process else None,
            error=self._error,
        )

    def add_log_callback(self, callback: Callable[[str], None]):
        """Add a callback for log output."""
        self._log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable[[str], None]):
        """Remove a log callback."""
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)

    def _emit_log(self, line: str):
        """Emit a log line to all callbacks."""
        for callback in self._log_callbacks:
            try:
                callback(line)
            except Exception:
                pass

    async def _read_output(self, stream: asyncio.StreamReader, prefix: str = ""):
        """Read and process output from the process."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace").rstrip()
                log_line = f"{prefix}{decoded}" if prefix else decoded

                self._emit_log(log_line)
                logger.debug(f"llama-server: {decoded}")

                # Write to log file
                if self._log_file:
                    try:
                        with open(self._log_file, "a", encoding="utf-8") as f:
                            f.write(log_line + "\n")
                    except Exception:
                        pass

                # Check for server ready message
                if "server listening" in decoded.lower() or "listening on" in decoded.lower():
                    self._state = LlamaServerState.RUNNING
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading llama-server output: {e}")

    async def start(
        self,
        model_path: str,
        gpu_layers: int = 0,
        context_size: int = 4096,
        host: str = "127.0.0.1",
        port: int = 8080,
        **kwargs,
    ) -> bool:
        """
        Start the llama-server with the specified model.

        Returns True if started successfully.
        """
        if self._state in (LlamaServerState.RUNNING, LlamaServerState.STARTING):
            self._error = "llama-server is already running or starting"
            logger.warning(self._error)
            return False

        # Find binary
        binary = find_llama_server()
        if not binary:
            self._error = "llama-server binary not found"
            self._state = LlamaServerState.ERROR
            return False

        # Validate model path
        if not Path(model_path).exists():
            self._error = f"Model not found: {model_path}"
            self._state = LlamaServerState.ERROR
            return False

        # Build config
        self._config = LlamaServerConfig(
            model_path=model_path,
            host=host,
            port=port,
            context_size=context_size,
            gpu_layers=gpu_layers,
            **kwargs,
        )

        # Setup log file
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = logs_dir / "llama-server.log"

        # Clear previous log
        try:
            self._log_file.write_text("")
        except Exception:
            pass

        # Build command
        cmd = [binary] + self._config.to_args()

        logger.info(f"Starting llama-server: {' '.join(cmd)}")
        self._emit_log(f"[LLMLaunchpad] Starting llama-server...")
        self._emit_log(f"[LLMLaunchpad] Model: {Path(model_path).name}")
        self._emit_log(f"[LLMLaunchpad] GPU layers: {gpu_layers}")
        self._emit_log(f"[LLMLaunchpad] Context size: {context_size}")

        self._state = LlamaServerState.STARTING
        self._error = None

        # Buffer to capture logs for error reporting
        log_lines: List[str] = []

        def capture_log(line: str):
            log_lines.append(line)
            while len(log_lines) > 50:
                log_lines.pop(0)

        self.add_log_callback(capture_log)

        try:
            # Start the process with separate stdout/stderr pipes
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )

            # Start reading output from both streams
            if self._process.stdout:
                self._log_task = asyncio.create_task(
                    self._read_output(self._process.stdout, "[out] ")
                )

            if self._process.stderr:
                asyncio.create_task(
                    self._read_output(self._process.stderr, "[err] ")
                )

            # Wait a moment to see if it starts successfully
            await asyncio.sleep(1.0)

            # Check if process exited immediately
            if self._process.returncode is not None:
                await asyncio.sleep(0.5)  # Give time for logs to be captured
                error_output = "\n".join(log_lines[-20:])

                if error_output.strip():
                    self._error = f"llama-server exited with code {self._process.returncode}:\n{error_output}"
                else:
                    self._error = f"llama-server exited with code {self._process.returncode} (no output captured)"

                self._state = LlamaServerState.ERROR
                self.remove_log_callback(capture_log)
                return False

            # Give it more time to fully initialize (up to 30 seconds)
            for _ in range(30):
                if self._state == LlamaServerState.RUNNING:
                    self._emit_log(f"[LLMLaunchpad] Server ready at http://{host}:{port}")
                    self.remove_log_callback(capture_log)
                    return True

                if self._process.returncode is not None:
                    error_output = "\n".join(log_lines[-20:])
                    if error_output.strip():
                        self._error = f"llama-server exited with code {self._process.returncode}:\n{error_output}"
                    else:
                        self._error = f"llama-server exited with code {self._process.returncode} (no output captured)"
                    self._state = LlamaServerState.ERROR
                    self.remove_log_callback(capture_log)
                    return False

                await asyncio.sleep(1.0)

            # Timeout but process still running - assume it's working
            if self._process.returncode is None:
                self._state = LlamaServerState.RUNNING
                self._emit_log(f"[LLMLaunchpad] Server started at http://{host}:{port}")
                self.remove_log_callback(capture_log)
                return True

            self._error = "Timeout waiting for llama-server to start"
            self._state = LlamaServerState.ERROR
            self.remove_log_callback(capture_log)
            return False

        except Exception as e:
            self._error = str(e)
            self._state = LlamaServerState.ERROR
            logger.error(f"Failed to start llama-server: {e}")
            self.remove_log_callback(capture_log)
            return False

    async def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the llama-server.

        Returns True if stopped successfully.
        """
        if self._state == LlamaServerState.STOPPED:
            return True

        if not self._process:
            self._state = LlamaServerState.STOPPED
            return True

        self._state = LlamaServerState.STOPPING
        self._emit_log("[LLMLaunchpad] Stopping llama-server...")

        try:
            # Cancel log reading task
            if self._log_task:
                self._log_task.cancel()
                try:
                    await self._log_task
                except asyncio.CancelledError:
                    pass
                self._log_task = None

            # Try graceful shutdown first
            self._process.terminate()

            try:
                await asyncio.wait_for(self._process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                # Force kill
                logger.warning("llama-server did not stop gracefully, killing...")
                self._process.kill()
                await self._process.wait()

            self._state = LlamaServerState.STOPPED
            self._emit_log("[LLMLaunchpad] llama-server stopped")
            logger.info("llama-server stopped")
            return True

        except Exception as e:
            self._error = str(e)
            self._state = LlamaServerState.ERROR
            logger.error(f"Failed to stop llama-server: {e}")
            return False
        finally:
            self._process = None

    async def restart(self) -> bool:
        """Restart the llama-server with the same config."""
        if not self._config:
            self._error = "No configuration to restart with"
            return False

        config = self._config
        await self.stop()

        return await self.start(
            model_path=config.model_path,
            gpu_layers=config.gpu_layers,
            context_size=config.context_size,
            host=config.host,
            port=config.port,
            threads=config.threads,
            batch_size=config.batch_size,
            parallel=config.parallel,
            flash_attention=config.flash_attention,
            mlock=config.mlock,
            no_mmap=config.no_mmap,
        )

    def get_api_url(self) -> Optional[str]:
        """Get the API URL for the running server."""
        if not self.is_running or not self._config:
            return None
        return f"http://{self._config.host}:{self._config.port}"

    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        if not self.is_running:
            return False

        url = self.get_api_url()
        if not url:
            return False

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False


# Global server instance
_llama_server: Optional[LlamaServer] = None


def get_llama_server() -> LlamaServer:
    """Get the global llama-server instance."""
    global _llama_server
    if _llama_server is None:
        _llama_server = LlamaServer()
    return _llama_server
