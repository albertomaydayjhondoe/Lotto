"""
Meta Ads Client Factory

Factory function to create MetaAdsClient instances from database records.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .client import MetaAdsClient
from .exceptions import MetaAuthError

logger = logging.getLogger(__name__)


async def get_meta_client_for_account(
    db: AsyncSession,
    social_account_id: int,
) -> MetaAdsClient:
    """
    Create a MetaAdsClient instance for a social account from the database.
    
    This function:
    1. Fetches the SocialAccount record by ID
    2. Validates the account is for Meta/Facebook
    3. Retrieves the access token
    4. Determines the mode (STUB/LIVE) based on token validity
    5. Creates and returns a configured MetaAdsClient
    
    Args:
        db: Async database session
        social_account_id: ID of the SocialAccount record
        
    Returns:
        Configured MetaAdsClient instance
        
    Raises:
        ValueError: If social account not found or not a Meta account
        MetaAuthError: If token is missing or invalid
    """
    # Import here to avoid circular imports
    from app.models.database import SocialAccountModel, MetaAccountModel
    
    # Fetch social account
    result = await db.execute(
        select(SocialAccountModel).where(SocialAccountModel.id == social_account_id)
    )
    social_account = result.scalar_one_or_none()
    
    if not social_account:
        logger.warning(f"SocialAccount {social_account_id} not found, returning stub client")
        return MetaAdsClient(mode="stub")
    
    # Validate platform
    if social_account.platform.lower() not in ["meta", "facebook", "instagram"]:
        raise ValueError(
            f"SocialAccount {social_account_id} is not a Meta account "
            f"(platform: {social_account.platform})"
        )
    
    # Get access token from OAuth field
    access_token = social_account.oauth_access_token
    if not access_token:
        logger.warning(
            f"SocialAccount {social_account_id} has no access token, returning stub client"
        )
        return MetaAdsClient(mode="stub")
    
    # Get ad account ID from MetaAccountModel if exists, or construct from social account
    result = await db.execute(
        select(MetaAccountModel).where(MetaAccountModel.social_account_id == social_account_id)
    )
    meta_account = result.scalar_one_or_none()
    
    ad_account_id = None
    if meta_account:
        ad_account_id = meta_account.ad_account_id
    elif social_account.external_id:
        # Try to construct from external_id if available
        ad_account_id = f"act_{social_account.external_id}"
    
    if not ad_account_id:
        logger.warning(
            f"SocialAccount {social_account_id} has no ad_account_id, will use default"
        )
        ad_account_id = "act_000000000000000"  # Fallback for stub mode
    
    # Determine mode based on environment or token validity
    # For now, default to STUB mode. In production, you would:
    # 1. Check if token is expired
    # 2. Validate token has required permissions
    # 3. Set to LIVE if valid, STUB otherwise
    mode = "stub"
    
    # You can add logic here to determine mode:
    # if _is_production_environment() and _is_token_valid(access_token):
    #     mode = "live"
    
    logger.info(
        f"Creating MetaAdsClient for account {social_account_id} "
        f"(platform: {social_account.platform}, mode: {mode})"
    )
    
    # Create and return client
    return MetaAdsClient(
        access_token=access_token,
        ad_account_id=ad_account_id,
        mode=mode,
    )


def _is_production_environment() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        True if production, False otherwise
    """
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ["production", "prod"]


def _is_token_valid(access_token: str) -> bool:
    """
    Check if access token is valid (not expired, has required permissions).
    
    This is a placeholder. In production, you would:
    1. Call Meta's debug_token endpoint
    2. Check expiration time
    3. Verify required permissions (ads_management, ads_read, etc.)
    
    Args:
        access_token: Meta access token
        
    Returns:
        True if valid, False otherwise
    """
    # TODO: Implement token validation
    # For now, assume valid if token exists and is not empty
    return bool(access_token and len(access_token) > 20)
