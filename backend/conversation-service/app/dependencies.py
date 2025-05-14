"""
Conversation service dependencies
"""
from functools import lru_cache
from uuid import UUID

import httpx
from fastapi import Depends, Header, HTTPException, status
from supabase import create_client, Client

from app.config import settings
from app.service import ConversationService
from app.llm import LLMService


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


def get_llm_service() -> LLMService:
    """Get LLM service"""
    return LLMService()


def get_conversation_service() -> ConversationService:
    """Get conversation service"""
    supabase = get_supabase_client()
    llm_service = get_llm_service()
    return ConversationService(supabase, llm_service)


async def validate_user_id(authorization: str = Header(...)) -> UUID:
    """Validate user ID from authorization header"""
    # print(f"Authorization header: {authorization}")
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
            # supabase.auth.set_session(token)

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
