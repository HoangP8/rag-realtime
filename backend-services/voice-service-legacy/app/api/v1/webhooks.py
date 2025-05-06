"""
Webhook handlers for external services
"""
import hmac
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.realtime.session_manager import SessionManager
from app.dependencies import get_session_manager

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_livekit_webhook(request: Request) -> bool:
    """
    Verify LiveKit webhook signature
    
    Args:
        request: FastAPI request
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Get signature and timestamp from headers
    signature = request.headers.get("Authorization")
    if not signature or not signature.startswith("Bearer "):
        return False
    
    signature = signature[7:]  # Remove "Bearer " prefix
    
    # Get body
    body = request.scope.get("body")
    if not body:
        return False
    
    # Compute expected signature
    expected_signature = hmac.new(
        settings.LIVEKIT_API_SECRET.encode(),
        body,
        "sha256"
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


@router.post("/livekit", status_code=status.HTTP_200_OK)
async def livekit_webhook(
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Handle LiveKit webhook events
    
    Args:
        request: FastAPI request
        session_manager: Session manager
        
    Returns:
        JSON response
    """
    # Verify webhook signature
    if not verify_livekit_webhook(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    # Parse request body
    body = await request.body()
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    
    # Get event type
    event_type = event.get("event")
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type"
        )
    
    # Handle event
    try:
        await _handle_livekit_event(event_type, event, session_manager)
        return JSONResponse(content={"status": "success"})
    
    except Exception as e:
        logger.error(f"Error handling LiveKit event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error handling event: {str(e)}"
        )


async def _handle_livekit_event(
    event_type: str, 
    event: Dict[str, Any],
    session_manager: SessionManager
):
    """
    Handle LiveKit event
    
    Args:
        event_type: Event type
        event: Event data
        session_manager: Session manager
    """
    room = event.get("room")
    if not room:
        logger.warning(f"Missing room in LiveKit event: {event}")
        return
    
    room_name = room.get("name")
    if not room_name or not room_name.startswith("voice-"):
        logger.debug(f"Ignoring non-voice room: {room_name}")
        return
    
    # Extract session ID from room name
    session_id = room_name[6:]  # Remove "voice-" prefix
    
    # Handle different event types
    if event_type == "room_started":
        logger.info(f"Room started: {room_name}")
    
    elif event_type == "room_finished":
        logger.info(f"Room finished: {room_name}")
        # End session if it exists
        await session_manager.end_session(session_id)
    
    elif event_type == "participant_joined":
        participant = event.get("participant", {})
        identity = participant.get("identity", "unknown")
        logger.info(f"Participant joined: {identity} in room {room_name}")
    
    elif event_type == "participant_left":
        participant = event.get("participant", {})
        identity = participant.get("identity", "unknown")
        logger.info(f"Participant left: {identity} from room {room_name}")
        
        # If user left, end session
        if not identity.startswith("ai-"):
            logger.info(f"User left room, ending session {session_id}")
            await session_manager.end_session(session_id)
    
    else:
        logger.debug(f"Unhandled LiveKit event type: {event_type}")
