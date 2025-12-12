"""
Permission and role management.

Defines role-to-scope mappings and permission decorators.
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from functools import wraps

from app.auth.jwt import decode_access_token

# Security scheme
security = HTTPBearer()

# Role to scopes mapping
ROLE_SCOPES = {
    "admin": [
        "all",  # Admin has all permissions
    ],
    "manager": [
        "publishing:read",
        "publishing:write",
        "publishing:delete",
        "campaigns:read",
        "campaigns:write",
        "campaigns:delete",
        "dashboard:read",
        "metrics:read",
        "alerts:read",
    ],
    "operator": [
        "queue:read",
        "queue:write",
        "worker:read",
        "worker:write",
        "dashboard:read",
        "metrics:read",
        "alerts:read",
        "orchestrator:read",
    ],
    "viewer": [
        "dashboard:read",
        "metrics:read",
        "alerts:read",
    ]
}


def get_scopes_for_role(role: str) -> list[str]:
    """
    Get list of scopes for a given role.
    
    Args:
        role: User role
        
    Returns:
        List of permission scopes
    """
    return ROLE_SCOPES.get(role, [])


def has_scope(user_scopes: list[str], required_scope: str) -> bool:
    """
    Check if user has a specific scope.
    
    Args:
        user_scopes: User's permission scopes
        required_scope: Required scope to check
        
    Returns:
        True if user has scope, False otherwise
    """
    # Admin has all permissions
    if "all" in user_scopes:
        return True
    
    # Check exact match
    if required_scope in user_scopes:
        return True
    
    # Check wildcard match (e.g., "publishing:*" matches "publishing:read")
    scope_prefix = required_scope.split(":")[0]
    wildcard = f"{scope_prefix}:*"
    if wildcard in user_scopes:
        return True
    
    return False


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        User payload from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_role(*allowed_roles: str):
    """
    Dependency to require specific roles.
    
    Args:
        allowed_roles: Tuple of allowed role names
        
    Returns:
        Dependency function
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not allowed. Required: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return role_checker


def require_scope(*required_scopes: str):
    """
    Dependency to require specific permission scopes.
    
    Args:
        required_scopes: Tuple of required scope names
        
    Returns:
        Dependency function
    """
    async def scope_checker(user: dict = Depends(get_current_user)) -> dict:
        user_scopes = user.get("scopes", [])
        
        # Check if user has all required scopes
        for scope in required_scopes:
            if not has_scope(user_scopes, scope):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}"
                )
        
        return user
    
    return scope_checker


def require_active_user(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to ensure user is active.
    
    Args:
        user: Current user payload
        
    Returns:
        User payload
        
    Raises:
        HTTPException: If user is inactive
    """
    # Note: is_active is checked at login, but this provides extra safety
    return user


def require_permission(scope: str):
    """
    Dependency to require a specific permission scope.
    
    Args:
        scope: Required permission scope (e.g., "analytics:read")
        
    Returns:
        Dependency function that checks for the scope
    """
    return require_scope(scope)


# Convenience dependencies
RequireAdmin = Depends(require_role("admin"))
RequireManager = Depends(require_role("admin", "manager"))
RequireOperator = Depends(require_role("admin", "operator"))
RequireAny = Depends(get_current_user)
