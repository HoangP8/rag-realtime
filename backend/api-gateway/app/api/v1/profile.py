"""
User profile endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header

from app.schemas.profile import UserProfileResponse, UserProfileUpdate, UserPreferencesResponse, UserPreferencesUpdate
from app.services.profile import ProfileService
from app.core.dependencies import get_profile_service, get_current_user_and_token

router = APIRouter()


@router.get("/", response_model=UserProfileResponse)
async def get_profile(
    authorization: str = Header(None, alias="Authorization"),
    x_api_auth: str = Header(None, alias="X-API-Auth"),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get user profile"""
    authorization = authorization or x_api_auth

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.replace("Bearer ", "")
        user_data = await get_current_user_and_token(token)
        user_id = user_data["user_id"]
        token = user_data["token"]

        profile = await profile_service.get_user_profile(user_id, token)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    authorization: str = Header(None, alias="Authorization"),
    x_api_auth: str = Header(None, alias="X-API-Auth"),
):
    """Update user profile"""
    authorization = authorization or x_api_auth

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.replace("Bearer ", "")
        user_data = await get_current_user_and_token(token)
        user_id = user_data["user_id"]
        token = user_data["token"]

        profile = await profile_service.update_user_profile(user_id, profile_data, token)
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    profile_service: ProfileService = Depends(get_profile_service),
    authorization: str = Header(None, alias="Authorization"),
    x_api_auth: str = Header(None, alias="X-API-Auth"),
):
    """Get user preferences"""
    authorization = authorization or x_api_auth

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.replace("Bearer ", "")
        user_data = await get_current_user_and_token(token)
        user_id = user_data["user_id"]
        token = user_data["token"]

        preferences = await profile_service.get_user_preferences(user_id, token)
        return preferences
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences_data: UserPreferencesUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    authorization: str = Header(None, alias="Authorization"),
    x_api_auth: str = Header(None, alias="X-API-Auth"),
):
    """Update user preferences"""
    authorization = authorization or x_api_auth

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.replace("Bearer ", "")
        user_data = await get_current_user_and_token(token)
        user_id = user_data["user_id"]
        token = user_data["token"]

        preferences = await profile_service.update_user_preferences(user_id, preferences_data, token)
        return preferences
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
