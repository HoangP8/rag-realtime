"""
LiveKit utility functions
"""
import json
import logging
from datetime import timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from livekit import api
from livekit.api import CreateRoomRequest, DeleteRoomRequest

from app.config import settings

logger = logging.getLogger(__name__)

def create_livekit_client():
    """Create a LiveKit API client"""
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET or not settings.LIVEKIT_URL:
        raise ValueError("LiveKit API key, secret, and URL must be provided")
    
    return api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )

async def create_room(room_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Create a LiveKit room"""
    try:
        client = create_livekit_client()
        
        # Create room request
        request = CreateRoomRequest(
            name=room_name,
            empty_timeout=300,  # 5 minutes
            max_participants=2  # User and AI
        )
        
        # Create room
        await client.room.create_room(request)
        
        # Set metadata if provided
        if metadata:
            await client.room.update_room_metadata(
                room_name=room_name,
                metadata=json.dumps(metadata)
            )
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating LiveKit room '{room_name}': {str(e)}")
        raise

async def delete_room(room_name: str):
    """Delete a LiveKit room"""
    try:
        client = create_livekit_client()
        
        # Delete room request
        request = DeleteRoomRequest(
            room=room_name
        )
        
        # Delete room
        await client.room.delete_room(request)
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting LiveKit room '{room_name}': {str(e)}")
        raise

def generate_token(room_name: str, identity: str, name: str = None, ttl_seconds: int = 3600):
    """Generate a LiveKit token"""
    try:
        # Create an AccessToken
        token = api.AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET
        )
        
        # Create a VideoGrant
        grant = api.VideoGrants(
            room_join=True,
            room=room_name
        )
        
        # Set identity, name and add grant
        token.with_identity(identity)
        token.with_name(name or f"User {identity}")
        token.with_grants(grant)
        
        # Set TTL
        token.with_ttl(timedelta(seconds=ttl_seconds))
        
        # Convert to JWT
        jwt_token = token.to_jwt()
        
        return jwt_token
    
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {str(e)}")
        raise

async def create_session(user_id: UUID, metadata: Optional[Dict[str, Any]] = None):
    """Create a LiveKit session"""
    try:
        # Generate session ID
        session_id = str(UUID.uuid4())
        
        # Create room name
        room_name = f"voice-{session_id}"
        
        # Create LiveKit room with metadata
        room_metadata = {
            "session_id": session_id,
            "user_id": str(user_id),
            "metadata": metadata or {}
        }
        
        await create_room(room_name, room_metadata)
        
        # Generate token for the user
        user_token = generate_token(
            room_name=room_name,
            identity=str(user_id),
            name=f"User {user_id}"
        )
        
        # Return session data
        return {
            "id": session_id,
            "room_name": room_name,
            "token": user_token,
            "metadata": metadata or {}
        }
    
    except Exception as e:
        logger.error(f"Error creating LiveKit session: {str(e)}")
        raise
