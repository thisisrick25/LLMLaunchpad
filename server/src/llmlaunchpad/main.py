"""LLMLaunchpad - Main application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config
from .database import init_db
from .routes import router

# Create FastAPI app
app = FastAPI(
    title="LLMLaunchpad",
    description="Lightweight local AI platform",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    config = get_config()
    config.ensure_directories()
    init_db()
    print(f"LLMLaunchpad started on http://{config.host}:{config.port}")


def run():
    """Run the server."""
    config = get_config()
    uvicorn.run(
        "llmlaunchpad.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
