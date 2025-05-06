"""
LiveKit Agents worker for voice service
"""
import asyncio
import logging
import uuid
from typing import Dict, Optional, Any
from uuid import UUID

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import openai
from livekit.rtc import Room

from app.config import settings
from app.models import VoiceSessionConfig
from app.dependencies import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAgent(Agent):
    """Voice agent for real-time speech-to-speech communication"""
    
    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[VoiceSessionConfig] = None
    ):
        # Get instructions from metadata or use default
        instructions = metadata.get("instructions", "You are a medical assistant. Help the user with their medical questions.")
        
        # Initialize the base Agent class
        super().__init__(
            instructions=instructions
        )
        
        # Store agent-specific properties
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.metadata = metadata or {}
        self.config = config
        self.last_activity = asyncio.get_event_loop().time()
        
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
            # Get Supabase client
            supabase = get_supabase_client()
            
            # Prepare message data
            message_data = {
                "conversation_id": str(self.conversation_id),
                "role": role,
                "content": text,
                "message_type": "voice",
                "metadata": {"source": "voice_session", "session_id": self.session_id}
            }
            
            # Insert message into database
            response = supabase.table("messages").insert(message_data).execute()
            
            logger.info(f"Stored transcription in conversation {self.conversation_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            # Don't raise the exception to avoid interrupting the conversation flow

async def entrypoint(ctx: JobContext):
    """
    Entrypoint for the LiveKit Agents worker
    
    Args:
        ctx: Job context provided by LiveKit Agents
    """
    # Extract metadata from the room
    metadata = ctx.room_metadata or {}
    session_id = metadata.get("session_id")
    user_id = metadata.get("user_id")
    conversation_id = metadata.get("conversation_id")
    config_data = metadata.get("config", {})
    
    if not session_id or not user_id:
        logger.error("Missing required metadata: session_id or user_id")
        return
    
    try:
        # Connect to the room
        await ctx.connect()
        
        # Create voice settings from config
        voice_settings = config_data.get("voice_settings", {})
        
        # Create the agent
        agent = VoiceAgent(
            session_id=session_id,
            user_id=UUID(user_id),
            conversation_id=UUID(conversation_id) if conversation_id else None,
            metadata=metadata.get("metadata", {}),
            config=VoiceSessionConfig(**config_data) if config_data else None
        )
        
        # Create the agent session with OpenAI components
        session = AgentSession(
            # Use OpenAI's realtime API for speech-to-speech
            llm=openai.realtime.RealtimeModel(
                api_key=settings.OPENAI_API_KEY,
                instructions=agent.instructions,
                voice=voice_settings.get("voice_id", "alloy"),
                temperature=float(voice_settings.get("temperature", 0.8)),
                max_response_output_tokens=int(voice_settings.get("max_output_tokens", 2048)),
                modalities=["text", "audio"],
                turn_detection=openai.realtime.ServerVadOptions(
                    threshold=0.5,
                    prefix_padding_ms=200,
                    silence_duration_ms=300,
                ),
            )
        )
        
        # Start the session with our agent and the room from the context
        await session.start(agent=agent, room=ctx.room)
        
        # Wait for the session to end (when the room is disconnected)
        await ctx.wait_until_done()
        
    except Exception as e:
        logger.error(f"Error in agent entrypoint: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the worker with our entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
