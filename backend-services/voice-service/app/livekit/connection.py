"""
LiveKit connection management
"""
import logging
from functools import lru_cache

from livekit import api

from app.livekit.config import LiveKitConfig


@lru_cache()
def get_livekit_client():
    """
    Create and return a LiveKit client
    Uses LRU cache to avoid creating multiple clients
    """
    if not LiveKitConfig.API_KEY or not LiveKitConfig.API_SECRET or not LiveKitConfig.URL:
        raise ValueError("LiveKit API key, secret, and URL must be provided")
    
    return api.LiveKitAPI(
        LiveKitConfig.URL,
        LiveKitConfig.API_KEY,
        LiveKitConfig.API_SECRET
    ).room


class LiveKitConnection:
    """LiveKit connection management"""
    
    def __init__(self):
        """Initialize LiveKit connection"""
        self.client = get_livekit_client()
        self.logger = logging.getLogger(__name__)
    
    def create_room(self, room_name: str, **kwargs) -> bool:
        """Create a LiveKit room"""
        try:
            # Merge default settings with provided kwargs
            settings = {**LiveKitConfig.DEFAULT_ROOM_SETTINGS, **kwargs}
            
            # Create room
            self.client.create_room(
                name=room_name,
                empty_timeout=settings.get("empty_timeout"),
                max_participants=settings.get("max_participants")
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error creating LiveKit room: {str(e)}")
            raise
    
    def delete_room(self, room_name: str) -> bool:
        """Delete a LiveKit room"""
        try:
            self.client.delete_room(room_name)
            return True
        
        except Exception as e:
            self.logger.error(f"Error deleting LiveKit room: {str(e)}")
            raise
    
    def generate_token(self, room_name: str, identity: str, name: str = None, **kwargs) -> str:
        """Generate a LiveKit token"""
        try:
            # Merge default settings with provided kwargs
            settings = {**LiveKitConfig.DEFAULT_TOKEN_SETTINGS, **kwargs}
            
            # Generate token
            token = self.client.generate_token(
                room_name=room_name,
                identity=identity,
                ttl=settings.get("ttl"),
                name=name or f"User {identity}"
            )
            
            return token
        
        except Exception as e:
            self.logger.error(f"Error generating LiveKit token: {str(e)}")
            raise
