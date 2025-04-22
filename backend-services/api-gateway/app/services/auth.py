"""
Authentication service
"""
import logging
from typing import Dict, Any
from uuid import UUID

import httpx
from supabase import Client

from app.core.config import settings
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse


class AuthService:
    """Service for authentication operations"""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)

        # Auth service URL
        self.auth_service_url = settings.AUTH_SERVICE_URL
        if not self.auth_service_url:
            self.auth_service_url = "http://localhost:8001"

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        try:
            # Prepare request data
            request_data = {
                "email": user_data.email,
                "password": user_data.password,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name
            }

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/register",
                    json=request_data
                )

                # Check response
                if response.status_code != 200 and response.status_code != 201:
                    self.logger.error(f"Error registering user: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                user_data = response.json()

                # Return user data
                return UserResponse(
                    id=user_data["id"],
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    created_at=user_data.get("created_at")
                )

        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            raise

    async def login_user(self, user_data: UserLogin) -> TokenResponse:
        """Login a user"""
        try:
            # Prepare request data
            request_data = {
                "email": user_data.email,
                "password": user_data.password
            }

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/login",
                    json=request_data
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error logging in user: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                token_data = response.json()

                # Return token data
                return TokenResponse(
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"]
                )

        except Exception as e:
            self.logger.error(f"Error logging in user: {str(e)}")
            raise

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token"""
        try:
            # Prepare request data
            request_data = {
                "refresh_token": refresh_token
            }

            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/refresh",
                    json=request_data
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error refreshing token: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                token_data = response.json()

                # Return token data
                return TokenResponse(
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"]
                )

        except Exception as e:
            self.logger.error(f"Error refreshing token: {str(e)}")
            raise

    async def validate_token(self, token: str) -> UUID:
        """Validate token and return user ID"""
        try:
            # Call auth service API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/auth/validate",
                    headers={"Authorization": f"Bearer {token}"}
                )

                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Error validating token: {response.text}")
                    raise Exception(f"Auth service returned error: {response.text}")

                # Parse response
                user_data = response.json()

                # Return user ID
                return UUID(user_data["id"])

        except Exception as e:
            self.logger.error(f"Error validating token: {str(e)}")
            raise
