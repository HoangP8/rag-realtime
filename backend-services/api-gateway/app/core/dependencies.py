"""
FastAPI dependencies
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.services.auth import AuthService
from app.services.conversations import ConversationService
from app.services.voice import VoiceService
from app.services.profile import ProfileService
from app.services.llm import LLMService
from app.db.supabase import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


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
    llm_service = get_llm_service()
    return ConversationService(supabase, llm_service)


def get_voice_service():
    """Get voice service"""
    supabase = get_supabase()
    llm_service = get_llm_service()
    return VoiceService(supabase, llm_service)


def get_profile_service():
    """Get profile service"""
    supabase = get_supabase()
    return ProfileService(supabase)


def get_llm_service():
    """Get LLM service"""
    return LLMService()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UUID:
    """Get current user from token"""
    auth_service = get_auth_service()
    try:
        user_id = await auth_service.validate_token(token)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
