"""
Pydantic models for the Voice Service
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

class VoiceSettings(BaseModel):
    """Voice settings model"""
    voice_id: str = "alloy"
    temperature: float = 0.8
    max_output_tokens: int = 2048
    
class VoiceSessionCreate(BaseModel):
    """Voice session creation request model"""
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class VoiceSession(BaseModel):
    """Voice session model"""
    id: str
    user_id: UUID
    conversation_id: Optional[UUID] = None
    room_name: str
    token: str
    status: str = "active"
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
class VoiceSessionResponse(BaseModel):
    """Voice session response model"""
    id: str
    user_id: UUID
    conversation_id: Optional[UUID] = None
    status: str
    token: str
    room_name: str
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Optional[Dict[str, Any]] = None
    
class TranscriptionMessage(BaseModel):
    """Transcription message model"""
    conversation_id: UUID
    role: str
    content: str
    message_type: str = "voice"
    metadata: Optional[Dict[str, Any]] = None

class MessageBase(BaseModel):
    """Base message model"""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    message_type: str = Field("text", description="Message type: 'text' or 'voice'")
    voice_url: Optional[str] = Field(None, description="URL to voice recording if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MessageResponse(MessageBase):
    """Message response model"""
    id: UUID
    conversation_id: UUID
    created_at: datetime

    class Config:
        """Pydantic config"""
        orm_mode = True