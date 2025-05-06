"""
Session service for managing voice sessions
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.config import settings
from app.models import VoiceSession, VoiceSettings
from app.utils.livekit import create_session, delete_room, create_livekit_client

logger = logging.getLogger(__name__)

class SessionService:
    """Session service for managing voice sessions"""
    
    def __init__(self):
        """Initialize session service"""
        self.active_sessions = {}
    
    async def create_session(
        self, 
        user_id: UUID, 
        conversation_id: Optional[UUID] = None,
        instructions: Optional[str] = None,
        voice_settings: Optional[VoiceSettings] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VoiceSession:
        """Create a new voice session"""
        try:
            # Create LiveKit session
            livekit_data = await create_session(
                user_id=user_id,
                metadata={
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "instructions": instructions,
                    "voice_settings": voice_settings.model_dump() if voice_settings else None,
                    "metadata": metadata or {}
                }
            )
            
            # Use default voice settings if not provided
            if not voice_settings:
                voice_settings = VoiceSettings(
                    voice_id=settings.DEFAULT_VOICE_ID,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    max_output_tokens=settings.DEFAULT_MAX_OUTPUT_TOKENS
                )
            
            # Create session object
            session = VoiceSession(
                id=livekit_data["id"],
                user_id=user_id,
                conversation_id=conversation_id,
                room_name=livekit_data["room_name"],
                status="active",
                instructions=instructions,
                voice_settings=voice_settings,
                metadata=metadata,
                created_at=datetime.now()
            )
            
            # Store in active sessions
            self.active_sessions[session.id] = session
            
            return session
        
        except Exception as e:
            logger.error(f"Error creating voice session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get a voice session"""
        return self.active_sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a voice session"""
        try:
            # Get session
            session = self.active_sessions.pop(session_id, None)
            if not session:
                return False
            
            # Delete LiveKit room
            await delete_room(session.room_name)
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting voice session: {str(e)}")
            raise
    
    async def update_session_metadata(
        self, 
        session_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Update session metadata"""
        try:
            # Get session
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Create LiveKit client
            client = create_livekit_client()
            
            # Update room metadata
            await client.room.update_room_metadata(
                room_name=session.room_name,
                metadata=json.dumps(metadata)
            )
            
            # Update session metadata
            session.metadata = metadata
            self.active_sessions[session_id] = session
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating session metadata: {str(e)}")
            raise
