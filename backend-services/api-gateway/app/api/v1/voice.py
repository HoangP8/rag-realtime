"""
Voice communication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.voice import VoiceSessionCreate, VoiceSessionResponse, VoiceSessionConfig
from app.services.voice import VoiceService
from app.core.dependencies import get_voice_service, get_current_user_and_token

router = APIRouter()


@router.post("/session/create", response_model=VoiceSessionResponse)
async def create_voice_session(
    session_data: VoiceSessionCreate,
    voice_service: VoiceService = Depends(get_voice_service),
    user_data = Depends(get_current_user_and_token)
):
    """Create a new voice session"""
    try:
        user_id = user_data["user_id"]
        token = user_data["token"]
        session = await voice_service.create_session(user_id, session_data, token)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_session(
    session_id: str,
    voice_service: VoiceService = Depends(get_voice_service),
    user_data = Depends(get_current_user_and_token)
):
    """Delete a voice session"""
    try:
        token = user_data["token"]
        success = await voice_service.delete_session(session_id, token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice session not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}/status", response_model=VoiceSessionResponse)
async def get_voice_session_status(
    session_id: str,
    voice_service: VoiceService = Depends(get_voice_service),
    user_data = Depends(get_current_user_and_token)
):
    """Get status of a voice session"""
    try:
        token = user_data["token"]
        session = await voice_service.get_session_status(session_id, token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/session/{session_id}/config", response_model=VoiceSessionResponse)
async def update_voice_session_config(
    session_id: str,
    config_data: VoiceSessionConfig,
    voice_service: VoiceService = Depends(get_voice_service),
    user_data = Depends(get_current_user_and_token)
):
    """Update configuration of a voice session"""
    try:
        token = user_data["token"]
        session = await voice_service.update_session_config(session_id, config_data, token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
