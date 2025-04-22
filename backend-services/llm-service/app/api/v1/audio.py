"""
Audio processing endpoints
"""
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.models.audio import TranscriptionResponse, TextToSpeechRequest, TextToSpeechResponse
from app.models.common import ErrorResponse
from app.services.llm import LLMService
from app.dependencies import get_llm_service

router = APIRouter()


@router.post(
    "/transcriptions",
    response_model=TranscriptionResponse,
    responses={400: {"model": ErrorResponse}}
)
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: Optional[str] = Form(None),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Transcribe audio to text"""
    try:
        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name
        
        try:
            # Transcribe audio
            transcription = await llm_service.transcribe_audio(
                audio_file_path=temp_file_path,
                model=model,
                language=language
            )
            
            return TranscriptionResponse(text=transcription)
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/text-to-speech",
    response_model=TextToSpeechResponse,
    responses={400: {"model": ErrorResponse}}
)
async def text_to_speech(
    request: TextToSpeechRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Convert text to speech"""
    try:
        # Generate speech
        audio_url = await llm_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            model=request.model,
            speed=request.speed
        )
        
        return TextToSpeechResponse(audio_url=audio_url)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
