"""
API routes for the Voice Service
"""
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Header

from app.models import VoiceSessionCreate, VoiceSessionResponse, VoiceSession
from app.services.session import SessionService
from app.services.storage import StorageService
from app.utils.livekit import generate_token

router = APIRouter(prefix="/api/v1/voice")
logger = logging.getLogger(__name__)

# Dependencies
def get_session_service():
    """Get session service"""
    return SessionService()

def get_storage_service():
    """Get storage service"""
    return StorageService()

async def validate_token(authorization: str = Header(...)):
    """Validate token from authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # For simplicity, we're just returning the token and assuming it's valid
        # In a real application, you would validate the token with Supabase
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
async def validate_user_id(authorization: str = Header(...)) -> Dict:
    """Validate user ID from authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    try:
        # First try to parse the token as a UUID (for API gateway communication)
        try:
            return {"token": token, "user_id": UUID(token)}
        except ValueError:
            pass

        # If not a UUID, validate as a JWT token with Supabase
        storage_service = StorageService()

        try:
            # Set auth token for the client
            # Note: We don't set the session here since we need to do it
            # before each database operation to ensure it's always set

            # Get user data
            user = storage_service.get_user(token)

            # Return user ID
            return {
                "token": token,
                "user_id": UUID(user.user.id)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/session/create", response_model=VoiceSessionResponse)
async def create_voice_session(
    session_data: VoiceSessionCreate,
    session_service: SessionService = Depends(get_session_service),
    storage_service: StorageService = Depends(get_storage_service),
    user_data: Dict = Depends(validate_user_id)
):
    """Create a new voice session"""
    try:
        user_id = user_data["user_id"]
        auth_token = user_data["token"]
        
        # Create session
        session = await session_service.create_session(
            user_id=user_id,
            conversation_id=session_data.conversation_id,
            instructions=session_data.metadata.get("instructions"),
            voice_settings=session_data.metadata.get("voice_settings"),
            metadata=session_data.metadata,
            auth_token=auth_token,  # Pass auth token to the session service
            use_rag=session_data.metadata.get("use_rag", True)
        )
        
        # Store in database
        db_session = await storage_service.create_session(session, auth_token)
        
        # Return response
        return VoiceSessionResponse(
            id=session.id,
            user_id=user_id,
            conversation_id=session.conversation_id,
            status="active",
            token=session.token,
            room_name=session.room_name,
            config=session.config,
            metadata=session.metadata,
            created_at=session.created_at
        )
    
    except Exception as e:
        logger.error(f"Error creating voice session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/session/{session_id}", response_model=VoiceSessionResponse)
async def get_voice_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    storage_service: StorageService = Depends(get_storage_service),
    user_data: Dict = Depends(validate_user_id)
):
    """Get a voice session"""
    try:
        user_id = user_data["user_id"]
        auth_token = user_data["token"]
        
        # Get session from service cache
        session = await session_service.get_session(session_id)
        
        # If not found in service cache, try to get from database
        if not session:
            db_session = await storage_service.get_session(session_id, user_id, auth_token)
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Voice session not found"
                )
            
            # Convert to VoiceSession and add a token
            token = None
            try:
                # Generate a new token if possible
                room_name = db_session.get("room_name", f"voice-{session_id}")
                token = generate_token(
                    room_name=room_name,
                    identity=str(user_id),
                    name=f"User {user_id}"
                )
            except Exception as e:
                logger.warning(f"Error generating token for session {session_id}: {str(e)}")
            
            # Create session object
            session = VoiceSession(
                id=db_session.get("id", session_id),
                user_id=user_id,
                conversation_id=db_session.get("conversation_id"),
                room_name=db_session.get("room_name", f"voice-{session_id}"),
                token=token or db_session.get("token", ""),
                status=db_session.get("status", "active"),
                config=db_session.get("config", {}),
                metadata=db_session.get("metadata", {}),
                created_at=db_session.get("created_at", datetime.now())
            )
            
            # Cache the session
            session_service._add_to_cache(session)
        
        # Return response
        return VoiceSessionResponse(
            id=session.id,
            user_id=user_id,
            conversation_id=session.conversation_id,
            status="active",
            token=session.token,
            room_name=session.room_name,
            config=session.config,
            metadata=session.metadata,
            created_at=session.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/session/{session_id}")
async def delete_voice_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    storage_service: StorageService = Depends(get_storage_service),
    user_data: Dict = Depends(validate_user_id)
):
    """Delete a voice session"""
    try:
        user_id = user_data["user_id"]
        auth_token = user_data["token"]
        
        # Delete from database
        await storage_service.delete_session(session_id, user_id, auth_token)
        
        # Delete from service
        await session_service.delete_session(session_id)
        
        return {"message": "Voice session deleted"}
    
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
    session_service: SessionService = Depends(get_session_service)
):
    """WebSocket endpoint for voice session status updates"""
    await websocket.accept()
    
    try:
        # Get session
        session = await session_service.get_session(session_id)
        if not session:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
            return
        
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "status",
            "status": "connected",
            "message": "Connected to voice session",
            "session_id": session_id
        }))
        
        # Handle messages
        while True:
            message = await websocket.receive_text()
            
            try:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }))
                
                elif message_type == "status":
                    # Send status
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "status": "active",
                        "message": "Voice session is active",
                        "session_id": session_id
                    }))
                
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
            
            except json.JSONDecodeError:
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
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except:
            pass
