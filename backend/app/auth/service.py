"""
Authentication service layer.

Handles user registration, login, logout, token refresh, and verification.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.auth.models import UserRegister, UserLogin, TokenResponse, UserResponse, UserMe
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.permissions import get_scopes_for_role
from app.models.database import UserModel, RefreshTokenModel


async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
    """
    Register a new user.
    
    Args:
        db: Database session
        user_data: User registration data
        
    Returns:
        Created user information
        
    Raises:
        ValueError: If email already exists
    """
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user
    user = UserModel(
        id=str(uuid4()),
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise ValueError("Email already registered")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=bool(user.is_active),
        created_at=user.created_at,
        updated_at=user.updated_at
    )


async def login_user(db: AsyncSession, credentials: UserLogin) -> TokenResponse:
    """
    Authenticate user and generate tokens.
    
    Args:
        db: Database session
        credentials: Login credentials
        
    Returns:
        Access and refresh tokens
        
    Raises:
        ValueError: If credentials are invalid or user is inactive
    """
    # Find user by email
    query = select(UserModel).where(UserModel.email == credentials.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise ValueError("Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise ValueError("User account is inactive")
    
    # Get scopes for role
    scopes = get_scopes_for_role(user.role)
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email, user.role, scopes)
    refresh_token_str, refresh_expires = create_refresh_token(user.id)
    
    # Store refresh token in database
    refresh_token = RefreshTokenModel(
        id=str(uuid4()),
        user_id=user.id,
        token=refresh_token_str,
        expires_at=refresh_expires,
        created_at=datetime.utcnow(),
        revoked=0
    )
    
    db.add(refresh_token)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        db: Database session
        refresh_token: Refresh token string
        
    Returns:
        New access and refresh tokens
        
    Raises:
        ValueError: If refresh token is invalid, expired, or revoked
    """
    # Decode refresh token
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise ValueError("Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    
    # Check if token exists and is not revoked
    query = select(RefreshTokenModel).where(
        RefreshTokenModel.token == refresh_token,
        RefreshTokenModel.user_id == user_id,
        RefreshTokenModel.revoked == 0
    )
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    
    if not db_token:
        raise ValueError("Refresh token not found or revoked")
    
    # Check if token is expired
    if db_token.expires_at < datetime.utcnow():
        raise ValueError("Refresh token expired")
    
    # Get user
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")
    
    # Revoke old refresh token
    await db.execute(
        update(RefreshTokenModel)
        .where(RefreshTokenModel.id == db_token.id)
        .values(revoked=1)
    )
    
    # Get scopes for role
    scopes = get_scopes_for_role(user.role)
    
    # Generate new tokens
    new_access_token = create_access_token(user.id, user.email, user.role, scopes)
    new_refresh_token_str, new_refresh_expires = create_refresh_token(user.id)
    
    # Store new refresh token
    new_refresh_token = RefreshTokenModel(
        id=str(uuid4()),
        user_id=user.id,
        token=new_refresh_token_str,
        expires_at=new_refresh_expires,
        created_at=datetime.utcnow(),
        revoked=0
    )
    
    db.add(new_refresh_token)
    await db.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token_str,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


async def logout_user(db: AsyncSession, refresh_token: str) -> bool:
    """
    Logout user by revoking refresh token.
    
    Args:
        db: Database session
        refresh_token: Refresh token to revoke
        
    Returns:
        True if token was revoked
    """
    result = await db.execute(
        update(RefreshTokenModel)
        .where(RefreshTokenModel.token == refresh_token)
        .values(revoked=1)
    )
    await db.commit()
    
    return result.rowcount > 0


async def get_user_by_id(db: AsyncSession, user_id: str) -> UserResponse:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        User information
        
    Raises:
        ValueError: If user not found
    """
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=bool(user.is_active),
        created_at=user.created_at,
        updated_at=user.updated_at
    )


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> int:
    """
    Revoke all refresh tokens for a user.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Number of tokens revoked
    """
    result = await db.execute(
        update(RefreshTokenModel)
        .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked == 0)
        .values(revoked=1)
    )
    await db.commit()
    
    return result.rowcount
