"""
User profile schemas
"""
from datetime import date, datetime
from typing import Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    """Base user profile schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdate(UserProfileBase):
    """User profile update schema"""
    pass


class UserProfileResponse(UserProfileBase):
    """User profile response schema"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config"""
        orm_mode = True


class UserPreferencesBase(BaseModel):
    """Base user preferences schema"""
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserPreferencesUpdate(UserPreferencesBase):
    """User preferences update schema"""
    pass


class UserPreferencesResponse(UserPreferencesBase):
    """User preferences response schema"""
    id: UUID
    user_id: UUID
    updated_at: datetime

    class Config:
        """Pydantic config"""
        orm_mode = True
