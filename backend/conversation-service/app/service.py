"""
Conversation service implementation
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from supabase import Client

from app.models import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse
)
from app.llm import LLMService


class ConversationService:
    """Service for conversation operations"""

    def __init__(self, supabase: Client, llm_service: LLMService):
        """Initialize with Supabase client and LLM service"""
        self.supabase = supabase
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)

    async def get_user_conversations(self, user_id: UUID, token: str) -> List[ConversationResponse]:
        """Get all conversations for a user"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # Query conversations table
            # print("user ID:", user_id, "type:", type(user_id))

            response = self.supabase.table("conversations") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("updated_at", desc=True) \
                .execute()

            # print("Raw response:", response)

            # Convert to response models
            conversations = []
            for item in response.data:
                conversations.append(ConversationResponse(**item))

            # print("conversations:", conversations)

            return conversations

        except Exception as e:
            self.logger.error(f"Error getting user conversations: {str(e)}")
            raise

    async def create_conversation(self, user_id: UUID, token: str, data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # Prepare conversation data
            conversation_data = {
                "user_id": str(user_id),
                "title": data.title or "New Conversation",
                "metadata": data.metadata or {},
                "tags": data.tags or [],
                "is_archived": False
            }

            # Insert into conversations table
            response = self.supabase.table("conversations") \
                .insert(conversation_data) \
                .execute()

            # Return created conversation
            return ConversationResponse(**response.data[0])

        except Exception as e:
            self.logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def get_conversation(self, user_id: UUID, token: str, conversation_id: UUID) -> Optional[ConversationResponse]:
        """Get a specific conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # Query conversations table
            response = self.supabase.table("conversations") \
                .select("*") \
                .eq("id", str(conversation_id)) \
                .eq("user_id", str(user_id)) \
                .execute()

            # Return conversation if found
            if response.data:
                return ConversationResponse(**response.data[0])
            return None

        except Exception as e:
            self.logger.error(f"Error getting conversation: {str(e)}")
            raise

    async def update_conversation(
        self, user_id: UUID, token: str, conversation_id: UUID, data: ConversationUpdate
    ) -> Optional[ConversationResponse]:
        """Update a conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

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

            # Update conversation
            response = self.supabase.table("conversations") \
                .update(update_data) \
                .eq("id", str(conversation_id)) \
                .eq("user_id", str(user_id)) \
                .execute()

            # Return updated conversation if found
            if response.data:
                return ConversationResponse(**response.data[0])
            return None

        except Exception as e:
            self.logger.error(f"Error updating conversation: {str(e)}")
            raise

    async def delete_conversation(self, user_id: UUID, token: str, conversation_id: UUID) -> bool:
        """Delete a conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # First, check if the conversation exists and belongs to the user
            check_response = self.supabase.table("conversations") \
                .select("id") \
                .eq("id", str(conversation_id)) \
                .eq("user_id", str(user_id)) \
                .execute()

            if not check_response.data:
                return False

            # Delete any associated voice sessions first to avoid foreign key constraint violations
            self.logger.info(f"Deleting voice sessions for conversation {conversation_id}")
            voice_sessions_response = self.supabase.table("voice_sessions") \
                .delete() \
                .eq("conversation_id", str(conversation_id)) \
                .eq("user_id", str(user_id)) \
                .execute()

            self.logger.info(f"Deleted {len(voice_sessions_response.data)} voice sessions")

            # Now delete the conversation
            response = self.supabase.table("conversations") \
                .delete() \
                .eq("id", str(conversation_id)) \
                .eq("user_id", str(user_id)) \
                .execute()

            # Return success status
            return len(response.data) > 0

        except Exception as e:
            self.logger.error(f"Error deleting conversation: {str(e)}")
            raise

    async def get_conversation_messages(self, user_id: UUID, token: str, conversation_id: UUID) -> List[MessageResponse]:
        """Get all messages for a conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # First verify the conversation belongs to the user
            conversation = await self.get_conversation(user_id, token, conversation_id)
            if not conversation:
                return []

            # Query messages table
            response = self.supabase.table("messages") \
                .select("*") \
                .eq("conversation_id", str(conversation_id)) \
                .order("created_at") \
                .execute()

            # Convert to response models
            messages = []
            for item in response.data:
                messages.append(MessageResponse(**item))

            return messages

        except Exception as e:
            self.logger.error(f"Error getting conversation messages: {str(e)}")
            raise

    async def create_message(
        self, user_id: UUID, token: str, conversation_id: UUID, data: MessageCreate, generate_ai_response: bool = False
    ) -> MessageResponse:
        """Create a new message in a conversation"""
        try:
            self.supabase.auth.set_session(token, refresh_token="")

            # First verify the conversation belongs to the user
            conversation = await self.get_conversation(user_id, token, conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")

            # Prepare message data
            message_data = {
                "conversation_id": str(conversation_id),
                "role": data.role,
                "content": data.content,
                "message_type": data.message_type,
                "voice_url": data.voice_url,
                "metadata": data.metadata or {}
            }

            # Insert user message
            response = self.supabase.table("messages") \
                .insert(message_data) \
                .execute()

            user_message = MessageResponse(**response.data[0])

            # If this is a user message, generate AI response
            if data.role == "user" and generate_ai_response:
                # Get conversation history
                messages = await self.get_conversation_messages(user_id, token, conversation_id)

                # Generate AI response
                ai_response = await self.llm_service.generate_response(messages, data.content)

                # Save AI response
                ai_message_data = {
                    "conversation_id": str(conversation_id),
                    "role": "assistant",
                    "content": ai_response,
                    "message_type": "text",
                    "metadata": {}
                }

                ai_response = self.supabase.table("messages") \
                    .insert(ai_message_data) \
                    .execute()

            # Return the user message
            return user_message

        except Exception as e:
            self.logger.error(f"Error creating message: {str(e)}")
            raise
