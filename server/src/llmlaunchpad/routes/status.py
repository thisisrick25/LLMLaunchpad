"""Status and health routes."""

from fastapi import APIRouter

from ..config import get_config
from ..hardware import get_hardware_info

router = APIRouter()


@router.get("/health")
async def health():
    """Basic health check."""
    return {"status": "ok"}


@router.get("/status")
async def status():
    """Full application status."""
    config = get_config()
    hardware = get_hardware_info()
    
    return {
        "status": "ok",
        "version": "0.1.0",
        "services": {
            "llama": {"running": False, "model": None},
            "litellm": {"running": False},
        },
        "hardware": hardware.to_dict(),
        "config": {
            "mode": config.mode,
            "models_dir": config.models_dir,
            "context_size": config.context_size,
        },
    }


@router.get("/hardware")
async def hardware():
    """Get hardware information."""
    info = get_hardware_info(refresh=True)
    return info.to_dict()
