"""
Auth service implementation
"""
import logging
from typing import Dict, Any
from uuid import UUID

from supabase import Client

from app.models import UserCreate, UserLogin, UserResponse, TokenResponse


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
            # Set auth token for the client
            self.supabase.auth.set_session(token)
            
            # Get user data
            user = self.supabase.auth.get_user()
            
            # Return user ID
            return UUID(user.user.id)
        
        except Exception as e:
            self.logger.error(f"Error validating token: {str(e)}")
            raise
