"""
User profile service
"""
import logging
from typing import Dict, Optional, Any
from uuid import UUID

from supabase import Client

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
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfileResponse]:
        """Get user profile"""
        try:
            # Query user profile
            response = self.supabase.table("user_profiles") \
                .select("*") \
                .eq("id", str(user_id)) \
                .execute()
            
            # Return profile if found
            if response.data:
                return UserProfileResponse(**response.data[0])
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting user profile: {str(e)}")
            raise
    
    async def update_user_profile(self, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
        """Update user profile"""
        try:
            # Prepare update data
            update_data = {}
            if data.first_name is not None:
                update_data["first_name"] = data.first_name
            if data.last_name is not None:
                update_data["last_name"] = data.last_name
            if data.date_of_birth is not None:
                update_data["date_of_birth"] = data.date_of_birth
            
            # Update profile
            response = self.supabase.table("user_profiles") \
                .update(update_data) \
                .eq("id", str(user_id)) \
                .execute()
            
            # Return updated profile
            if response.data:
                return UserProfileResponse(**response.data[0])
            
            # If no profile exists, create one
            profile_data = {
                "id": str(user_id),
                "first_name": data.first_name,
                "last_name": data.last_name,
                "date_of_birth": data.date_of_birth
            }
            
            create_response = self.supabase.table("user_profiles") \
                .insert(profile_data) \
                .execute()
            
            return UserProfileResponse(**create_response.data[0])
        
        except Exception as e:
            self.logger.error(f"Error updating user profile: {str(e)}")
            raise
    
    async def get_user_preferences(self, user_id: UUID) -> UserPreferencesResponse:
        """Get user preferences"""
        try:
            # Query user profile for preferences
            response = self.supabase.table("user_profiles") \
                .select("id, preferences") \
                .eq("id", str(user_id)) \
                .execute()
            
            # Return preferences
            if response.data:
                preferences = response.data[0].get("preferences", {})
                return UserPreferencesResponse(
                    id=UUID(response.data[0]["id"]),
                    user_id=user_id,
                    preferences=preferences,
                    updated_at=response.data[0].get("updated_at")
                )
            
            # If no profile exists, return empty preferences
            return UserPreferencesResponse(
                id=user_id,
                user_id=user_id,
                preferences={},
                updated_at=None
            )
        
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {str(e)}")
            raise
    
    async def update_user_preferences(
        self, user_id: UUID, data: UserPreferencesUpdate
    ) -> UserPreferencesResponse:
        """Update user preferences"""
        try:
            # Get current preferences
            current_prefs_response = self.supabase.table("user_profiles") \
                .select("preferences") \
                .eq("id", str(user_id)) \
                .execute()
            
            current_preferences = {}
            if current_prefs_response.data:
                current_preferences = current_prefs_response.data[0].get("preferences", {})
            
            # Merge with new preferences
            updated_preferences = {**current_preferences, **data.preferences}
            
            # Update preferences
            response = self.supabase.table("user_profiles") \
                .update({"preferences": updated_preferences}) \
                .eq("id", str(user_id)) \
                .execute()
            
            # Return updated preferences
            if response.data:
                return UserPreferencesResponse(
                    id=UUID(response.data[0]["id"]),
                    user_id=user_id,
                    preferences=updated_preferences,
                    updated_at=response.data[0].get("updated_at")
                )
            
            # If no profile exists, create one with preferences
            profile_data = {
                "id": str(user_id),
                "preferences": data.preferences
            }
            
            create_response = self.supabase.table("user_profiles") \
                .insert(profile_data) \
                .execute()
            
            return UserPreferencesResponse(
                id=UUID(create_response.data[0]["id"]),
                user_id=user_id,
                preferences=data.preferences,
                updated_at=create_response.data[0].get("updated_at")
            )
        
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {str(e)}")
            raise
