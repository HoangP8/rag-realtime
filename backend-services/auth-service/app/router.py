"""
Auth service router
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.models import UserCreate, UserLogin, UserResponse, TokenResponse
from app.service import AuthService
from app.dependencies import get_auth_service

router = APIRouter()


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
async def refresh_token(refresh_token: str, auth_service: AuthService = Depends(get_auth_service)):
    """Refresh access token"""
    try:
        token_data = await auth_service.refresh_token(refresh_token)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(auth_service: AuthService = Depends(get_auth_service)):
    """Logout a user"""
    return {"message": "Successfully logged out"}


@router.get("/validate")
async def validate_token(token: str, auth_service: AuthService = Depends(get_auth_service)):
    """Validate a token"""
    try:
        user_id = await auth_service.validate_token(token)
        return {"user_id": user_id, "valid": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
