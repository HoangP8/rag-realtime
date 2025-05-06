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

    try:
        # First try to parse the token as a UUID (for API gateway communication)
        try:
            return {"token": token, "user_id": UUID(token)}
        except ValueError:
            pass

        # If not a UUID, validate as a JWT token with Supabase
        supabase = get_supabase_client()

        try:
            # Set auth token for the client
            # Note: We don't set the session here because we need to do it
            # before each database operation to ensure it's always set

            # Get user data
            user = supabase.auth.get_user(token)

            # Return user ID
            return {
                "token": token,
                "user_id": UUID(user.user.id)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
