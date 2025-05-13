"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request

from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import AuthService
from app.core.dependencies import get_auth_service

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
async def validate_token(
    request: Request,
    token: str = None, 
    authorization: str = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate a token"""
    try:
        # Debug logging
        # print(f"Headers: {request.headers}")
        # print(f"Authorization header: {authorization}")
        
        # Try to get token from query parameter
        if token:
            pass
        # Try to get token from Authorization header
        elif authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Token is required either as a query parameter or in the Authorization header"
            )

        user_id = await auth_service.validate_token(token)
        return {"user_id": str(user_id), "valid": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
