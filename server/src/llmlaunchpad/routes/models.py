"""Model management API routes for LLMLaunchpad."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..models import (
    get_local_models,
    get_sources_status,
    get_recommended_models,
    find_model_by_name,
    parse_hf_url,
    list_hf_gguf_files,
    search_hf_models,
    download_model,
)
from ..offload import get_offload_preview

router = APIRouter(prefix="/models", tags=["models"])


# Request/Response models

class ModelScanRequest(BaseModel):
    """Request to refresh model scan."""
    pass


class HFSearchRequest(BaseModel):
    """Request to search Hugging Face."""
    query: str
    limit: int = 10


class HFFilesRequest(BaseModel):
    """Request to list files in a HF repo."""
    repo_id: str


class HFParseRequest(BaseModel):
    """Request to parse a HF URL."""
    url: str


class DownloadRequest(BaseModel):
    """Request to download a model."""
    repo_id: str
    filename: str


class OffloadPreviewRequest(BaseModel):
    """Request offload preview for a model."""
    model_path: str
    context_size: int = 4096


# Download tracking
_download_progress: Dict[str, Dict[str, Any]] = {}


# Routes

@router.get("")
@router.get("/")
async def list_models(refresh: bool = False):
    """
    List all available local models.
    
    Query params:
    - refresh: Force rescan of model directories
    """
    models = get_local_models(refresh=refresh)
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
    }


@router.post("/scan")
async def scan_models():
    """Force a rescan of all model sources."""
    models = get_local_models(refresh=True)
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
    }


@router.get("/sources")
async def get_sources():
    """Get status of all model source directories."""
    return get_sources_status()


@router.get("/recommended")
async def get_recommended():
    """Get list of recommended models for new users."""
    return {
        "models": get_recommended_models(),
    }


@router.get("/{model_name}")
async def get_model(model_name: str):
    """Get details about a specific model."""
    model = find_model_by_name(model_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
    return model.to_dict()


@router.post("/offload-preview")
async def offload_preview(request: OffloadPreviewRequest):
    """
    Get offload recommendations for a model.
    
    Returns recommendations for all performance modes.
    """
    model = find_model_by_name(request.model_path)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_path}")
    
    return get_offload_preview(model.path, request.context_size)


# Hugging Face integration routes

@router.post("/hf/search")
async def hf_search(request: HFSearchRequest):
    """Search Hugging Face for GGUF models."""
    try:
        results = await search_hf_models(request.query, request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hf/files")
async def hf_list_files(request: HFFilesRequest):
    """List GGUF files in a Hugging Face repository."""
    try:
        files = await list_hf_gguf_files(request.repo_id)
        return {
            "repo_id": request.repo_id,
            "files": [f.to_dict() for f in files],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hf/parse")
async def hf_parse_url(request: HFParseRequest):
    """Parse a Hugging Face URL to extract repo_id and filename."""
    try:
        repo_id, filename = parse_hf_url(request.url)
        return {
            "repo_id": repo_id,
            "filename": filename,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Start downloading a model from Hugging Face.
    
    Returns a download_id to track progress.
    """
    download_id = f"{request.repo_id}/{request.filename}"
    
    # Check if already downloading
    if download_id in _download_progress:
        status = _download_progress[download_id]
        if status.get("status") == "downloading":
            return {
                "download_id": download_id,
                "status": "already_downloading",
            }
    
    # Initialize progress
    _download_progress[download_id] = {
        "status": "starting",
        "repo_id": request.repo_id,
        "filename": request.filename,
        "progress": 0,
        "error": None,
    }
    
    async def do_download():
        try:
            _download_progress[download_id]["status"] = "downloading"
            
            # Download the model
            local_path = await download_model(
                repo_id=request.repo_id,
                filename=request.filename,
            )
            
            _download_progress[download_id].update({
                "status": "completed",
                "progress": 100,
                "local_path": local_path,
            })
            
            # Refresh model cache
            get_local_models(refresh=True)
            
        except Exception as e:
            _download_progress[download_id].update({
                "status": "error",
                "error": str(e),
            })
    
    background_tasks.add_task(do_download)
    
    return {
        "download_id": download_id,
        "status": "started",
    }


@router.get("/download/{repo_owner}/{repo_name}/{filename:path}")
async def get_download_status(repo_owner: str, repo_name: str, filename: str):
    """Get the status of a download."""
    download_id = f"{repo_owner}/{repo_name}/{filename}"
    
    if download_id not in _download_progress:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return _download_progress[download_id]


@router.get("/downloads")
async def list_downloads():
    """List all download statuses."""
    return {
        "downloads": list(_download_progress.values()),
    }
