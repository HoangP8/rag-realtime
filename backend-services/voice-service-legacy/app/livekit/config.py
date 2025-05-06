"""
LiveKit configuration
"""
from app.config import settings


class LiveKitConfig:
    """LiveKit configuration"""
    
    API_KEY = settings.LIVEKIT_API_KEY
    API_SECRET = settings.LIVEKIT_API_SECRET
    URL = settings.LIVEKIT_URL
    
    # Default room settings
    DEFAULT_ROOM_SETTINGS = {
        "empty_timeout": 300,  # 5 minutes
        "max_participants": 2  # User and AI
    }
    
    # Default token settings
    DEFAULT_TOKEN_SETTINGS = {
        "ttl": 3600,  # 1 hour
    }
