"""
LLM service implementation
"""
import logging
import os
from typing import Dict, List, Optional, Any

from openai import OpenAI

from app.config import settings
from app.models.completions import Message


class LLMService:
    """Service for LLM operations"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
    
    async def generate_chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Generate a chat completion"""
        try:
            # Format messages for OpenAI
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Use default settings if not provided
            model = model or settings.DEFAULT_MODEL
            temperature = temperature or settings.DEFAULT_TEMPERATURE
            max_tokens = max_tokens or settings.DEFAULT_MAX_TOKENS
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error generating chat completion: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        model: str = "whisper-1",
        language: Optional[str] = None
    ) -> str:
        """Transcribe audio to text"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                # Prepare parameters
                params = {
                    "model": model,
                    "file": audio_file
                }
                
                # Add language if provided
                if language:
                    params["language"] = language
                
                # Call OpenAI API
                transcription = self.client.audio.transcriptions.create(**params)
            
            return transcription.text
        
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0
    ) -> str:
        """Convert text to speech"""
        try:
            # Call OpenAI API
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            # In a real application, we would save the audio to a storage service
            # and return the URL. For simplicity, we'll just return a placeholder.
            # response.stream_to_file("output.mp3")
            
            # Return a placeholder URL
            return f"https://storage.example.com/audio/{hash(text)}.mp3"
        
        except Exception as e:
            self.logger.error(f"Error converting text to speech: {str(e)}")
            raise
