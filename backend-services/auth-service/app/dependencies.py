"""
Auth service dependencies
"""
from functools import lru_cache

from supabase import create_client, Client

from app.config import settings
from app.service import AuthService


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


def get_auth_service() -> AuthService:
    """Get auth service"""
    supabase = get_supabase_client()
    return AuthService(supabase)
