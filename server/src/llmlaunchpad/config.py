"""Configuration management for LLMLaunchpad."""

import os
import json
import platform
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


def get_app_dir() -> Path:
    """Get the platform-specific app data directory."""
    system = platform.system()
    
    if system == "Windows":
        base = Path(os.environ.get("USERPROFILE", "~"))
    else:
        base = Path.home()
    
    return base / ".llmlaunchpad"


def get_models_dir() -> Path:
    """Get the models directory."""
    return get_app_dir() / "models"


def get_data_dir() -> Path:
    """Get the data directory (for SQLite, etc.)."""
    return get_app_dir() / "data"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    return get_app_dir() / "logs"


@dataclass
class Config:
    """Application configuration."""
    
    # Paths
    models_dir: str = ""
    data_dir: str = ""
    logs_dir: str = ""
    llama_binary: str = ""
    
    # Hugging Face
    hf_token: Optional[str] = None
    
    # Performance mode: auto | gpu-heavy | cpu-only | cloud
    mode: str = "auto"
    
    # Manual overrides
    gpu_layers: Optional[int] = None
    context_size: int = 4096
    
    # LiteLLM (cloud routing)
    litellm_enabled: bool = False
    litellm_api_keys: dict = field(default_factory=dict)
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if not self.models_dir:
            self.models_dir = str(get_models_dir())
        if not self.data_dir:
            self.data_dir = str(get_data_dir())
        if not self.logs_dir:
            self.logs_dir = str(get_logs_dir())
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_config_path() -> Path:
    """Get the config file path."""
    return get_app_dir() / "config.json"


def load_config() -> Config:
    """Load configuration from file or return defaults."""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return Config.from_dict(data)
        except (json.JSONDecodeError, IOError):
            pass
    
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = load_config()
        _config.ensure_directories()
    return _config
