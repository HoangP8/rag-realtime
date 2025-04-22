"""
Supabase client for database operations
"""
import os
from functools import lru_cache

from supabase import create_client, Client

from app.core.config import settings


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
