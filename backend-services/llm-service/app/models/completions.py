"""
Models for LLM completions
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class CompletionRequest(BaseModel):
    """Chat completion request model"""
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    model: Optional[str] = Field(None, description="Model to use for completion")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")


class CompletionResponse(BaseModel):
    """Chat completion response model"""
    id: str = Field(..., description="Unique identifier for the completion")
    created: int = Field(..., description="Unix timestamp of when the completion was created")
    model: str = Field(..., description="Model used for completion")
    content: str = Field(..., description="Generated text")
    finish_reason: str = Field(..., description="Reason for finishing: 'stop', 'length', etc.")
    usage: Dict[str, int] = Field(..., description="Token usage information")
