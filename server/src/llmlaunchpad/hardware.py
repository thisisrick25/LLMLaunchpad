"""Hardware detection for LLMLaunchpad."""

import platform
import psutil
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class GPUInfo:
    """Information about a GPU."""
    name: str
    memory_total_mb: int
    memory_free_mb: int
    memory_used_mb: int
    
    @property
    def memory_total_gb(self) -> float:
        return self.memory_total_mb / 1024
    
    @property
    def memory_free_gb(self) -> float:
        return self.memory_free_mb / 1024


@dataclass
class HardwareInfo:
    """System hardware information."""
    cpu_count: int
    cpu_name: str
    ram_total_gb: float
    ram_available_gb: float
    platform: str
    gpus: List[GPUInfo]
    
    @property
    def has_gpu(self) -> bool:
        return len(self.gpus) > 0
    
    @property
    def total_vram_gb(self) -> float:
        return sum(gpu.memory_total_gb for gpu in self.gpus)
    
    def to_dict(self) -> dict:
        return {
            "cpu_count": self.cpu_count,
            "cpu_name": self.cpu_name,
            "ram_total_gb": round(self.ram_total_gb, 2),
            "ram_available_gb": round(self.ram_available_gb, 2),
            "platform": self.platform,
            "has_gpu": self.has_gpu,
            "total_vram_gb": round(self.total_vram_gb, 2),
            "gpus": [
                {
                    "name": gpu.name,
                    "memory_total_gb": round(gpu.memory_total_gb, 2),
                    "memory_free_gb": round(gpu.memory_free_gb, 2),
                }
                for gpu in self.gpus
            ],
        }


def detect_gpus() -> List[GPUInfo]:
    """Detect available GPUs."""
    gpus = []
    
    # Try NVIDIA GPUs via GPUtil
    try:
        import GPUtil
        nvidia_gpus = GPUtil.getGPUs()
        for gpu in nvidia_gpus:
            gpus.append(GPUInfo(
                name=gpu.name,
                memory_total_mb=int(gpu.memoryTotal),
                memory_free_mb=int(gpu.memoryFree),
                memory_used_mb=int(gpu.memoryUsed),
            ))
    except (ImportError, Exception):
        pass
    
    # Try Apple GPUs via system_profiler (macOS)
    if platform.system() == "Darwin":
        import subprocess
        import json
        try:
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            output = subprocess.check_output(cmd, text=True, timeout=5)
            data = json.loads(output)
            if "SPDisplaysDataType" in data:
                for item in data["SPDisplaysDataType"]:
                    if "_items" in item:
                        for gpu in item["_items"]:
                            name = gpu.get("sppci_model", "Apple GPU")
                            vram_str = gpu.get("spdisplays_vram", "0 MB")
                            # Extract number from vram_str (e.g., "1024 MB")
                            try:
                                vram_mb = int(vram_str.split()[0])
                            except (ValueError, IndexError):
                                vram_mb = 0
                            gpus.append(GPUInfo(
                                name=name,
                                memory_total_mb=vram_mb,
                                memory_free_mb=0,  # unknown
                                memory_used_mb=0,  # unknown
                            ))
        except (Exception, subprocess.SubprocessError, json.JSONDecodeError):
            pass
    
    # TODO: Add AMD ROCm detection
    
    return gpus


def get_cpu_name() -> str:
    """Get CPU name/model."""
    try:
        if platform.system() == "Windows":
            import subprocess
            output = subprocess.check_output(
                ["wmic", "cpu", "get", "name"],
                text=True,
                timeout=5,
            )
            lines = output.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
        elif platform.system() == "Darwin":
            import subprocess
            output = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                timeout=5,
            )
            return output.strip()
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except Exception:
        pass
    
    return platform.processor() or "Unknown"


def detect_hardware() -> HardwareInfo:
    """Detect all hardware information."""
    mem = psutil.virtual_memory()
    
    return HardwareInfo(
        cpu_count=psutil.cpu_count(logical=True) or 1,
        cpu_name=get_cpu_name(),
        ram_total_gb=mem.total / (1024 ** 3),
        ram_available_gb=mem.available / (1024 ** 3),
        platform=platform.system(),
        gpus=detect_gpus(),
    )


# Cached hardware info
_hardware_info: Optional[HardwareInfo] = None


def get_hardware_info(refresh: bool = False) -> HardwareInfo:
    """Get hardware information (cached unless refresh=True)."""
    global _hardware_info
    if _hardware_info is None or refresh:
        _hardware_info = detect_hardware()
    return _hardware_info
