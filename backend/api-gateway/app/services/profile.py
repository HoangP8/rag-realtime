"""
User profile service
"""
import logging
from typing import Dict, Optional, Any
from uuid import UUID

import httpx
from supabase import Client

from app.core.config import settings
from app.schemas.profile import (
    UserProfileResponse,
    UserProfileUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate
)


class ProfileService:
    """Service for user profile operations"""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)

        # Auth service URL
        self.auth_service_url = settings.AUTH_SERVICE_URL
        if not self.auth_service_url:
            self.auth_service_url = "http://localhost:8001"

    async def get_user_profile(self, user_id: UUID, token: str) -> Optional[UserProfileResponse]:
        """Get user profile"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {token}"}

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/auth/profile",
                    headers=headers
                )

                # Check response
                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    self.logger.error(f"Error getting user profile: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                profile_data = response.json()

                # Return profile data
                return UserProfileResponse(**profile_data)

        except Exception as e:
            self.logger.error(f"Error getting user profile: {str(e)}")
            raise

    async def update_user_profile(self, user_id: UUID, data: UserProfileUpdate, token: str) -> UserProfileResponse:
        """Update user profile"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {token}"}

            # Prepare update data
            update_data = {}
            if data.first_name is not None:
                update_data["first_name"] = data.first_name
            if data.last_name is not None:
                update_data["last_name"] = data.last_name
            if data.date_of_birth is not None:
                update_data["date_of_birth"] = data.date_of_birth
            if data.preferences is not None:
                update_data["preferences"] = data.preferences

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.auth_service_url}/api/v1/auth/profile",
                    json=update_data,
                    headers=headers
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error updating user profile: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                profile_data = response.json()

                # Return updated profile
                return UserProfileResponse(**profile_data)

        except Exception as e:
            self.logger.error(f"Error updating user profile: {str(e)}")
            raise

    async def get_user_preferences(self, user_id: UUID, token: str) -> UserPreferencesResponse:
        """Get user preferences"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {token}"}

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/auth/profile/preferences",
                    headers=headers
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error getting user preferences: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                preferences_data = response.json()

                # Return preferences
                return UserPreferencesResponse(
                    id=UUID(preferences_data["id"]),
                    user_id=user_id,
                    preferences=preferences_data.get("preferences", {}),
                    updated_at=preferences_data.get("updated_at")
                )

        except Exception as e:
            self.logger.error(f"Error getting user preferences: {str(e)}")
            raise

    async def update_user_preferences(
        self, user_id: UUID, data: UserPreferencesUpdate, token: str
    ) -> UserPreferencesResponse:
        """Update user preferences"""
        try:
            # Set authorization header with user ID
            headers = {"Authorization": f"Bearer {token}"}

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/profile/preferences",
                    json=data.dict(),
                    headers=headers
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error updating user preferences: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                preferences_data = response.json()

                # Return updated preferences
                return UserPreferencesResponse(
                    id=UUID(preferences_data["id"]),
                    user_id=user_id,
                    preferences=preferences_data.get("preferences", {}),
                    updated_at=preferences_data.get("updated_at")
                )

        except Exception as e:
            self.logger.error(f"Error updating user preferences: {str(e)}")
            raise
