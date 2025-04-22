"""
LiveKit session management
"""
import logging
import uuid
from typing import Dict, Optional, Any
from uuid import UUID

from app.livekit.connection import LiveKitConnection


class LiveKitSession:
    """LiveKit session management"""
    
    def __init__(self):
        """Initialize LiveKit session"""
        self.connection = LiveKitConnection()
        self.logger = logging.getLogger(__name__)
    
    async def create_session(self, user_id: UUID, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new LiveKit session"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create room name
            room_name = f"voice-{session_id}"
            
            # Create LiveKit room
            self.connection.create_room(room_name)
            
            # Generate token for the user
            token = self.connection.generate_token(
                room_name=room_name,
                identity=str(user_id),
                name=f"User {user_id}"
            )
            
            # Return session data
            return {
                "id": session_id,
                "room_name": room_name,
                "token": token,
                "metadata": metadata or {}
            }
        
        except Exception as e:
            self.logger.error(f"Error creating LiveKit session: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a LiveKit session"""
        try:
            # Delete LiveKit room
            room_name = f"voice-{session_id}"
            return self.connection.delete_room(room_name)
        
        except Exception as e:
            self.logger.error(f"Error deleting LiveKit session: {str(e)}")
            raise
