"""
Voice service for LiveKit integration
"""
import logging
import uuid
from typing import Dict, Optional, Any
from uuid import UUID

from supabase import Client
from livekit import api

from app.core.config import settings
from app.schemas.voice import VoiceSessionCreate, VoiceSessionResponse, VoiceSessionConfig
from app.services.llm import LLMService


class VoiceService:
    """Service for voice operations"""
    
    def __init__(self, supabase: Client, llm_service: LLMService):
        """Initialize with Supabase client and LLM service"""
        self.supabase = supabase
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize LiveKit API client
        self.livekit_api = api.RoomServiceClient(
            settings.LIVEKIT_URL,
            settings.LIVEKIT_API_KEY,
            settings.LIVEKIT_API_SECRET
        )
    
    async def create_session(self, user_id: UUID, data: VoiceSessionCreate) -> VoiceSessionResponse:
        """Create a new voice session"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create LiveKit room
            room_name = f"voice-{session_id}"
            self.livekit_api.create_room(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=2  # User and AI
            )
            
            # Generate token for the user
            token = self.livekit_api.generate_token(
                room_name=room_name,
                identity=str(user_id),
                ttl=3600,  # 1 hour
                name=f"User {user_id}"
            )
            
            # Default config
            config = VoiceSessionConfig(
                voice_settings={
                    "voice_id": "default",
                    "stability": 0.5,
                    "similarity_boost": 0.5
                },
                transcription_settings={
                    "language": "en",
                    "model": "whisper-1"
                }
            )
            
            # Prepare session data
            session_data = {
                "id": session_id,
                "user_id": str(user_id),
                "conversation_id": str(data.conversation_id) if data.conversation_id else None,
                "status": "active",
                "token": token,
                "metadata": data.metadata or {},
                "config": config.dict()
            }
            
            # Store session in database
            response = self.supabase.table("voice_sessions") \
                .insert(session_data) \
                .execute()
            
            # Return session data
            session = response.data[0]
            return VoiceSessionResponse(
                id=session["id"],
                user_id=UUID(session["user_id"]),
                conversation_id=UUID(session["conversation_id"]) if session["conversation_id"] else None,
                status=session["status"],
                token=session["token"],
                metadata=session["metadata"],
                created_at=session["created_at"],
                config=VoiceSessionConfig(**session["config"])
            )
        
        except Exception as e:
            self.logger.error(f"Error creating voice session: {str(e)}")
            raise
    
    async def delete_session(self, user_id: UUID, session_id: str) -> bool:
        """Delete a voice session"""
        try:
            # Get session
            response = self.supabase.table("voice_sessions") \
                .select("*") \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                return False
            
            # Delete LiveKit room
            room_name = f"voice-{session_id}"
            try:
                self.livekit_api.delete_room(room_name)
            except Exception as e:
                self.logger.warning(f"Error deleting LiveKit room: {str(e)}")
            
            # Delete session from database
            delete_response = self.supabase.table("voice_sessions") \
                .delete() \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            return len(delete_response.data) > 0
        
        except Exception as e:
            self.logger.error(f"Error deleting voice session: {str(e)}")
            raise
    
    async def get_session_status(self, user_id: UUID, session_id: str) -> Optional[VoiceSessionResponse]:
        """Get status of a voice session"""
        try:
            # Query session
            response = self.supabase.table("voice_sessions") \
                .select("*") \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                return None
            
            # Return session data
            session = response.data[0]
            return VoiceSessionResponse(
                id=session["id"],
                user_id=UUID(session["user_id"]),
                conversation_id=UUID(session["conversation_id"]) if session["conversation_id"] else None,
                status=session["status"],
                token=session["token"],
                metadata=session["metadata"],
                created_at=session["created_at"],
                config=VoiceSessionConfig(**session["config"])
            )
        
        except Exception as e:
            self.logger.error(f"Error getting voice session status: {str(e)}")
            raise
    
    async def update_session_config(
        self, user_id: UUID, session_id: str, config: VoiceSessionConfig
    ) -> Optional[VoiceSessionResponse]:
        """Update configuration of a voice session"""
        try:
            # Update session config
            response = self.supabase.table("voice_sessions") \
                .update({"config": config.dict()}) \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                return None
            
            # Return updated session
            session = response.data[0]
            return VoiceSessionResponse(
                id=session["id"],
                user_id=UUID(session["user_id"]),
                conversation_id=UUID(session["conversation_id"]) if session["conversation_id"] else None,
                status=session["status"],
                token=session["token"],
                metadata=session["metadata"],
                created_at=session["created_at"],
                config=VoiceSessionConfig(**session["config"])
            )
        
        except Exception as e:
            self.logger.error(f"Error updating voice session config: {str(e)}")
            raise
