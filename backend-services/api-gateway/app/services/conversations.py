"""
Conversation service
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

import httpx
from supabase import Client

from app.core.config import settings
from app.schemas.conversations import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse
)


class ConversationService:
    """Service for conversation operations"""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)

        # Conversation service URL
        self.conversation_service_url = settings.CONVERSATION_SERVICE_URL
        if not self.conversation_service_url:
            self.conversation_service_url = "http://localhost:8002"

    async def get_user_conversations(self, user_id: UUID, token: str) -> List[ConversationResponse]:
        """Get all conversations for a user"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.conversation_service_url}/api/v1/conversations",
                    headers=headers
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error getting user conversations: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                conversations_data = response.json()

                # Convert to ConversationResponse objects
                conversations = []
                for item in conversations_data:
                    conversation = ConversationResponse(
                        id=UUID(item["id"]),
                        user_id=UUID(item["user_id"]),
                        title=item["title"],
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        metadata=item["metadata"] or {}
                    )
                    conversations.append(conversation)

                return conversations

        except Exception as e:
            self.logger.error(f"Error getting user conversations: {str(e)}")
            raise

    async def create_conversation(self, user_id: UUID, data: ConversationCreate, token: str) -> ConversationResponse:
        """Create a new conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Prepare request data
            request_data = {
                "title": data.title or "New Conversation",
                "metadata": data.metadata or {},
                "tags": data.tags or [],
                "is_archived": False
            }

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.conversation_service_url}/api/v1/conversations",
                    json=request_data,
                    headers=headers
                )

                # Check response
                if response.status_code != 200 and response.status_code != 201:
                    self.logger.error(f"Error creating conversation: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                created = response.json()

                # Return created conversation
                return ConversationResponse(**created)

        except Exception as e:
            self.logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def get_conversation(self, conversation_id: UUID, token: str) -> Optional[ConversationResponse]:
        """Get a specific conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.conversation_service_url}/api/v1/conversations/{conversation_id}",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    self.logger.error(f"Error getting conversation: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                conversation_data = response.json()

                # Return conversation
                return ConversationResponse(**conversation_data)

        except Exception as e:
            self.logger.error(f"Error getting conversation: {str(e)}")
            raise

    async def update_conversation(
        self, conversation_id: UUID, data: ConversationUpdate, token: str
    ) -> Optional[ConversationResponse]:
        """Update a conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Prepare update data
            update_data = {}
            if data.title is not None:
                update_data["title"] = data.title
            if data.metadata is not None:
                update_data["metadata"] = data.metadata
            if data.tags is not None:
                update_data["tags"] = data.tags
            if data.is_archived is not None:
                update_data["is_archived"] = data.is_archived

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.conversation_service_url}/api/v1/conversations/{conversation_id}",
                    json=update_data,
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    self.logger.error(f"Error updating conversation: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                conversation_data = response.json()

                # Return updated conversation
                return ConversationResponse(**conversation_data)

        except Exception as e:
            self.logger.error(f"Error updating conversation: {str(e)}")
            raise

    async def delete_conversation(self, conversation_id: UUID, token: str) -> bool:
        """Delete a conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.conversation_service_url}/api/v1/conversations/{conversation_id}",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return False

                if response.status_code != 200 and response.status_code != 204:
                    self.logger.error(f"Error deleting conversation: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                return True

        except Exception as e:
            self.logger.error(f"Error deleting conversation: {str(e)}")
            raise

    async def get_conversation_messages(self, conversation_id: UUID, token: str) -> List[MessageResponse]:
        """Get all messages for a conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.conversation_service_url}/api/v1/conversations/{conversation_id}/messages",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return []

                if response.status_code != 200:
                    self.logger.error(f"Error getting conversation messages: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                messages_data = response.json()

                # Convert to MessageResponse objects
                messages = []
                for item in messages_data:
                    messages.append(MessageResponse(**item))

                return messages

        except Exception as e:
            self.logger.error(f"Error getting conversation messages: {str(e)}")
            raise

    async def create_message(
        self, conversation_id: UUID, data: MessageCreate, token: str
    ) -> MessageResponse:
        """Create a new message in a conversation"""
        try:
            # Set authorization header with token
            headers = {"Authorization": f"Bearer {token}"}

            # Prepare message data
            message_data = {
                "role": data.role,
                "content": data.content,
                "message_type": data.message_type,
                "voice_url": data.voice_url,
                "metadata": data.metadata or {}
            }

            # Call conversation service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.conversation_service_url}/api/v1/conversations/{conversation_id}/messages",
                    json=message_data,
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    raise ValueError("Conversation not found")

                if response.status_code != 200 and response.status_code != 201:
                    self.logger.error(f"Error creating message: {response.text}")
                    raise Exception(f"Conversation service returned error: {response.text}")

                # Parse response
                message_data = response.json()

                # Return created message
                user_message = MessageResponse(**message_data)

            # The conversation service will handle generating AI responses
            # Return the user message
            return user_message

        except Exception as e:
            self.logger.error(f"Error creating message: {str(e)}")
            raise
