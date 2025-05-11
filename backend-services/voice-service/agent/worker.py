"""
LiveKit Agents worker implementation
"""
import json
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional
from uuid import UUID

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, WorkerType, AutoSubscribe, cli
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai

from app.config import settings
from app.models import TranscriptionMessage

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

async def store_transcription(
    conversation_id: UUID,
    session_id: str,
    text: str,
    role: str,
    auth_token: Optional[str] = None
):
    """Store transcription in conversation database"""
    try:
        # Check if we have auth token
        if not auth_token:
            logger.warning(f"No auth token available for session {session_id}, skipping transcription storage")
            return
            
        # Import here to avoid circular imports
        from app.services.storage import StorageService
        
        # Create message
        message = TranscriptionMessage(
            conversation_id=conversation_id,
            session_id=session_id,
            role=role,
            content=text,
            message_type="voice",
            metadata={"source": "voice_session", "session_id": session_id}
        )
        
        # Store message
        storage = StorageService()
        await storage.store_transcription(message, auth_token)
        
        logger.info(f"Stored transcription in conversation {conversation_id}")
    
    except Exception as e:
        logger.error(f"Error storing transcription: {str(e)}")
        # Don't raise the exception to avoid interrupting the conversation flow

async def send_transcription(
    ctx: JobContext,
    participant: rtc.Participant,
    track_sid: str,
    segment_id: str,
    text: str,
    is_final: bool = True,
):
    """Send transcription to the room"""
    transcription = rtc.Transcription(
        participant_identity=participant.identity,
        track_sid=track_sid,
        segments=[
            rtc.TranscriptionSegment(
                id=segment_id,
                text=text,
                start_time=0,
                end_time=0,
                language="en",
                final=is_final,
            )
        ],
    )
    await ctx.room.local_participant.publish_transcription(transcription)

async def entrypoint(ctx: JobContext):
    """
    Entrypoint for the LiveKit Agents worker
    
    Args:
        ctx: Job context provided by LiveKit Agents
    """
    retry_count = 0
    while retry_count < MAX_RETRIES:
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
            agent_metadata = metadata.get("metadata", {})
            
            # Validate required fields
            if not session_id or not user_id_str:
                logger.error("Missing required metadata: session_id or user_id")
                return
            
            # Get auth token from metadata if available
            auth_token = agent_metadata.get("auth_token")
            
            # Convert IDs to proper types
            user_id = UUID(user_id_str)
            conversation_id = UUID(conversation_id_str) if conversation_id_str else None
            
            # Get instructions or use default
            if not instructions:
                instructions = "You are a medical assistant. Help the user with their medical questions."
            
            # Connect to the room with auto-subscribe for audio
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
            
            # Wait for participant to join
            participant = await ctx.wait_for_participant()
            
            # Configure real-time model
            model = openai.realtime.RealtimeModel(
                api_key=settings.OPENAI_API_KEY,
                instructions=instructions,
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
            
            # Create multimodal agent
            assistant = MultimodalAgent(model=model)
            assistant.start(ctx.room)
            session = model.sessions[0]
            
            # Start with a greeting
            session.conversation.item.create(
                openai.realtime.ChatMessage(
                    role="user",
                    content="Please greet the user and ask how you can help them with their medical questions."
                )
            )
            session.response.create()
            
            # Set up transcription handling
            last_transcript_id = None
            
            @session.on("input_speech_started")
            def on_input_speech_started():
                nonlocal last_transcript_id
                remote_participant = next(iter(ctx.room.remote_participants.values()), None)
                if not remote_participant:
                    return

                track_sid = next(
                    (
                        track.sid
                        for track in remote_participant.track_publications.values()
                        if track.source == rtc.TrackSource.SOURCE_MICROPHONE
                    ),
                    None,
                )
                if last_transcript_id:
                    asyncio.create_task(
                        send_transcription(
                            ctx, remote_participant, track_sid, last_transcript_id, ""
                        )
                    )

                new_id = str(uuid.uuid4())
                last_transcript_id = new_id
                asyncio.create_task(
                    send_transcription(
                        ctx, remote_participant, track_sid, new_id, "…", is_final=False
                    )
                )
            
            @session.on("input_speech_transcription_completed")
            def on_input_speech_transcription_completed(event):
                nonlocal last_transcript_id
                if last_transcript_id:
                    remote_participant = next(iter(ctx.room.remote_participants.values()), None)
                    if not remote_participant:
                        return

                    track_sid = next(
                        (
                            track.sid
                            for track in remote_participant.track_publications.values()
                            if track.source == rtc.TrackSource.SOURCE_MICROPHONE
                        ),
                        None,
                    )
                    asyncio.create_task(
                        send_transcription(
                            ctx, remote_participant, track_sid, last_transcript_id, ""
                        )
                    )
                    last_transcript_id = None
                    
                    # Store user message in database
                    if conversation_id and event.text:
                        asyncio.create_task(store_transcription(
                            conversation_id=conversation_id,
                            session_id=session_id,
                            text=event.text,
                            role="user",
                            auth_token=auth_token
                        ))
            
            @session.on("response_done")
            def on_response_done(response):
                # Store assistant response in database
                if conversation_id and response.text:
                    asyncio.create_task(store_transcription(
                        conversation_id=conversation_id,
                        session_id=session_id,
                        text=response.text,
                        role="assistant",
                        auth_token=auth_token
                    ))
            
            # Wait for the session to end (when the room is disconnected)
            await ctx.wait_until_done()
            
            # If we get here, the session ended normally
            logger.info(f"Agent session {session_id} ended")
            break
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Error in agent entrypoint (attempt {retry_count}/{MAX_RETRIES}): {str(e)}")
            
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached, giving up")
                raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the worker with our entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, worker_type=WorkerType.ROOM))
