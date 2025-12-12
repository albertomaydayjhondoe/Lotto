"""
OAuth Service Data Models

Pydantic models for OAuth token management and refresh operations.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class OAuthTokenInfo(BaseModel):
    """
    OAuth token information for a social account.
    
    Contains all OAuth-related data including access token, refresh token,
    expiration time, and granted scopes.
    """
    access_token: str = Field(..., description="OAuth access token for API calls")
    refresh_token: str | None = Field(None, description="Refresh token for automatic renewal")
    expires_at: datetime | None = Field(None, description="UTC timestamp when access token expires")
    scopes: list[str] | None = Field(None, description="List of granted OAuth scopes")
    provider: Literal["instagram", "tiktok", "youtube", "other"] = Field(
        ..., 
        description="OAuth provider identifier"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "IGQVJXa1...",
                "refresh_token": "IGQVJXr2...",
                "expires_at": "2025-11-23T12:00:00Z",
                "scopes": ["instagram_basic", "instagram_content_publish"],
                "provider": "instagram"
            }
        }


class OAuthRefreshResult(BaseModel):
    """
    Result of an OAuth token refresh operation.
    
    Indicates whether the refresh was successful and provides details
    about the new token or failure reason.
    """
    success: bool = Field(..., description="Whether token refresh succeeded")
    provider: str = Field(..., description="OAuth provider that was refreshed")
    reason: str | None = Field(None, description="Failure reason if success=False")
    new_access_token: str | None = Field(None, description="New access token if successful")
    new_expires_at: datetime | None = Field(None, description="New expiration time if successful")
    
    class Config:
        json_schema_extra = {
            "example_success": {
                "success": True,
                "provider": "instagram",
                "reason": None,
                "new_access_token": "IGQVJXnew...",
                "new_expires_at": "2025-11-23T13:00:00Z"
            },
            "example_failure": {
                "success": False,
                "provider": "tiktok",
                "reason": "no_refresh_token",
                "new_access_token": None,
                "new_expires_at": None
            }
        }
