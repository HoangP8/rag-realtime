"""
Auth service models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model"""
    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime

    class Config:
        """Pydantic config"""
        orm_mode = True


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    expires_in: int


# New models for profile functionality

class UserProfileBase(BaseModel):
    """Base user profile model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class UserProfileUpdate(UserProfileBase):
    """User profile update model"""
    pass


class UserProfileResponse(UserProfileBase):
    """User profile response model"""
    id: UUID
    email: Optional[EmailStr] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config"""
        orm_mode = True


class UserPreferencesBase(BaseModel):
    """Base user preferences model"""
    preferences: Dict[str, Any] = {}


class UserPreferencesUpdate(UserPreferencesBase):
    """User preferences update model"""
    pass


class UserPreferencesResponse(UserPreferencesBase):
    """User preferences response model"""
    id: UUID
    user_id: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic config"""
        orm_mode = True
