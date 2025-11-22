"""
OAuth Service Functions

Core OAuth token management logic for social media platforms.
Handles token retrieval, expiration checking, refresh, and automatic renewal.

IMPORTANT: This is infrastructure-only (PASO 5.4).
Real OAuth API calls are not implemented yet - all operations are simulated.
TODO markers indicate where real API calls should be added in future phases.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SocialAccountModel
from app.oauth_service.models import OAuthTokenInfo, OAuthRefreshResult

logger = logging.getLogger(__name__)


async def get_account_oauth_info(
    db: AsyncSession,
    social_account_id: str
) -> OAuthTokenInfo | None:
    """
    Retrieve OAuth token information for a social account.
    
    Args:
        db: Database session
        social_account_id: UUID of the social account
        
    Returns:
        OAuthTokenInfo if OAuth tokens exist, None otherwise
        
    Example:
        >>> token_info = await get_account_oauth_info(db, account.id)
        >>> if token_info:
        ...     print(f"Token expires at: {token_info.expires_at}")
    """
    from sqlalchemy import select
    from uuid import UUID
    
    # Fetch account from database
    stmt = select(SocialAccountModel).where(SocialAccountModel.id == UUID(social_account_id))
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    
    if not account:
        logger.warning(f"Social account {social_account_id} not found")
        return None
    
    # Check if OAuth access token exists
    if not account.oauth_access_token:
        logger.debug(f"No OAuth token for account {social_account_id}")
        return None
    
    # Build token info from database fields
    return OAuthTokenInfo(
        access_token=account.oauth_access_token,
        refresh_token=account.oauth_refresh_token,
        expires_at=account.oauth_expires_at,
        scopes=account.oauth_scopes if account.oauth_scopes else None,
        provider=account.oauth_provider or account.platform or "other"
    )


def is_token_expired_or_close(
    info: OAuthTokenInfo,
    threshold_seconds: int = 300
) -> bool:
    """
    Check if an OAuth token is expired or close to expiration.
    
    Args:
        info: OAuth token information
        threshold_seconds: Time buffer in seconds before expiration (default: 5 minutes)
        
    Returns:
        True if token is expired or expires within threshold, False otherwise
        
    Note:
        If expires_at is None, assumes token doesn't expire and returns False.
        
    Example:
        >>> if is_token_expired_or_close(token_info, threshold_seconds=600):
        ...     # Refresh token if it expires within 10 minutes
        ...     await refresh_oauth_token(db, account)
    """
    # If no expiration time, assume token doesn't expire
    if info.expires_at is None:
        return False
    
    # Calculate expiration threshold
    now = datetime.utcnow()
    threshold_time = now + timedelta(seconds=threshold_seconds)
    
    # Token is expired or close to expiration
    is_expired = info.expires_at <= threshold_time
    
    if is_expired:
        logger.debug(
            f"Token for {info.provider} is expired or close to expiration. "
            f"Expires at: {info.expires_at}, Now: {now}, Threshold: {threshold_time}"
        )
    
    return is_expired


async def refresh_oauth_token(
    db: AsyncSession,
    account: SocialAccountModel
) -> OAuthRefreshResult:
    """
    Refresh an OAuth access token using the refresh token.
    
    This is the SINGLE POINT where real OAuth API calls will be made in the future.
    Currently simulates refresh for testing infrastructure.
    
    Args:
        db: Database session
        account: Social account with OAuth tokens
        
    Returns:
        OAuthRefreshResult indicating success or failure
        
    TODO (Future phases - PASO 5.5+):
        - Implement real Instagram token refresh: 
          POST https://graph.instagram.com/refresh_access_token
        - Implement real TikTok token refresh:
          POST https://open-api.tiktok.com/oauth/refresh_token/
        - Implement real YouTube token refresh:
          POST https://oauth2.googleapis.com/token
        - Add retry logic with exponential backoff
        - Handle rate limiting and API errors
        - Store refresh attempts in ledger
        
    Example:
        >>> result = await refresh_oauth_token(db, account)
        >>> if result.success:
        ...     logger.info(f"Token refreshed, new expiration: {result.new_expires_at}")
        >>> else:
        ...     logger.error(f"Refresh failed: {result.reason}")
    """
    provider = account.oauth_provider or account.platform or "unknown"
    
    # Check if refresh token exists
    if not account.oauth_refresh_token:
        logger.warning(f"No refresh token for account {account.id} ({provider})")
        return OAuthRefreshResult(
            success=False,
            provider=provider,
            reason="no_refresh_token",
            new_access_token=None,
            new_expires_at=None
        )
    
    # Check if we have current access token
    if not account.oauth_access_token:
        logger.warning(f"No access token to refresh for account {account.id} ({provider})")
        return OAuthRefreshResult(
            success=False,
            provider=provider,
            reason="no_access_token",
            new_access_token=None,
            new_expires_at=None
        )
    
    # ============================================================================
    # TODO: Real OAuth refresh implementation
    # ============================================================================
    # This is where real API calls will go in future phases:
    #
    # if provider == "instagram":
    #     # Instagram Graph API token refresh
    #     response = await httpx.post(
    #         "https://graph.instagram.com/refresh_access_token",
    #         params={
    #             "grant_type": "ig_refresh_token",
    #             "access_token": account.oauth_access_token
    #         }
    #     )
    #     new_token = response.json()["access_token"]
    #     new_expires_in = response.json()["expires_in"]
    #
    # elif provider == "tiktok":
    #     # TikTok OAuth token refresh
    #     response = await httpx.post(
    #         "https://open-api.tiktok.com/oauth/refresh_token/",
    #         json={
    #             "client_key": settings.TIKTOK_CLIENT_KEY,
    #             "grant_type": "refresh_token",
    #             "refresh_token": account.oauth_refresh_token
    #         }
    #     )
    #     new_token = response.json()["data"]["access_token"]
    #     new_expires_in = response.json()["data"]["expires_in"]
    #
    # elif provider == "youtube":
    #     # YouTube (Google OAuth) token refresh
    #     response = await httpx.post(
    #         "https://oauth2.googleapis.com/token",
    #         data={
    #             "client_id": settings.YOUTUBE_CLIENT_ID,
    #             "client_secret": settings.YOUTUBE_CLIENT_SECRET,
    #             "refresh_token": account.oauth_refresh_token,
    #             "grant_type": "refresh_token"
    #         }
    #     )
    #     new_token = response.json()["access_token"]
    #     new_expires_in = response.json()["expires_in"]
    # ============================================================================
    
    # SIMULATED REFRESH (for infrastructure testing)
    logger.info(f"Simulating token refresh for account {account.id} ({provider})")
    
    # Generate fake refreshed token
    old_token = account.oauth_access_token
    new_token = f"refreshed_{old_token}"
    
    # Set expiration to 60 minutes from now
    new_expires_at = datetime.utcnow() + timedelta(minutes=60)
    
    # Update account in database
    account.oauth_access_token = new_token
    account.oauth_expires_at = new_expires_at
    account.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(account)
    
    logger.info(
        f"Token refresh simulated for account {account.id}. "
        f"New expiration: {new_expires_at}"
    )
    
    return OAuthRefreshResult(
        success=True,
        provider=provider,
        reason=None,
        new_access_token=new_token,
        new_expires_at=new_expires_at
    )


async def ensure_valid_access_token(
    db: AsyncSession,
    account: SocialAccountModel
) -> tuple[SocialAccountModel, OAuthRefreshResult | None]:
    """
    Ensure an account has a valid (non-expired) OAuth access token.
    
    Automatically refreshes the token if it's expired or close to expiration.
    
    Args:
        db: Database session
        account: Social account to check
        
    Returns:
        Tuple of (updated_account, refresh_result)
        - updated_account: Account with potentially refreshed token
        - refresh_result: OAuthRefreshResult if refresh was attempted, None otherwise
        
    Workflow:
        1. Check if account has OAuth access token
        2. If no token, return (account, None)
        3. Check if token is expired or close to expiration
        4. If not expired, return (account, None)
        5. If expired, call refresh_oauth_token()
        6. Return (updated_account, refresh_result)
        
    Example:
        >>> account, refresh_result = await ensure_valid_access_token(db, account)
        >>> if refresh_result and not refresh_result.success:
        ...     logger.error(f"Failed to ensure valid token: {refresh_result.reason}")
        >>> # Use account.oauth_access_token for API calls
    """
    # Check if account has OAuth access token
    if not account.oauth_access_token:
        logger.debug(f"Account {account.id} has no OAuth access token")
        return (account, None)
    
    # Build token info
    token_info = OAuthTokenInfo(
        access_token=account.oauth_access_token,
        refresh_token=account.oauth_refresh_token,
        expires_at=account.oauth_expires_at,
        scopes=account.oauth_scopes if account.oauth_scopes else None,
        provider=account.oauth_provider or account.platform or "other"
    )
    
    # Check if token is expired or close to expiration
    if not is_token_expired_or_close(token_info, threshold_seconds=300):
        logger.debug(f"Token for account {account.id} is still valid")
        return (account, None)
    
    # Token is expired or close to expiration - refresh it
    logger.info(f"Token for account {account.id} needs refresh")
    refresh_result = await refresh_oauth_token(db, account)
    
    # Refresh account from database to get updated token
    await db.refresh(account)
    
    return (account, refresh_result)
