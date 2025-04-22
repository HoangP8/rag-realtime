"""
LLM service router
"""
from fastapi import APIRouter

from app.api.v1 import completions, audio

router = APIRouter(prefix="/api/v1")

# Include all API endpoint routers
router.include_router(completions.router, prefix="/completions", tags=["Completions"])
router.include_router(audio.router, prefix="/audio", tags=["Audio"])
