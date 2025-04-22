"""
LLM service for OpenAI integration
"""
import logging
import os
from typing import List, Optional

import openai
from openai import OpenAI

from app.config import settings


class LLMService:
    """Service for LLM operations"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio to text using OpenAI Whisper"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcription.text
        
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise
