"""
FastAPI dependencies
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header

from app.core.config import settings
from app.services.auth import AuthService
from app.services.conversations import ConversationService
from app.services.voice import VoiceService
from app.services.profile import ProfileService
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

def get_supabase():
    """Get Supabase client"""
    return get_supabase_client()


def get_auth_service():
    """Get auth service"""
    supabase = get_supabase()
    return AuthService(supabase)


def get_conversation_service():
    """Get conversation service"""
    supabase = get_supabase()
    return ConversationService(supabase)


def get_voice_service():
    """Get voice service"""
    supabase = get_supabase()
    return VoiceService(supabase)


def get_profile_service():
    """Get profile service"""
    supabase = get_supabase()
    return ProfileService(supabase)


async def get_current_user_and_token(token: str):
    """Get current user and token"""
    auth_service = get_auth_service()

    try:
        user_id = await auth_service.validate_token(token)
        # logger.info(f"User ID: {user_id}")
        return {"user_id": user_id, "token": token}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str) -> UUID:
    """Get current user from token"""
    user_data = await get_current_user_and_token(token)
    return user_data["user_id"]
