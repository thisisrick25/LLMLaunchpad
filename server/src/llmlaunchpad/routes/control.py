"""Service control API routes for LLMLaunchpad."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json

from ..llama import get_llama_server, LlamaServerState
from ..offload import calculate_offload, PerformanceMode
from ..models import find_model_by_name
from ..config import get_config, save_config, is_dev_mode, get_dev_model_path

router = APIRouter(prefix="/control", tags=["control"])


# Request models

class StartRequest(BaseModel):
    """Request to start the llama-server."""
    model: str  # Model name or path
    mode: str = "auto"  # auto, gpu-heavy, cpu-only
    context_size: int = 4096
    gpu_layers: Optional[int] = None  # Override auto-calculation
    port: int = 8080


class StopRequest(BaseModel):
    """Request to stop the llama-server."""
    pass


class ModeRequest(BaseModel):
    """Request to change performance mode."""
    mode: str  # auto, gpu-heavy, cpu-only, cloud
    force_restart: Optional[bool] = None  # Force restart even if dynamic update possible


class OptimizeRequest(BaseModel):
    """Request to optimize GPU layers for current model and mode."""
    model: str  # Model name or path
    context_size: int = 4096


class ConfigUpdateRequest(BaseModel):
    """Request to update server configuration."""
    mode: Optional[str] = None
    context_size: Optional[int] = None
    gpu_layers: Optional[int] = None


# Routes

@router.get("/status")
async def get_status():
    """Get current llama-server status."""
    server = get_llama_server()
    status = server.get_status()
    
    return {
        **status.to_dict(),
        "api_url": server.get_api_url(),
    }


@router.post("/start")
async def start_server(request: StartRequest):
    """
    Start the llama-server with the specified model.
    
    If gpu_layers is not specified, it will be calculated based on the mode:
    - auto: Calculate based on available VRAM
    - gpu-heavy: Maximize GPU usage
    - cpu-only: No GPU layers
    """
    server = get_llama_server()
    
    # Check if already running
    if server.state == LlamaServerState.RUNNING:
        raise HTTPException(
            status_code=409,
            detail="Server is already running. Stop it first."
        )
    
    # Find the model
    model = find_model_by_name(request.model)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {request.model}"
        )
    
    # Validate context_size
    if request.context_size < 128 or request.context_size > 131072:
        raise HTTPException(
            status_code=400,
            detail="Context size must be between 128 and 131072"
        )
    
    # Validate port
    if request.port < 1 or request.port > 65535:
        raise HTTPException(
            status_code=400,
            detail="Port must be between 1 and 65535"
        )
    
    # Calculate GPU layers if not specified
    if request.gpu_layers is not None:
        gpu_layers = request.gpu_layers
    else:
        recommendation = calculate_offload(
            model_path=model.path,
            context_size=request.context_size,
            mode=request.mode,
        )
        gpu_layers = recommendation.gpu_layers
    
    # Start the server
    success = await server.start(
        model_path=model.path,
        gpu_layers=gpu_layers,
        context_size=request.context_size,
        port=request.port,
    )
    
    if not success:
        status = server.get_status()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start server: {status.error}"
        )
    
    return {
        "status": "started",
        "model": model.name,
        "gpu_layers": gpu_layers,
        "api_url": server.get_api_url(),
    }


@router.post("/stop")
async def stop_server():
    """Stop the llama-server."""
    server = get_llama_server()
    
    if server.state == LlamaServerState.STOPPED:
        return {"status": "already_stopped"}
    
    success = await server.stop()
    
    if not success:
        status = server.get_status()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop server: {status.error}"
        )
    
    return {"status": "stopped"}


@router.post("/restart")
async def restart_server():
    """Restart the llama-server with the same configuration."""
    server = get_llama_server()
    
    if server.state == LlamaServerState.STOPPED:
        raise HTTPException(
            status_code=400,
            detail="Server is not running. Use /start instead."
        )
    
    success = await server.restart()
    
    if not success:
        status = server.get_status()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart server: {status.error}"
        )
    
    return {
        "status": "restarted",
        "api_url": server.get_api_url(),
    }


@router.get("/health")
async def health_check():
    """Check if the llama-server is healthy."""
    server = get_llama_server()
    
    if not server.is_running:
        return {
            "healthy": False,
            "reason": "Server is not running",
        }
    
    is_healthy = await server.health_check()
    
    return {
        "healthy": is_healthy,
        "api_url": server.get_api_url(),
    }


@router.get("/mode")
async def get_mode():
    """Get current performance mode."""
    config = get_config()
    return {
        "mode": config.mode,
        "available_modes": [m.value for m in PerformanceMode],
    }


@router.get("/logs")
async def stream_logs():
    """
    Stream llama-server logs via Server-Sent Events.
    
    Connect to this endpoint to receive real-time log output.
    """
    server = get_llama_server()
    
    async def event_generator():
        queue: asyncio.Queue[str] = asyncio.Queue()
        
        def log_callback(line: str):
            try:
                queue.put_nowait(line)
            except asyncio.QueueFull:
                pass  # Drop logs if queue is full
        
        server.add_log_callback(log_callback)
        
        try:
            # Send initial status
            status = server.get_status()
            yield f"data: {json.dumps({'type': 'status', 'data': status.to_dict()})}\n\n"
            
            while True:
                try:
                    # Wait for log lines with timeout
                    line = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps({'type': 'log', 'data': line})}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        finally:
            server.remove_log_callback(log_callback)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/config")
async def get_server_config():
    """Get current server configuration."""
    config = get_config()
    
    # Don't expose sensitive data
    return {
        "mode": config.mode,
        "context_size": config.context_size,
        "gpu_layers": config.gpu_layers,
        "host": config.host,
        "port": config.port,
        "litellm_enabled": config.litellm_enabled,
        "models_dir": config.models_dir,
    }


@router.post("/config")
async def update_server_config(request: ConfigUpdateRequest):
    """Update server configuration."""
    print(f"DEBUG: Received request - mode: {request.mode}, context_size: {request.context_size}, gpu_layers: {request.gpu_layers}")
    config = get_config()
    print(f"DEBUG: Current config before update - mode: {config.mode}, context_size: {config.context_size}, gpu_layers: {config.gpu_layers}")
    
    if request.mode is not None:
        try:
            mode_enum = PerformanceMode(request.mode.lower())
            config.mode = mode_enum.value
            print(f"DEBUG: Set mode to {config.mode}")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {request.mode}"
            )
    
    if request.context_size is not None:
        if request.context_size < 128 or request.context_size > 131072:
            raise HTTPException(
                status_code=400,
                detail="Context size must be between 128 and 131072"
            )
        config.context_size = request.context_size
        print(f"DEBUG: Set context_size to {config.context_size}")
    
    if request.gpu_layers is not None:
        if request.gpu_layers < 0:
            raise HTTPException(
                status_code=400,
                detail="GPU layers must be >= 0"
            )
        config.gpu_layers = request.gpu_layers
        print(f"DEBUG: Set gpu_layers to {config.gpu_layers}")
    
    print(f"DEBUG: About to call save_config with config - mode: {config.mode}, context_size: {config.context_size}, gpu_layers: {config.gpu_layers}")
    save_config(config)
    print(f"DEBUG: save_config called")
    
    return {
        "message": "Configuration updated",
        "mode": config.mode,
        "context_size": config.context_size,
        "gpu_layers": config.gpu_layers,
    }


@router.post("/optimize")
async def optimize_performance(request: OptimizeRequest):
    """
    Optimize GPU layers for the current model and mode without restart.
    Recalculates optimal GPU layers and applies them via API if supported.
    """
    server = get_llama_server()
    
    # Check if server is running
    if server.state != LlamaServerState.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Server is not running. Start it first."
        )
    
    # Find the model
    model = find_model_by_name(request.model)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {request.model}"
        )
    
    # Get current config
    config = get_config()
    
    # Calculate optimal GPU layers for current mode
    recommendation = calculate_offload(
        model_path=model.path,
        context_size=request.context_size,
        mode=config.mode,
    )
    
    # Check if we can update GPU layers dynamically
    # For now, we'll require a restart as llama-server doesn't support dynamic GPU layer updates
    # In a future version, we could check if the version supports it or use SIGHUP
    
    return {
        "success": True,
        "current_gpu_layers": server.get_status().gpu_layers,
        "recommended_gpu_layers": recommendation.gpu_layers,
        "requires_restart": True,  # llama-server doesn't support dynamic GPU layer updates yet
        "recommendation": recommendation.to_dict(),
        "message": f"Optimization complete. Restart server to apply {recommendation.gpu_layers} GPU layers."
    }


@router.post("/mode")
async def set_mode(request: ModeRequest):
    """Set performance mode."""
    # Validate mode
    try:
        mode = PerformanceMode(request.mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Must be one of: {[m.value for m in PerformanceMode]}"
        )
    
    # Update config
    config = get_config()
    config.mode = mode.value
    save_config(config)
    
    # Check if we can apply mode change without restart
    server = get_llama_server()
    can_apply_dynamically = False
    requires_restart = True
    
    if server.state == LlamaServerState.RUNNING and not request.force_restart:
        # Check if we're switching between modes that could potentially be applied dynamically
        current_mode = config.mode  # This is the new mode we just set
        # For now, we'll require restart for all mode changes as llama-server 
        # doesn't support dynamic GPU layer updates
        requires_restart = True
        can_apply_dynamically = False
    
    return {
        "mode": mode.value,
        "requires_restart": requires_restart,
        "can_apply_dynamically": can_apply_dynamically,
        "message": "Mode updated. " + ("Changes will take effect immediately." if can_apply_dynamically else "Restart the server for changes to take effect.")
    }


@router.post("/dev-start")
async def dev_start():
    """
    Auto-start llama-server with dev model.
    
    Only available in development mode (LLMLAUNCHPAD_DEV=1).
    Uses sensible defaults for fast dev iteration.
    """
    if not is_dev_mode():
        raise HTTPException(
            status_code=403,
            detail="Dev-start only available in development mode"
        )
    
    server = get_llama_server()
    
    # Already running?
    if server.state == LlamaServerState.RUNNING:
        return {
            "status": "already_running",
            "api_url": server.get_api_url(),
        }
    
    # Get dev model path
    model_path = get_dev_model_path()
    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dev model not found at {model_path}. Run: python scripts/get-dev-model.py"
        )
    
    # Start with dev defaults
    success = await server.start(
        model_path=str(model_path),
        gpu_layers=0,  # CPU only for dev
        context_size=2048,
    )
    
    if not success:
        status = server.get_status()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start: {status.error}"
        )
    
    return {
        "status": "started",
        "model": model_path.name,
        "mode": "cpu-only",
        "api_url": server.get_api_url(),
    }
