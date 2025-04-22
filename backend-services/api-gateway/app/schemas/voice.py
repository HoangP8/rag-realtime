"""
Voice session schemas
"""
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class VoiceSessionBase(BaseModel):
    """Base voice session schema"""
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VoiceSessionCreate(VoiceSessionBase):
    """Voice session creation schema"""
    pass


class VoiceSessionConfig(BaseModel):
    """Voice session configuration schema"""
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice settings")
    transcription_settings: Optional[Dict[str, Any]] = Field(None, description="Transcription settings")


class VoiceSessionResponse(VoiceSessionBase):
    """Voice session response schema"""
    id: str
    user_id: UUID
    status: str
    token: str
    created_at: datetime
    config: VoiceSessionConfig

    class Config:
        """Pydantic config"""
        orm_mode = True
