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
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

class SessionService:
    """Session service for managing voice sessions"""
    
    def __init__(self):
        """Initialize session service"""
        # Keep a small cache for recently accessed sessions
        # This reduces database load but doesn't cause scaling issues
        # since we don't rely exclusively on in-memory storage
        self.session_cache = {}
        self.max_cache_size = 100
    
    async def create_session(
        self, 
        user_id: UUID, 
        conversation_id: Optional[UUID] = None,
        instructions: Optional[str] = None,
        voice_settings: Optional[VoiceSettings] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        use_rag: bool = True
    ) -> VoiceSession:
        """Create a new voice session"""
        try:
            if not instructions:
                instructions = "You are a medical assistant. Help the user with their medical questions."
            # Use default voice settings if not provided
            if not voice_settings:
                voice_settings = VoiceSettings(
                    voice_id=settings.DEFAULT_VOICE_ID,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    max_output_tokens=settings.DEFAULT_MAX_OUTPUT_TOKENS
                )

            # Get user preferences from database
            storage_service = StorageService()
            user_preferences = await storage_service.get_user_preferences(user_id, auth_token)

            # logger.info(f"USER PREFERENCES: {user_preferences}") 
            # logger.info(f"USE RAG: {use_rag}") 

            # Create LiveKit session
            livekit_data = await create_session(
                user_id=user_id,
                metadata={
                    "session_id": None,  # Will be set by create_session
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "instructions": instructions,
                    "voice_settings": voice_settings.model_dump() if voice_settings else None,
                    "auth_token": auth_token,  # Pass auth token to agent
                    "use_rag": use_rag,  # Pass use_rag flag to agent
                    "preferences": user_preferences,  # Pass user preferences from database
                    "metadata": metadata or {}
                }
            )

            config = {
                "instructions": instructions,
                "voice_settings": voice_settings.model_dump() if voice_settings else None,
            }
            
            # Create session object
            session = VoiceSession(
                id=livekit_data["id"],
                user_id=user_id,
                conversation_id=conversation_id,
                room_name=livekit_data["room_name"],
                token=livekit_data["token"],
                status="active",
                config=config,
                metadata=metadata,
                created_at=datetime.now()
            )
            
            # Store in cache
            self._add_to_cache(session)
            
            return session
        
        except Exception as e:
            logger.error(f"Error creating voice session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """
        Get a voice session
        First checks cache, then falls back to database (caller should implement)
        """
        # Check cache first
        return self.session_cache.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a voice session"""
        try:
            # Remove from cache
            session = self.session_cache.pop(session_id, None)
            
            # If not in cache, we still attempt to delete the LiveKit room
            # This handles cases where the session was created on another instance
            room_name = f"voice-{session_id}" if not session else session.room_name
            
            # Delete LiveKit room
            try:
                await delete_room(room_name)
            except Exception as e:
                logger.warning(f"Error deleting LiveKit room '{room_name}': {str(e)}")
            
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
            # Get session from cache first
            session = self.session_cache.get(session_id)
            
            # If not in cache, use default room name
            if not session:
                room_name = f"voice-{session_id}"
            else:
                room_name = session.room_name
            
            # Create LiveKit client
            client = create_livekit_client()
            
            # Update room metadata
            await client.room.update_room_metadata(
                room_name=room_name,
                metadata=json.dumps(metadata)
            )
            
            # Update cache if session exists
            if session:
                session.metadata = metadata
                self._add_to_cache(session)
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating session metadata: {str(e)}")
            raise
    
    def _add_to_cache(self, session: VoiceSession):
        """Add session to cache, removing oldest if cache is full"""
        # Add to cache
        self.session_cache[session.id] = session
        
        # Remove oldest if cache is full
        if len(self.session_cache) > self.max_cache_size:
            oldest_id = next(iter(self.session_cache))
            self.session_cache.pop(oldest_id, None)
