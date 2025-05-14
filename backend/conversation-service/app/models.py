"""
Conversation service models
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base message model"""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    message_type: str = Field("text", description="Message type: 'text' or 'voice'")
    voice_url: Optional[str] = Field(None, description="URL to voice recording if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MessageCreate(MessageBase):
    """Message creation model"""
    pass


class MessageResponse(MessageBase):
    """Message response model"""
    id: UUID
    conversation_id: UUID
    created_at: datetime

    class Config:
        """Pydantic config"""
        orm_mode = True


class ConversationBase(BaseModel):
    """Base conversation model"""
    title: Optional[str] = Field(None, description="Conversation title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Conversation tags")


class ConversationCreate(ConversationBase):
    """Conversation creation model"""
    pass


class ConversationUpdate(ConversationBase):
    """Conversation update model"""
    is_archived: Optional[bool] = Field(None, description="Archive status")


class ConversationResponse(ConversationBase):
    """Conversation response model"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    is_archived: bool = False

    class Config:
        """Pydantic config"""
        orm_mode = True
