"""
Authentication router.

Endpoints for user registration, login, logout, token refresh, and user info.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserResponse, UserMe, LogoutRequest
)
from app.auth.service import (
    register_user, login_user, refresh_access_token, logout_user,
    get_user_by_id
)
from app.auth.permissions import get_current_user, require_role
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """
    Register a new user (admin only).
    
    Only administrators can create new user accounts.
    """
    try:
        user = await register_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access/refresh tokens.
    
    Returns JWT tokens for accessing protected endpoints.
    Access token expires in 15 minutes, refresh token in 30 days.
    """
    try:
        tokens = await login_user(db, credentials)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Generates a new access token and refresh token.
    The old refresh token is revoked.
    """
    try:
        tokens = await refresh_access_token(db, request.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Logout user by revoking refresh token.
    
    Invalidates the refresh token so it cannot be used again.
    """
    success = await logout_user(db, request.refresh_token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserMe)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns user details from the JWT token.
    """
    return UserMe(
        id=current_user["sub"],
        email=current_user["email"],
        full_name=current_user.get("full_name", ""),
        role=current_user["role"],
        scopes=current_user.get("scopes", []),
        is_active=True
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager"))
):
    """
    Get user information by ID (admin/manager only).
    """
    try:
        user = await get_user_by_id(db, user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
