"""
JWT token generation and validation.

Handles access tokens (15 min) and refresh tokens (30 days).
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from uuid import uuid4

# Secret keys (in production, load from environment variables)
SECRET_KEY = "your-secret-key-change-in-production-use-env-var"  # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(user_id: str, email: str, role: str, scopes: list[str]) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User UUID
        email: User email
        role: User role
        scopes: List of permission scopes
        
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "scopes": scopes,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4())
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """
    Create JWT refresh token.
    
    Args:
        user_id: User UUID
        
    Returns:
        Tuple of (encoded token, expiration datetime)
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4())
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify it's an access token
        if payload.get("type") != "access":
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and validate refresh token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get expiration datetime from token without validation.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime or None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except jwt.JWTError:
        return None
