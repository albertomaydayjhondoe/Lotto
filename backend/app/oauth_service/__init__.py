"""
OAuth Service Module

This module provides OAuth token management infrastructure for social media platforms.
Handles token refresh, expiration checking, and integration with SocialAccountModel.

Modules:
- models: Pydantic models for OAuth data structures
- service: OAuth token management functions

Usage:
    from app.oauth_service import ensure_valid_access_token, OAuthTokenInfo
    
    account, refresh_result = await ensure_valid_access_token(db, account)
    if refresh_result and not refresh_result.success:
        logger.warning(f"Failed to refresh token: {refresh_result.reason}")
"""
from app.oauth_service.models import (
    OAuthTokenInfo,
    OAuthRefreshResult
)
from app.oauth_service.service import (
    get_account_oauth_info,
    is_token_expired_or_close,
    refresh_oauth_token,
    ensure_valid_access_token
)

__all__ = [
    "OAuthTokenInfo",
    "OAuthRefreshResult",
    "get_account_oauth_info",
    "is_token_expired_or_close",
    "refresh_oauth_token",
    "ensure_valid_access_token"
]
