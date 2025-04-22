"""
Voice service for LiveKit integration
"""
import logging
import uuid
from typing import Dict, Optional, Any
from uuid import UUID

import httpx
from supabase import Client

from app.core.config import settings
from app.schemas.voice import VoiceSessionCreate, VoiceSessionResponse, VoiceSessionConfig
from app.services.llm import LLMService


class VoiceService:
    """Service for voice operations"""

    def __init__(self, supabase: Client, llm_service: LLMService):
        """Initialize with Supabase client and LLM service"""
        self.supabase = supabase
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)

        # Voice service URL
        self.voice_service_url = settings.VOICE_SERVICE_URL
        if not self.voice_service_url:
            self.voice_service_url = "http://localhost:8003"

    async def create_session(self, user_id: UUID, data: VoiceSessionCreate) -> VoiceSessionResponse:
        """Create a new voice session"""
        try:
            # Prepare request data
            request_data = {
                "conversation_id": str(data.conversation_id) if data.conversation_id else None,
                "metadata": data.metadata or {}
            }

            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {str(user_id)}"}

            # Call voice service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.voice_service_url}/api/v1/session/create",
                    json=request_data,
                    headers=headers
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error creating voice session: {response.text}")
                    raise Exception(f"Voice service returned error: {response.text}")

                # Parse response
                session_data = response.json()

                # Convert to VoiceSessionResponse
                return VoiceSessionResponse(
                    id=session_data["id"],
                    user_id=UUID(session_data["user_id"]),
                    conversation_id=UUID(session_data["conversation_id"]) if session_data["conversation_id"] else None,
                    status=session_data["status"],
                    token=session_data["token"],
                    metadata=session_data["metadata"],
                    created_at=session_data["created_at"],
                    config=VoiceSessionConfig(**session_data["config"])
                )

        except Exception as e:
            self.logger.error(f"Error creating voice session: {str(e)}")
            raise

    async def delete_session(self, user_id: UUID, session_id: str) -> bool:
        """Delete a voice session"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {str(user_id)}"}

            # Call voice service API
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.voice_service_url}/api/v1/session/{session_id}",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return False

                if response.status_code != 200 and response.status_code != 204:
                    self.logger.error(f"Error deleting voice session: {response.text}")
                    raise Exception(f"Voice service returned error: {response.text}")

                return True

        except Exception as e:
            self.logger.error(f"Error deleting voice session: {str(e)}")
            raise

    async def get_session_status(self, user_id: UUID, session_id: str) -> Optional[VoiceSessionResponse]:
        """Get status of a voice session"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {str(user_id)}"}

            # Call voice service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.voice_service_url}/api/v1/session/{session_id}/status",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    self.logger.error(f"Error getting voice session status: {response.text}")
                    raise Exception(f"Voice service returned error: {response.text}")

                # Parse response
                session_data = response.json()

                # Convert to VoiceSessionResponse
                return VoiceSessionResponse(
                    id=session_data["id"],
                    user_id=UUID(session_data["user_id"]),
                    conversation_id=UUID(session_data["conversation_id"]) if session_data["conversation_id"] else None,
                    status=session_data["status"],
                    token=session_data["token"],
                    metadata=session_data["metadata"],
                    created_at=session_data["created_at"],
                    config=VoiceSessionConfig(**session_data["config"])
                )

        except Exception as e:
            self.logger.error(f"Error getting voice session status: {str(e)}")
            raise

    async def update_session_config(
        self, user_id: UUID, session_id: str, config: VoiceSessionConfig
    ) -> Optional[VoiceSessionResponse]:
        """Update configuration of a voice session"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {str(user_id)}"}

            # Call voice service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.voice_service_url}/api/v1/session/{session_id}/config",
                    json=config.dict(),
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    self.logger.error(f"Error updating voice session config: {response.text}")
                    raise Exception(f"Voice service returned error: {response.text}")

                # Parse response
                session_data = response.json()

                # Convert to VoiceSessionResponse
                return VoiceSessionResponse(
                    id=session_data["id"],
                    user_id=UUID(session_data["user_id"]),
                    conversation_id=UUID(session_data["conversation_id"]) if session_data["conversation_id"] else None,
                    status=session_data["status"],
                    token=session_data["token"],
                    metadata=session_data["metadata"],
                    created_at=session_data["created_at"],
                    config=VoiceSessionConfig(**session_data["config"])
                )

        except Exception as e:
            self.logger.error(f"Error updating voice session config: {str(e)}")
            raise
