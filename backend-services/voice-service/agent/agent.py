"""
Voice agent implementation using LiveKit Agents
"""
import logging
import json
from typing import Dict, Any, Optional
from uuid import UUID

from livekit.agents import Agent
from livekit.plugins import openai

from app.models import TranscriptionMessage

logger = logging.getLogger(__name__)

class VoiceAgent(Agent):
    """Voice agent for real-time speech-to-speech communication"""
    
    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        instructions: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        # Get instructions or use default
        if not instructions:
            instructions = "You are a medical assistant. Help the user with their medical questions."
        
        # Initialize the base Agent class
        super().__init__(
            instructions=instructions
        )
        
        # Store agent-specific properties
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.metadata = metadata or {}
        self._is_active = True
        
        # Get auth token from metadata if available
        self.auth_token = self.metadata.get("auth_token")
    
    async def on_enter(self):
        """Called when the agent is activated"""
        # Start the conversation with a greeting
        self.session.generate_reply(
            instructions="Greet the user and ask how you can help them with their medical questions."
        )
    
    async def on_message(self, message):
        """Called when a message is received"""
        if not self._is_active:
            return
            
        # Store the message in the database if we have a conversation_id
        if self.conversation_id:
            await self.store_transcription(message.text, "user")
    
    async def on_response(self, response):
        """Called when the agent generates a response"""
        if not self._is_active:
            return
            
        # Store the response in the database if we have a conversation_id
        if self.conversation_id and response.text:
            await self.store_transcription(response.text, "assistant")
    
    async def on_exit(self):
        """Called when the agent is deactivated"""
        self._is_active = False
        logger.info(f"Agent session {self.session_id} ended")
    
    async def store_transcription(self, text: str, role: str):
        """Store transcription in conversation database"""
        try:
            # Check if we have auth token
            if not self.auth_token:
                logger.warning(f"No auth token available for session {self.session_id}, skipping transcription storage")
                return
                
            # Import here to avoid circular imports
            from app.services.storage import StorageService
            
            # Create message
            message = TranscriptionMessage(
                conversation_id=self.conversation_id,
                session_id=self.session_id,
                role=role,
                content=text,
                message_type="voice",
                metadata={"source": "voice_session", "session_id": self.session_id}
            )
            
            # Store message
            storage = StorageService()
            await storage.store_transcription(message, self.auth_token)
            
            logger.info(f"Stored transcription in conversation {self.conversation_id}")
        
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            # Don't raise the exception to avoid interrupting the conversation flow
