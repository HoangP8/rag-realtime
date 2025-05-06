"""
Storage service for database operations
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from supabase import create_client, Client

from app.config import settings
from app.models import VoiceSession, TranscriptionMessage

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
    
    async def create_session(self, session: VoiceSession, auth_token: str) -> Dict[str, Any]:
        """Create a voice session in the database"""
        try:
            # Set auth token
            self.set_auth_token(auth_token)
            
            # Convert session to dict
            session_data = session.model_dump()
            
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
            
            # Convert message to dict
            message_data = message.model_dump()
            
            # Insert message into database
            response = self.client.table("messages").insert(message_data).execute()
            
            return response.data[0]
        
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            raise
