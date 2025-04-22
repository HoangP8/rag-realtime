"""
Models for audio processing
"""
from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Transcription response model"""
    text: str = Field(..., description="Transcribed text")


class TextToSpeechRequest(BaseModel):
    """Text-to-speech request model"""
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field("alloy", description="Voice to use for speech")
    model: str = Field("tts-1", description="Model to use for speech generation")
    speed: float = Field(1.0, description="Speed of speech", ge=0.25, le=4.0)


class TextToSpeechResponse(BaseModel):
    """Text-to-speech response model"""
    audio_url: str = Field(..., description="URL to the generated audio file")
