"""
Auth service router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from uuid import UUID
import logging
import json
from typing import Dict, Any

from app.models import UserCreate, UserLogin, UserResponse, TokenResponse, UserProfileUpdate, UserProfileResponse, UserPreferencesUpdate, UserPreferencesResponse
from app.service import AuthService
from app.dependencies import get_auth_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    """Register a new user"""
    try:
        user = await auth_service.register_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    """Login a user"""
    try:
        token_data = await auth_service.login_user(user_data)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: dict, auth_service: AuthService = Depends(get_auth_service)):
    """Refresh access token"""
    try:
        token_data = await auth_service.refresh_token(refresh_data["refresh_token"])
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(auth_service: AuthService = Depends(get_auth_service)):
    """Logout a user"""
    try:
        await auth_service.logout_user()
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/validate")
async def validate_token(token: str = None, authorization: str = Header(None), auth_service: AuthService = Depends(get_auth_service)):
    """Validate a token"""
    try:
        extracted_token = None
        
        # Try to get token from query parameter
        if token:
            logger.info("Using token from query parameter")
            extracted_token = token
        # Try to get token from Authorization header
        elif authorization:
            if authorization.startswith("Bearer "):
                logger.info("Extracting token from Bearer authorization header")
                extracted_token = authorization.replace("Bearer ", "").strip()
            else:
                logger.warning(f"Authorization header does not start with 'Bearer ': {authorization[:15]}...")
                extracted_token = authorization.strip()
                logger.info("Using raw authorization header as token")
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Token is required either as a query parameter or in the Authorization header"
            )
        
        # Log token format for debugging (showing only first few characters for security)
        # if extracted_token:
        #     token_preview = extracted_token[:10] + "..." if len(extracted_token) > 10 else extracted_token
        #     segments = extracted_token.split(".")
        #     logger.info(f"Token preview: {token_preview}, segments: {len(segments)}")
        
        # Validate token
        user_id = await auth_service.validate_token(extracted_token)
        return {"user_id": user_id, "valid": True}
    except ValueError as e:
        # Handle specific validation errors
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def _get_user_id_from_auth(authorization: str, auth_service: AuthService) -> UUID:
    """Helper to extract and validate user ID from auth header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Validate token and get user ID
        return await auth_service.validate_token(token)
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user profile"""
    try:
        # Get user ID from token
        user_id = await _get_user_id_from_auth(authorization, auth_service)
        
        # Get user profile
        profile = await auth_service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return profile
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile"""
    try:
        # Get user ID from token
        user_id = await _get_user_id_from_auth(authorization, auth_service)
        
        # Update profile
        updated_profile = await auth_service.update_user_profile(user_id, data)
        
        return updated_profile
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/profile/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user preferences"""
    try:
        # Get user ID from token
        user_id = await _get_user_id_from_auth(authorization, auth_service)
        
        # Get user preferences
        preferences = await auth_service.get_user_preferences(user_id)
        
        return preferences
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/profile/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    data: UserPreferencesUpdate,
    authorization: str = Header(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user preferences"""
    try:
        # Get user ID from token
        user_id = await _get_user_id_from_auth(authorization, auth_service)
        
        # Update preferences
        updated_preferences = await auth_service.update_user_preferences(user_id, data)
        
        return updated_preferences
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
