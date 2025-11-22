"""
Account Binding Module for Publishing Integrations.

This module provides the glue between SocialAccountModel (with encrypted credentials)
and platform-specific publishing clients.

PASO 5.2: SocialAccount + Credentials → Provider Client binding
PASO 5.4: Added OAuth token refresh before client construction
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SocialAccountModel
from app.services.social_accounts import get_account_credentials
from app.publishing_integrations.base_client import BasePublishingClient
from app.oauth_service import ensure_valid_access_token

logger = logging.getLogger(__name__)


class AccountCredentialsError(Exception):
    """Raised when account credentials are missing or invalid."""
    pass


class UnsupportedPlatformError(Exception):
    """Raised when platform is not supported."""
    pass


async def get_provider_client_for_account(
    db: AsyncSession,
    account: SocialAccountModel
) -> BasePublishingClient:
    """
    Get a configured provider client for a social account.
    
    This function:
    1. Ensures OAuth access token is valid (refreshes if needed) - PASO 5.4
    2. Retrieves encrypted credentials from the account
    3. Decrypts credentials using the secure credentials service
    4. Maps account fields + credentials to provider-specific config
    5. Returns an initialized provider client ready to use
    
    Args:
        db: Database session
        account: SocialAccountModel instance with platform and credentials
    
    Returns:
        BasePublishingClient: Platform-specific client (Instagram/TikTok/YouTube)
        
    Raises:
        AccountCredentialsError: If account has no credentials configured
        UnsupportedPlatformError: If platform is not supported
        ValueError: If required config fields are missing
        
    Example:
        >>> account = await db.get(SocialAccountModel, account_id)
        >>> client = await get_provider_client_for_account(db, account)
        >>> await client.authenticate()
        >>> result = await client.upload_video("/path/to/video.mp4")
        >>> await client.publish_post(result["video_id"], caption="Hello!")
    """
    # Import here to avoid circular dependency
    from app.publishing_integrations.instagram_client import InstagramPublishingClient
    from app.publishing_integrations.tiktok_client import TikTokPublishingClient
    from app.publishing_integrations.youtube_client import YouTubePublishingClient
    
    # Step 0: Ensure OAuth access token is valid (PASO 5.4)
    # This will automatically refresh the token if it's expired or close to expiration
    account, refresh_result = await ensure_valid_access_token(db, account)
    
    if refresh_result:
        if refresh_result.success:
            logger.info(
                f"OAuth token refreshed for account {account.id} ({refresh_result.provider}). "
                f"New expiration: {refresh_result.new_expires_at}"
            )
        else:
            logger.warning(
                f"Failed to refresh OAuth token for account {account.id} "
                f"({refresh_result.provider}): {refresh_result.reason}. "
                f"Continuing with existing token..."
            )
    
    # Step 1: Retrieve and decrypt credentials
    creds = await get_account_credentials(db, account.id)
    
    if creds is None:
        raise AccountCredentialsError(
            f"No credentials configured for social account {account.id} "
            f"(platform: {account.platform}, handle: {account.handle}). "
            f"Use set_account_credentials() to configure credentials first."
        )
    
    # Step 2: Map platform to config structure
    platform = account.platform.lower()
    
    if platform == "instagram":
        config = _build_instagram_config(account, creds)
        return InstagramPublishingClient(config=config)
    elif platform == "tiktok":
        config = _build_tiktok_config(account, creds)
        return TikTokPublishingClient(config=config)
    elif platform == "youtube":
        config = _build_youtube_config(account, creds)
        return YouTubePublishingClient(config=config)
    else:
        raise UnsupportedPlatformError(
            f"Platform '{account.platform}' is not supported. "
            f"Supported platforms: instagram, tiktok, youtube"
        )


def _build_instagram_config(
    account: SocialAccountModel,
    creds: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build Instagram client configuration.
    
    Required fields:
    - access_token: Instagram Graph API access token
    - instagram_account_id: Instagram Business Account ID
    
    Args:
        account: SocialAccountModel with platform="instagram"
        creds: Decrypted credentials dictionary
    
    Returns:
        dict: Configuration for InstagramPublishingClient
    """
    config = {
        "access_token": creds.get("access_token"),
        # Use external_id from account if set, otherwise from creds
        "instagram_account_id": (
            account.external_id or 
            creds.get("instagram_account_id")
        ),
    }
    
    # Optional fields from credentials
    if "facebook_page_id" in creds:
        config["facebook_page_id"] = creds["facebook_page_id"]
    
    # Include account metadata for reference
    config["account_handle"] = account.handle
    config["account_id"] = str(account.id)
    
    return config


def _build_tiktok_config(
    account: SocialAccountModel,
    creds: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build TikTok client configuration.
    
    Required fields:
    - client_key: TikTok app client key
    - client_secret: TikTok app client secret
    - access_token: User access token
    
    Args:
        account: SocialAccountModel with platform="tiktok"
        creds: Decrypted credentials dictionary
    
    Returns:
        dict: Configuration for TikTokPublishingClient
    """
    config = {
        "client_key": creds.get("client_key"),
        "client_secret": creds.get("client_secret"),
        "access_token": creds.get("access_token"),
    }
    
    # Optional: TikTok user open_id
    if account.external_id:
        config["open_id"] = account.external_id
    elif "open_id" in creds:
        config["open_id"] = creds["open_id"]
    
    # Optional: refresh token for token renewal
    if "refresh_token" in creds:
        config["refresh_token"] = creds["refresh_token"]
    
    # Include account metadata
    config["account_handle"] = account.handle
    config["account_id"] = str(account.id)
    
    return config


def _build_youtube_config(
    account: SocialAccountModel,
    creds: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build YouTube client configuration.
    
    Required fields:
    - client_id: Google OAuth client ID
    - client_secret: Google OAuth client secret
    - refresh_token: YouTube OAuth refresh token
    
    Args:
        account: SocialAccountModel with platform="youtube"
        creds: Decrypted credentials dictionary
    
    Returns:
        dict: Configuration for YouTubePublishingClient
    """
    config = {
        "client_id": creds.get("client_id"),
        "client_secret": creds.get("client_secret"),
        "refresh_token": creds.get("refresh_token"),
    }
    
    # Optional: YouTube channel ID
    if account.external_id:
        config["channel_id"] = account.external_id
    elif "channel_id" in creds:
        config["channel_id"] = creds["channel_id"]
    
    # Optional: access token (if available, avoids refresh)
    if "access_token" in creds:
        config["access_token"] = creds["access_token"]
    
    # Include account metadata
    config["account_handle"] = account.handle
    config["account_id"] = str(account.id)
    
    return config


def validate_config(platform: str, config: Dict[str, Any]) -> None:
    """
    Validate that config has required fields for platform.
    
    This is an optional validation helper. Clients should also validate internally.
    
    Args:
        platform: Platform name (instagram, tiktok, youtube)
        config: Configuration dictionary
        
    Raises:
        ValueError: If required fields are missing
    """
    required_fields = {
        "instagram": ["access_token", "instagram_account_id"],
        "tiktok": ["client_key", "client_secret", "access_token"],
        "youtube": ["client_id", "client_secret", "refresh_token"],
    }
    
    if platform not in required_fields:
        raise ValueError(f"Unknown platform: {platform}")
    
    missing = [
        field for field in required_fields[platform]
        if not config.get(field)
    ]
    
    if missing:
        raise ValueError(
            f"Missing required fields for {platform}: {', '.join(missing)}"
        )
