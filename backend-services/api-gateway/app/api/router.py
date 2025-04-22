"""
Main API router that includes all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1 import auth, conversations, voice, profile

api_router = APIRouter()

# Include all API endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profile"])
