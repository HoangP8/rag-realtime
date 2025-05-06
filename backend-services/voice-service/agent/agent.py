"""
Voice agent implementation using LiveKit Agents
"""
import logging
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
    
    async def on_enter(self):
        """Called when the agent is activated"""
        # Start the conversation with a greeting
        self.session.generate_reply(
            instructions="Greet the user and ask how you can help them with their medical questions."
        )
    
    async def on_message(self, message):
        """Called when a message is received"""
        # Store the message in the database if we have a conversation_id
        if self.conversation_id:
            await self.store_transcription(message.text, "user")
    
    async def on_response(self, response):
        """Called when the agent generates a response"""
        # Store the response in the database if we have a conversation_id
        if self.conversation_id and response.text:
            await self.store_transcription(response.text, "assistant")
    
    async def store_transcription(self, text: str, role: str):
        """Store transcription in conversation database"""
        try:
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
            # Note: In a real implementation, you would need to get the auth token
            # For now, we'll just use a placeholder
            await storage.store_transcription(message, "placeholder_token")
            
            logger.info(f"Stored transcription in conversation {self.conversation_id}")
        
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            # Don't raise the exception to avoid interrupting the conversation flow
