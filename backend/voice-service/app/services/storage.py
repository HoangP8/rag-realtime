"""
Storage service for database operations
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client

from app.config import settings
from app.models import VoiceSession, TranscriptionMessage, MessageResponse

logger = logging.getLogger(__name__)

class StorageService:
    """Storage service for database operations"""
    
    def __init__(self):
        """Initialize storage service"""
        self.client = self._create_client()
    
    def _create_client(self) -> Client:
        """Create Supabase client"""
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_ANON_KEY
        
        if not url or not key:
            raise ValueError("Supabase URL and key must be provided")
        
        return create_client(url, key)
    
    def set_auth_token(self, token: str):
        """Set authentication token for Supabase client"""
        self.client.auth.set_session(token, refresh_token="")
    
    def get_user(self, token: str):
        return self.client.auth.get_user(token)
    
    async def get_user_preferences(self, user_id: UUID, auth_token: str) -> Dict[str, Any]:
        """Get user preferences from the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Get user profile from database
            response = self.client.table("user_profiles") \
                .select("preferences") \
                .eq("id", str(user_id)) \
                .execute()
            
            if not response.data:
                return {}
            
            return response.data[0].get("preferences", {})
        
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python objects to JSON-serializable types"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_data(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized
    
    async def create_session(self, session: VoiceSession, auth_token: str) -> Dict[str, Any]:
        """Create a voice session in the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Convert session to dict and serialize
            session_data = session.model_dump()
            session_data = self._serialize_data(session_data)
            
            # Insert session into database
            response = self.client.table("voice_sessions").insert(session_data).execute()
            
            return response.data[0]
        
        except Exception as e:
            logger.error(f"Error creating voice session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str, user_id: UUID, auth_token: str) -> Optional[Dict[str, Any]]:
        """Get a voice session from the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Get session from database
            response = self.client.table("voice_sessions") \
                .select("*") \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                return None
            
            return response.data[0]
        
        except Exception as e:
            logger.error(f"Error getting voice session: {str(e)}")
            raise
    
    async def delete_session(self, session_id: str, user_id: UUID, auth_token: str) -> bool:
        """Delete a voice session from the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Delete session from database
            self.client.table("voice_sessions") \
                .delete() \
                .eq("id", session_id) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting voice session: {str(e)}")
            raise
    
    async def store_transcription(self, message: TranscriptionMessage, auth_token: str) -> Dict[str, Any]:
        """Store a transcription message in the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Convert message to dict and serialize
            message_data = message.model_dump()
            message_data = self._serialize_data(message_data)
            
            # Insert message into database
            response = self.client.table("messages").insert(message_data).execute()
            
            return response.data[0]
        
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            raise

    def get_conversation_history(
        self, 
        user_id: UUID, 
        conversation_id: UUID, 
        auth_token: str,
        since_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get the conversation history for a voice session"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Build query
            query = self.client.table("messages") \
                .select("*") \
                .eq("conversation_id", str(conversation_id))
            
            # Add timestamp filter if provided
            if since_timestamp:
                query = query.gt("created_at", since_timestamp.isoformat())
            
            # Execute query and order results
            response = query.order("created_at").execute()
            
            # Convert to response models
            messages = []
            for item in response.data:
                messages.append(MessageResponse(**item))

            return messages
        
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise

    def get_messages_since(
        self,
        conversation_id: UUID,
        auth_token: str,
        since_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Get messages since a specific timestamp"""
        return self.get_conversation_history(
            user_id=None,  # Not needed for this query
            conversation_id=conversation_id,
            auth_token=auth_token,
            since_timestamp=since_timestamp
        )
