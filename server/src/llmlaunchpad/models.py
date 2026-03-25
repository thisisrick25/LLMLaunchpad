"""Model scanning and Hugging Face integration for LLMLaunchpad."""

import os
import re
import json
import platform
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from .config import get_config


@dataclass
class LocalModel:
    """Information about a local GGUF model."""
    name: str
    path: str
    size_bytes: int
    source: str
    quantization: Optional[str] = None
    family: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)


@dataclass
class HFModelFile:
    """A GGUF file available on Hugging Face."""
    filename: str
    size_bytes: int
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HFModel:
    """A Hugging Face repository with GGUF files."""
    repo_id: str
    files: List[HFModelFile]
    downloads: int = 0
    last_modified: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "repo_id": self.repo_id,
            "files": [f.to_dict() for f in self.files],
            "downloads": self.downloads,
            "last_modified": self.last_modified,
        }


# Recommended models for new users
RECOMMENDED_MODELS = [
    {
        "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "name": "Llama 3.1 8B Instruct",
        "description": "Meta's latest Llama model, excellent for general use",
        "sizes": ["Q4_K_M", "Q5_K_M", "Q6_K"],
        "family": "llama",
    },
    {
        "repo_id": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
        "name": "Mistral 7B Instruct v0.3",
        "description": "Fast and efficient, great instruction following",
        "sizes": ["Q4_K_M", "Q5_K_M"],
        "family": "mistral",
    },
    {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "name": "Phi-3 Mini 4K",
        "description": "Small but powerful, runs on low-end hardware",
        "sizes": ["q4"],
        "family": "phi",
    },
    {
        "repo_id": "Qwen/Qwen2-7B-Instruct-GGUF",
        "name": "Qwen2 7B Instruct",
        "description": "Strong multilingual capabilities",
        "sizes": ["q4_k_m", "q5_k_m"],
        "family": "qwen",
    },
    {
        "repo_id": "bartowski/gemma-2-9b-it-GGUF",
        "name": "Gemma 2 9B Instruct",
        "description": "Google's latest open model",
        "sizes": ["Q4_K_M", "Q5_K_M"],
        "family": "gemma",
    },
]


def get_model_sources() -> Dict[str, Path]:
    """Get all model source directories to scan."""
    system = platform.system()
    
    if system == "Windows":
        home = Path(os.environ.get("USERPROFILE", "~")).expanduser()
        local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    else:
        home = Path.home()
        local_app_data = home / ".local" / "share"
    
    sources = {
        "llmlaunchpad": Path(get_config().models_dir),
        "lm_studio": home / ".cache" / "lm-studio" / "models",
        "huggingface": home / ".cache" / "huggingface" / "hub",
        "jan": home / "jan" / "models",
    }
    
    if system == "Windows":
        sources["gpt4all"] = local_app_data / "nomic.ai" / "GPT4All"
        sources["ollama"] = home / ".ollama" / "models"
    else:
        sources["gpt4all"] = home / ".local" / "share" / "nomic.ai" / "GPT4All"
        sources["ollama"] = home / ".ollama" / "models"
    
    return sources


def parse_quantization(filename: str) -> Optional[str]:
    """Extract quantization type from filename."""
    patterns = [
        r'[._-](Q[0-9]+_K_[A-Z]+)',  # Q4_K_M, Q5_K_S, etc.
        r'[._-](Q[0-9]+_K)',          # Q4_K, Q5_K, etc.
        r'[._-](Q[0-9]+)',            # Q4, Q5, Q8, etc.
        r'[._-](q[0-9]+_k_[a-z]+)',   # lowercase variants
        r'[._-](q[0-9]+_k)',
        r'[._-](q[0-9]+)',
        r'[._-](f16)',                # Full precision
        r'[._-](f32)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None


def parse_model_family(filename: str) -> Optional[str]:
    """Extract model family from filename."""
    families = [
        "llama", "mistral", "phi", "qwen", "gemma", "falcon",
        "mpt", "starcoder", "codellama", "vicuna", "wizardlm",
        "orca", "neural", "hermes", "openchat", "zephyr",
    ]
    
    filename_lower = filename.lower()
    for family in families:
        if family in filename_lower:
            return family
    
    return None


def scan_directory_for_gguf(directory: Path, source: str) -> List[LocalModel]:
    """Recursively scan a directory for GGUF files."""
    models = []
    
    if not directory.exists():
        return models
    
    try:
        for file_path in directory.rglob("*.gguf"):
            try:
                stat = file_path.stat()
                models.append(LocalModel(
                    name=file_path.name,
                    path=str(file_path),
                    size_bytes=stat.st_size,
                    source=source,
                    quantization=parse_quantization(file_path.name),
                    family=parse_model_family(file_path.name),
                ))
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    
    return models


def scan_ollama_models(ollama_dir: Path) -> List[LocalModel]:
    """Scan Ollama models by parsing manifests and finding blob paths."""
    models = []
    
    manifests_dir = ollama_dir / "manifests" / "registry.ollama.ai" / "library"
    blobs_dir = ollama_dir / "blobs"
    
    if not manifests_dir.exists() or not blobs_dir.exists():
        return models
    
    try:
        for model_dir in manifests_dir.iterdir():
            if not model_dir.is_dir():
                continue
            
            model_name = model_dir.name
            
            # Find the latest manifest (could be 'latest' or a specific version)
            manifest_file = None
            for tag in ["latest", "instruct", "chat"]:
                potential = model_dir / tag
                if potential.exists():
                    manifest_file = potential
                    break
            
            # If no common tag found, try first file
            if not manifest_file:
                try:
                    manifest_file = next(model_dir.iterdir())
                except StopIteration:
                    continue
            
            if not manifest_file or not manifest_file.is_file():
                continue
            
            try:
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)
                
                # Find the model layer (the actual weights)
                for layer in manifest.get("layers", []):
                    media_type = layer.get("mediaType", "")
                    if "model" in media_type:
                        digest = layer.get("digest", "")
                        size = layer.get("size", 0)
                        
                        if digest:
                            # Digest format: sha256:abc123...
                            blob_name = digest.replace(":", "-")
                            blob_path = blobs_dir / blob_name
                            
                            if blob_path.exists():
                                models.append(LocalModel(
                                    name=f"ollama:{model_name}",
                                    path=str(blob_path),
                                    size_bytes=size,
                                    source="ollama",
                                    quantization=None,  # Ollama doesn't expose this easily
                                    family=parse_model_family(model_name),
                                ))
                        break
            except (json.JSONDecodeError, KeyError, IOError):
                continue
    except (OSError, PermissionError):
        pass
    
    return models


def scan_huggingface_cache(hf_dir: Path) -> List[LocalModel]:
    """Scan Hugging Face cache for GGUF files."""
    models = []
    
    if not hf_dir.exists():
        return models
    
    try:
        # HF cache structure: hub/models--user--repo/snapshots/hash/file.gguf
        for model_dir in hf_dir.iterdir():
            if not model_dir.is_dir() or not model_dir.name.startswith("models--"):
                continue
            
            # Parse repo_id from directory name
            parts = model_dir.name.replace("models--", "").split("--")
            if len(parts) >= 2:
                repo_id = f"{parts[0]}/{parts[1]}"
            else:
                repo_id = parts[0]
            
            snapshots_dir = model_dir / "snapshots"
            if not snapshots_dir.exists():
                continue
            
            # Check each snapshot
            for snapshot in snapshots_dir.iterdir():
                if not snapshot.is_dir():
                    continue
                
                for file_path in snapshot.glob("*.gguf"):
                    try:
                        stat = file_path.stat()
                        models.append(LocalModel(
                            name=file_path.name,
                            path=str(file_path),
                            size_bytes=stat.st_size,
                            source="huggingface",
                            quantization=parse_quantization(file_path.name),
                            family=parse_model_family(file_path.name),
                        ))
                    except (OSError, PermissionError):
                        continue
    except (OSError, PermissionError):
        pass
    
    return models


def scan_all_models() -> List[LocalModel]:
    """Scan all sources for GGUF models."""
    all_models = []
    sources = get_model_sources()
    
    # Scan each source
    for source_name, source_path in sources.items():
        if source_name == "ollama":
            all_models.extend(scan_ollama_models(source_path))
        elif source_name == "huggingface":
            all_models.extend(scan_huggingface_cache(source_path))
        else:
            all_models.extend(scan_directory_for_gguf(source_path, source_name))
    
    # Remove duplicates by path
    seen_paths = set()
    unique_models = []
    for model in all_models:
        if model.path not in seen_paths:
            seen_paths.add(model.path)
            unique_models.append(model)
    
    return unique_models


def get_sources_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all model sources."""
    sources = get_model_sources()
    status = {}
    
    for name, path in sources.items():
        exists = path.exists()
        model_count = 0
        
        if exists:
            if name == "ollama":
                model_count = len(scan_ollama_models(path))
            elif name == "huggingface":
                model_count = len(scan_huggingface_cache(path))
            else:
                model_count = len(scan_directory_for_gguf(path, name))
        
        status[name] = {
            "path": str(path),
            "exists": exists,
            "model_count": model_count,
        }
    
    return status


# HF Hub integration

def parse_hf_url(url_or_id: str) -> tuple[str, Optional[str]]:
    """
    Parse a Hugging Face URL or repo ID.
    
    Returns (repo_id, filename_or_none)
    
    Examples:
    - "TheBloke/Mistral-7B-GGUF" -> ("TheBloke/Mistral-7B-GGUF", None)
    - "https://huggingface.co/TheBloke/X-GGUF" -> ("TheBloke/X-GGUF", None)
    - "https://huggingface.co/TheBloke/X/blob/main/x.gguf" -> ("TheBloke/X", "x.gguf")
    """
    url_or_id = url_or_id.strip()
    
    # Remove huggingface.co prefix if present
    hf_patterns = [
        r"https?://huggingface\.co/([^/]+/[^/]+)/blob/[^/]+/(.+\.gguf)",
        r"https?://huggingface\.co/([^/]+/[^/]+)/resolve/[^/]+/(.+\.gguf)",
        r"https?://huggingface\.co/([^/]+/[^/]+)(?:/.*)?",
    ]
    
    import re
    for pattern in hf_patterns:
        match = re.match(pattern, url_or_id)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return groups[0], groups[1]
            else:
                return groups[0], None
    
    # Assume it's a repo_id
    if "/" in url_or_id:
        return url_or_id, None
    
    raise ValueError(f"Invalid Hugging Face URL or repo ID: {url_or_id}")


async def list_hf_gguf_files(repo_id: str) -> List[HFModelFile]:
    """List GGUF files in a Hugging Face repository."""
    try:
        from huggingface_hub import list_repo_files, get_paths_info
        
        # List all files in the repo
        files = list_repo_files(repo_id)
        gguf_files = [f for f in files if f.endswith(".gguf")]
        
        # Get file sizes
        result = []
        if gguf_files:
            try:
                paths_info = get_paths_info(repo_id, gguf_files, repo_type="model")
                for info in paths_info:
                    if hasattr(info, "size") and info.size:
                        result.append(HFModelFile(
                            filename=info.path,
                            size_bytes=info.size,
                        ))
                    else:
                        result.append(HFModelFile(
                            filename=info.path,
                            size_bytes=0,
                        ))
            except Exception:
                # Fallback: just return filenames without sizes
                result = [HFModelFile(filename=f, size_bytes=0) for f in gguf_files]
        
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to list files in {repo_id}: {e}")


async def search_hf_models(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Hugging Face for GGUF models."""
    try:
        from huggingface_hub import HfApi
        
        api = HfApi()
        
        # Search for models with GGUF in the name or description
        results = api.list_models(
            search=f"{query} GGUF",
            sort="downloads",
            direction=-1,
            limit=limit,
        )
        
        models = []
        for model in results:
            # Filter to only include repos likely to have GGUF files
            model_id = model.id if hasattr(model, "id") else str(model)
            if "gguf" in model_id.lower() or "GGUF" in model_id:
                models.append({
                    "repo_id": model_id,
                    "downloads": getattr(model, "downloads", 0),
                    "last_modified": str(getattr(model, "last_modified", "")),
                })
        
        return models
    except Exception as e:
        raise RuntimeError(f"Failed to search Hugging Face: {e}")


async def download_model(
    repo_id: str,
    filename: str,
    progress_callback: Optional[callable] = None,
) -> str:
    """
    Download a model from Hugging Face.
    
    Returns the local path to the downloaded file.
    """
    try:
        from huggingface_hub import hf_hub_download
        
        config = get_config()
        models_dir = Path(config.models_dir)
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Get HF token if configured
        token = config.hf_token
        
        # Download the file
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(models_dir),
            local_dir_use_symlinks=False,
            token=token,
        )
        
        return local_path
    except Exception as e:
        raise RuntimeError(f"Failed to download {filename} from {repo_id}: {e}")


def get_recommended_models() -> List[Dict[str, Any]]:
    """Get the list of recommended models."""
    return RECOMMENDED_MODELS


# Cached model list
_cached_models: Optional[List[LocalModel]] = None


def get_local_models(refresh: bool = False) -> List[LocalModel]:
    """Get all local models (cached unless refresh=True)."""
    global _cached_models
    if _cached_models is None or refresh:
        _cached_models = scan_all_models()
    return _cached_models


def find_model_by_name(name: str) -> Optional[LocalModel]:
    """Find a model by name."""
    models = get_local_models()
    for model in models:
        if model.name == name or model.path == name:
            return model
    return None
