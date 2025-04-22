"""
LLM service for OpenAI integration
"""
import logging
import os
from typing import List, Optional

import httpx

from app.core.config import settings
from app.schemas.conversations import MessageResponse


class LLMService:
    """Service for LLM operations"""

    def __init__(self):
        """Initialize LLM service"""
        self.logger = logging.getLogger(__name__)

        # LLM service URL
        self.llm_service_url = settings.LLM_SERVICE_URL
        if not self.llm_service_url:
            self.llm_service_url = "http://localhost:8004"

        # Default model
        self.model = "gpt-4o-mini"

    async def generate_response(self, conversation_history: List[MessageResponse], user_message: str) -> str:
        """Generate a response from the LLM"""
        try:
            # Format conversation history
            messages = []

            # Add system message if not present in history
            has_system_message = any(msg.role == "system" for msg in conversation_history)
            if not has_system_message:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful medical assistant. Provide accurate and helpful information about medical topics. If you're unsure about something, acknowledge the limitations of your knowledge and suggest consulting with a healthcare professional."
                })

            # Add conversation history
            for msg in conversation_history:
                if msg.role in ["user", "assistant", "system"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Add the new user message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Prepare request data
            request_data = {
                "messages": messages,
                "model": self.model,
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # Call LLM service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.llm_service_url}/api/v1/generate",
                    json=request_data
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error generating LLM response: {response.text}")
                    return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

                # Parse response
                response_data = response.json()

                # Extract and return the response text
                return response_data["content"]

        except Exception as e:
            self.logger.error(f"Error generating LLM response: {str(e)}")
            # Return a fallback response in case of error
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio to text using LLM service"""
        try:
            # Read audio file as bytes
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            # Call LLM service API
            async with httpx.AsyncClient() as client:
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                response = await client.post(
                    f"{self.llm_service_url}/api/v1/transcribe",
                    files=files
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error transcribing audio: {response.text}")
                    raise Exception(f"LLM service returned error: {response.text}")

                # Parse response
                response_data = response.json()

                # Return transcription text
                return response_data["text"]

        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise
