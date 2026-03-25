"""Routes package."""

from fastapi import APIRouter

from .status import router as status_router
from .models import router as models_router
from .control import router as control_router
from .chat import router as chat_router
from .conversations import router as conversations_router

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(status_router, tags=["status"])
router.include_router(models_router)
router.include_router(control_router)
router.include_router(chat_router)
router.include_router(conversations_router)
