"""
Auth service implementation
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from supabase import Client
from fastapi import HTTPException, status

from app.models import UserCreate, UserLogin, UserResponse, TokenResponse, UserProfileUpdate, UserProfileResponse, UserPreferencesUpdate, UserPreferencesResponse


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, supabase: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        try:
            # Register user with Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password
            })
            
            user_id = auth_response.user.id
            
            # Create user profile in the database
            profile_data = {
                "id": user_id,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "preferences": {}
            }
            
            self.supabase.table("user_profiles").insert(profile_data).execute()
            
            # Return user data
            return UserResponse(
                id=user_id,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                created_at=auth_response.user.created_at
            )
        
        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            raise
    
    async def login_user(self, user_data: UserLogin) -> TokenResponse:
        """Login a user"""
        try:
            # Login with Supabase Auth
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": user_data.email,
                "password": user_data.password
            })
            
            # Return token data
            return TokenResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token
            )
        
        except Exception as e:
            self.logger.error(f"Error logging in user: {str(e)}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token"""
        try:
            # Refresh token with Supabase Auth
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            # Return new token data
            return TokenResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token
            )
        
        except Exception as e:
            self.logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    async def validate_token(self, token: str) -> UUID:
        """Validate token and return user ID"""
        try:
            # Basic validation for token format
            if not token or not isinstance(token, str):
                self.logger.error("Token is empty or not a string")
                raise ValueError("Invalid token format: Token is empty or not a string")
                
            # Check if token has the correct JWT format (3 parts separated by dots)
            parts = token.split('.')
            if len(parts) != 3:
                self.logger.error(f"Token has invalid number of segments: {len(parts)}")
                raise ValueError(f"Invalid token format: Token has {len(parts)} segments, expected 3")
            
            # Get user data from Supabase
            user = self.supabase.auth.get_user(token)
            
            # Return user ID
            return UUID(user.user.id)
        
        except ValueError as e:
            self.logger.error(f"Token validation error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error validating token: {str(e)}")
            raise

    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfileResponse]:
        """Get user profile"""
        try:
            # Get user profile from the database
            response = self.supabase.table("user_profiles").select("*").eq("id", str(user_id)).execute()
            
            if not response.data:
                return None
            
            profile_data = response.data[0]
            
            # Get user email from auth
            auth_user = self.supabase.auth.admin.get_user_by_id(str(user_id))
            email = auth_user.user.email
            
            # Return profile data
            return UserProfileResponse(
                id=UUID(profile_data["id"]),
                email=email,
                first_name=profile_data.get("first_name"),
                last_name=profile_data.get("last_name"),
                date_of_birth=profile_data.get("date_of_birth"),
                created_at=auth_user.user.created_at
            )
            
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
            
            # Update profile in the database
            response = self.supabase.table("user_profiles").update(update_data).eq("id", str(user_id)).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Get updated profile
            return await self.get_user_profile(user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating user profile: {str(e)}")
            raise
    
    async def get_user_preferences(self, user_id: UUID) -> UserPreferencesResponse:
        """Get user preferences"""
        try:
            # Get user profile from the database
            response = self.supabase.table("user_profiles").select("id, preferences").eq("id", str(user_id)).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="User preferences not found")
            
            profile_data = response.data[0]
            
            # Return preferences data
            return UserPreferencesResponse(
                id=UUID(profile_data["id"]),
                user_id=user_id,
                preferences=profile_data.get("preferences", {}),
                updated_at=datetime.now()  # This would ideally come from the database
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {str(e)}")
            raise
    
    async def update_user_preferences(self, user_id: UUID, data: UserPreferencesUpdate) -> UserPreferencesResponse:
        """Update user preferences"""
        try:
            # Get current preferences
            current_prefs_response = self.supabase.table("user_profiles").select("preferences").eq("id", str(user_id)).execute()
            
            if not current_prefs_response.data:
                raise HTTPException(status_code=404, detail="User preferences not found")
            
            # Merge existing preferences with new ones
            current_prefs = current_prefs_response.data[0].get("preferences", {})
            updated_prefs = {**current_prefs, **data.preferences}
            
            # Update preferences in the database
            response = self.supabase.table("user_profiles").update({"preferences": updated_prefs}).eq("id", str(user_id)).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="User preferences not found")
            
            # Return updated preferences
            return UserPreferencesResponse(
                id=UUID(response.data[0]["id"]),
                user_id=user_id,
                preferences=updated_prefs,
                updated_at=datetime.now()  # This would ideally come from the database
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {str(e)}")
            raise
