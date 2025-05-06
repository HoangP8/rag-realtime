"""
Real-time voice service endpoints
Handles both REST API and WebSocket endpoints for voice communication
"""
import json
import logging
import uuid
from typing import Dict, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Header, Response

from app.models import VoiceSessionCreate, VoiceSessionResponse, VoiceSessionConfig
from app.realtime.session_manager import SessionManager
from app.livekit.session import LiveKitSession
from app.dependencies import get_session_manager, validate_user_id, get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/session/create", response_model=VoiceSessionResponse)
async def create_voice_session(
    session_data: VoiceSessionCreate,
    session_manager: SessionManager = Depends(get_session_manager),
    user_data: Dict = Depends(validate_user_id),
    supabase = Depends(get_supabase_client)
):
    """Create a new voice session"""
    try:
        user_id = user_data["user_id"]
        auth_token = user_data["token"]

        # Create LiveKit session
        livekit_session = LiveKitSession()
        livekit_data = livekit_session.create_session(
            user_id,
            metadata=session_data.metadata
        )

        # print(f"LiveKit data: {livekit_data}")

        # Prepare session data
        session_id = livekit_data["id"]
        room_name = livekit_data["room_name"]
        user_token = livekit_data["user_token"]
        assistant_token = livekit_data["assistant_token"]
        metadata = session_data.metadata or {}
        conversation_id = session_data.conversation_id

        # Default voice config
        config = VoiceSessionConfig(
            voice_settings={
                "voice_id": "alloy",  # OpenAI voice
                "stability": 0.5,
                "similarity_boost": 0.5,
                "temperature": 0.8,
                "max_output_tokens": 2048
            },
            transcription_settings={
                "language": "en",
                "model": "whisper-1"
            }
        )

        # Store session in database
        session_db_data = {
            "id": session_id,
            "user_id": str(user_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "status": "active",
            "token": user_token,  # Store user token for client use
            "assistant_token": assistant_token,  # Store assistant token for internal use
            "metadata": metadata,
            "config": config.dict()
        }

        # Set the auth token for the Supabase client
        supabase.auth.set_session(auth_token, refresh_token="")

        # Store session in database
        response = supabase.table("voice_sessions") \
            .insert(session_db_data) \
            .execute()

        # Create real-time voice agent
        await session_manager.create_session(
            session_id=session_id,
            user_id=user_id,
            room_name=room_name,
            token=assistant_token,  # Use the assistant token for the voice agent
            config=config,
            conversation_id=conversation_id,
            metadata=metadata
        )

        # Return session data
        return VoiceSessionResponse(
            id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            status="active",
            token=user_token,  # Return the user token to the client
            assistant_token=assistant_token,  # Include the assistant token in the response
            metadata=metadata,
            config=config,
            created_at=response.data[0]["created_at"]
        )

    except Exception as e:
        logger.error(f"Error creating voice session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/session/{session_id}/status", response_model=VoiceSessionResponse)
async def get_voice_session_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    user_data: Dict = Depends(validate_user_id),
    supabase = Depends(get_supabase_client)
):
    """Get status of a voice session"""
    try:
        user_id = user_data["user_id"]
        user_token = user_data["token"]

        # Check if session exists in session manager
        agent = await session_manager.get_session(session_id)

        # Set the auth token for the Supabase client
        supabase.auth.set_session(user_token, refresh_token="")

        # Get session from database
        response = supabase.table("voice_sessions") \
            .select("*") \
            .eq("id", session_id) \
            .eq("user_id", str(user_id)) \
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice session not found"
            )

        session_data = response.data[0]

        # Return session data
        return VoiceSessionResponse(
            id=session_data["id"],
            user_id=UUID(session_data["user_id"]),
            conversation_id=UUID(session_data["conversation_id"]) if session_data["conversation_id"] else None,
            status="active" if agent else "inactive",
            token=session_data["token"],
            assistant_token=session_data["assistant_token"],
            metadata=session_data["metadata"],
            config=VoiceSessionConfig(**session_data["config"]),
            created_at=session_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/session/{session_id}")
async def delete_voice_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    user_data: Dict = Depends(validate_user_id),
    supabase = Depends(get_supabase_client)
):
    """Delete a voice session"""
    try:
        user_id = user_data["user_id"]
        user_token = user_data["token"]

        # Set the auth token for the Supabase client
        supabase.auth.set_session(user_token, refresh_token="")

        # Check if session exists in database
        response = supabase.table("voice_sessions") \
            .select("id") \
            .eq("id", session_id) \
            .eq("user_id", str(user_id)) \
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice session not found"
            )

        # End session in session manager
        await session_manager.end_session(session_id)

        # Delete LiveKit session
        livekit_session = LiveKitSession()
        livekit_session.delete_session(session_id)

        # Delete session from database (token already set above)
        supabase.table("voice_sessions") \
            .delete() \
            .eq("id", session_id) \
            .execute()

        return {"message": "Voice session deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    WebSocket endpoint for real-time voice communication

    Args:
        websocket: WebSocket connection
        session_id: Voice session ID
        session_manager: Session manager
    """
    # Accept connection
    await websocket.accept()

    try:
        # Get voice agent
        agent = await session_manager.get_session(session_id)
        if not agent:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
            return

        # Register WebSocket with agent
        await agent.register_websocket(websocket)

        # Handle messages
        while True:
            # Wait for message
            message = await websocket.receive_text()

            try:
                # Parse message
                data = json.loads(message)

                # Handle message
                await handle_websocket_message(agent, data)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message: {message}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))

            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                }))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")

        # Unregister WebSocket from agent
        if agent:
            await agent.unregister_websocket(websocket)

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")

        # Close WebSocket
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except:
            pass


async def handle_websocket_message(agent, data: Dict):
    """
    Handle WebSocket message

    Args:
        agent: Voice agent
        data: Message data
    """
    message_type = data.get("type")

    if message_type == "audio":
        # Handle audio data
        audio_data = data.get("data")
        if audio_data:
            await agent.process_audio(audio_data)

    elif message_type == "text":
        # Handle text message
        text = data.get("text")
        if text:
            await agent.process_text(text)

    elif message_type == "config":
        # Handle config update
        config_data = data.get("config")
        if config_data:
            config = VoiceSessionConfig(**config_data)
            await agent.update_config(config)

    elif message_type == "control":
        # Handle control message
        action = data.get("action")

        if action == "start":
            await agent.start_conversation()

        elif action == "stop":
            await agent.stop_conversation()

        elif action == "pause":
            await agent.pause_conversation()

        elif action == "resume":
            await agent.resume_conversation()

    else:
        logger.warning(f"Unknown message type: {message_type}")
