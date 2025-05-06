"""
LiveKit Agents worker implementation
"""
import json
import logging
from typing import Dict, Any
from uuid import UUID

from livekit.agents import AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import openai

from app.config import settings
from agent.agent import VoiceAgent

logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    """
    Entrypoint for the LiveKit Agents worker
    
    Args:
        ctx: Job context provided by LiveKit Agents
    """
    try:
        # Extract metadata from the room
        metadata_str = ctx.room_metadata or "{}"
        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            metadata = {}
        
        # Extract session information
        session_id = metadata.get("session_id")
        user_id_str = metadata.get("user_id")
        conversation_id_str = metadata.get("conversation_id")
        instructions = metadata.get("instructions")
        voice_settings = metadata.get("voice_settings", {})
        
        # Validate required fields
        if not session_id or not user_id_str:
            logger.error("Missing required metadata: session_id or user_id")
            return
        
        # Connect to the room
        await ctx.connect()
        
        # Create the agent
        agent = VoiceAgent(
            session_id=session_id,
            user_id=UUID(user_id_str),
            conversation_id=UUID(conversation_id_str) if conversation_id_str else None,
            instructions=instructions,
            metadata=metadata.get("metadata", {})
        )
        
        # Create the agent session with OpenAI components
        session = AgentSession(
            # Use OpenAI's realtime API for speech-to-speech
            llm=openai.realtime.RealtimeModel(
                api_key=settings.OPENAI_API_KEY,
                instructions=agent.instructions,
                voice=voice_settings.get("voice_id", settings.DEFAULT_VOICE_ID),
                temperature=float(voice_settings.get("temperature", settings.DEFAULT_TEMPERATURE)),
                max_response_output_tokens=int(voice_settings.get("max_output_tokens", settings.DEFAULT_MAX_OUTPUT_TOKENS)),
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
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the worker with our entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
