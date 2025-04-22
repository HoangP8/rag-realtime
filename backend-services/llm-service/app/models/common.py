"""
Common models for the LLM service
"""
from typing import Dict, Optional, Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
