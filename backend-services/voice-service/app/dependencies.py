"""
Voice service dependencies
"""
from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from supabase import create_client, Client

from app.config import settings
from app.messaging.rabbitmq import RabbitMQService
from app.realtime.session_manager import SessionManager


@lru_cache()
def get_supabase_client() -> Client:
    """
    Create and return a Supabase client
    Uses LRU cache to avoid creating multiple clients
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY

    if not url or not key:
        raise ValueError("Supabase URL and key must be provided")

    return create_client(url, key)


# RabbitMQ service singleton
_rabbitmq_service = None

@lru_cache()
def get_rabbitmq_service() -> RabbitMQService:
    """Get RabbitMQ service"""
    global _rabbitmq_service
    if _rabbitmq_service is None:
        _rabbitmq_service = RabbitMQService()
    return _rabbitmq_service


# Session manager singleton
_session_manager = None

@lru_cache()
def get_session_manager() -> SessionManager:
    """Get session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# Removed get_voice_service function


async def validate_user_id(authorization: str = Header(...)) -> UUID:
    """Validate user ID from authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    # In a real microservice architecture, we would call the auth service
    # For simplicity, we'll validate directly with Supabase
    supabase = get_supabase_client()

    try:
        # Set auth token for the client
        supabase.auth.set_session(token)

        # Get user data
        user = supabase.auth.get_user()

        # Return user ID
        return UUID(user.user.id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
