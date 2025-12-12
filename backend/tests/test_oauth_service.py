"""
Tests for OAuth Service (PASO 5.4)

This test suite validates the OAuth token management infrastructure:
1. Token info retrieval
2. Expiration checking
3. Token refresh (simulated)
4. Automatic token refresh before expiration
5. Integration with account binding

All tests use simulated OAuth operations - no real API calls.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from app.oauth_service import (
    get_account_oauth_info,
    is_token_expired_or_close,
    refresh_oauth_token,
    ensure_valid_access_token,
    OAuthTokenInfo,
    OAuthRefreshResult
)
from app.models.database import SocialAccountModel
from app.core.config import settings
from test_db import init_test_db, drop_test_db, get_test_session


# Fixtures for test database
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def test_db():
    """Get async test database session"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
def configure_test_key(monkeypatch):
    """Configure test encryption key in settings."""
    test_key = Fernet.generate_key().decode('utf-8')
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', test_key)
    return test_key


@pytest_asyncio.fixture
async def social_account_without_oauth(test_db):
    """Create a social account without OAuth tokens."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="test_no_oauth",
        external_id="111111111",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(account)
    await test_db.commit()
    await test_db.refresh(account)
    return account


@pytest_asyncio.fixture
async def social_account_with_oauth(test_db):
    """Create a social account with OAuth tokens."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="test_with_oauth",
        external_id="222222222",
        is_main_account=0,
        is_active=1,
        # OAuth fields
        oauth_provider="instagram",
        oauth_access_token="IGQVJXtest_access_token_12345",
        oauth_refresh_token="IGQVJXtest_refresh_token_67890",
        oauth_expires_at=datetime.utcnow() + timedelta(days=30),  # Far future
        oauth_scopes=["instagram_basic", "instagram_content_publish"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(account)
    await test_db.commit()
    await test_db.refresh(account)
    return account


@pytest_asyncio.fixture
async def social_account_with_expired_token(test_db):
    """Create a social account with expired OAuth token."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="tiktok",
        handle="test_expired",
        external_id="333333333",
        is_main_account=0,
        is_active=1,
        # OAuth fields - expired token
        oauth_provider="tiktok",
        oauth_access_token="TT_old_access_token",
        oauth_refresh_token="TT_refresh_token",
        oauth_expires_at=datetime.utcnow() - timedelta(minutes=10),  # Expired 10 min ago
        oauth_scopes=["user.info.basic", "video.upload"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(account)
    await test_db.commit()
    await test_db.refresh(account)
    return account


@pytest_asyncio.fixture
async def social_account_with_close_expiry(test_db):
    """Create a social account with token close to expiration."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="youtube",
        handle="test_close_expiry",
        external_id="444444444",
        is_main_account=0,
        is_active=1,
        # OAuth fields - expires in 2 minutes
        oauth_provider="youtube",
        oauth_access_token="YT_access_token",
        oauth_refresh_token="YT_refresh_token",
        oauth_expires_at=datetime.utcnow() + timedelta(minutes=2),  # Expires soon
        oauth_scopes=["https://www.googleapis.com/auth/youtube.upload"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(account)
    await test_db.commit()
    await test_db.refresh(account)
    return account


# Test 1: get_account_oauth_info returns None when no token
@pytest.mark.asyncio
async def test_get_account_oauth_info_none_when_no_token(
    test_db, social_account_without_oauth
):
    """
    Test: get_account_oauth_info returns None when account has no OAuth token.
    
    Expected:
    - Function returns None
    - No errors raised
    """
    result = await get_account_oauth_info(test_db, str(social_account_without_oauth.id))
    
    assert result is None, "Should return None when account has no OAuth token"


# Test 2: get_account_oauth_info returns info
@pytest.mark.asyncio
async def test_get_account_oauth_info_returns_info(
    test_db, social_account_with_oauth
):
    """
    Test: get_account_oauth_info returns OAuthTokenInfo when tokens exist.
    
    Expected:
    - Returns OAuthTokenInfo instance
    - All fields correctly populated from database
    """
    result = await get_account_oauth_info(test_db, str(social_account_with_oauth.id))
    
    assert result is not None, "Should return OAuthTokenInfo"
    assert isinstance(result, OAuthTokenInfo)
    assert result.access_token == "IGQVJXtest_access_token_12345"
    assert result.refresh_token == "IGQVJXtest_refresh_token_67890"
    assert result.provider == "instagram"
    assert result.scopes == ["instagram_basic", "instagram_content_publish"]
    assert result.expires_at is not None


# Test 3: is_token_expired_or_close returns False for far future
@pytest.mark.asyncio
async def test_is_token_expired_or_close_false_for_far_future():
    """
    Test: Token with far future expiration is not considered expired.
    
    Expected:
    - is_token_expired_or_close returns False
    """
    token_info = OAuthTokenInfo(
        access_token="test_token",
        refresh_token="test_refresh",
        expires_at=datetime.utcnow() + timedelta(days=1),  # 1 day in future
        scopes=["basic"],
        provider="instagram"
    )
    
    result = is_token_expired_or_close(token_info, threshold_seconds=300)
    
    assert result is False, "Token expiring in 1 day should not be considered expired"


# Test 4: is_token_expired_or_close returns True for past
@pytest.mark.asyncio
async def test_is_token_expired_or_close_true_for_past():
    """
    Test: Token with past expiration is considered expired.
    
    Expected:
    - is_token_expired_or_close returns True
    """
    token_info = OAuthTokenInfo(
        access_token="test_token",
        refresh_token="test_refresh",
        expires_at=datetime.utcnow() - timedelta(minutes=1),  # 1 minute ago
        scopes=["basic"],
        provider="tiktok"
    )
    
    result = is_token_expired_or_close(token_info, threshold_seconds=300)
    
    assert result is True, "Token expired 1 minute ago should be considered expired"


# Test 5: is_token_expired_or_close returns True for threshold
@pytest.mark.asyncio
async def test_is_token_expired_or_close_true_for_threshold():
    """
    Test: Token close to expiration (within threshold) is considered expired.
    
    Expected:
    - is_token_expired_or_close returns True
    - Threshold of 300 seconds (5 minutes)
    - Token expires in 100 seconds
    """
    token_info = OAuthTokenInfo(
        access_token="test_token",
        refresh_token="test_refresh",
        expires_at=datetime.utcnow() + timedelta(seconds=100),  # 100 seconds from now
        scopes=["basic"],
        provider="youtube"
    )
    
    result = is_token_expired_or_close(token_info, threshold_seconds=300)
    
    assert result is True, "Token expiring in 100 seconds should be considered expired with 300s threshold"


# Test 6: is_token_expired_or_close returns False when expires_at is None
@pytest.mark.asyncio
async def test_is_token_expired_or_close_false_when_no_expiration():
    """
    Test: Token without expiration time is not considered expired.
    
    Expected:
    - is_token_expired_or_close returns False
    - Assumes token doesn't expire
    """
    token_info = OAuthTokenInfo(
        access_token="test_token",
        refresh_token="test_refresh",
        expires_at=None,  # No expiration
        scopes=["basic"],
        provider="other"
    )
    
    result = is_token_expired_or_close(token_info, threshold_seconds=300)
    
    assert result is False, "Token without expiration should not be considered expired"


# Test 7: refresh_oauth_token successful
@pytest.mark.asyncio
async def test_refresh_oauth_token_successful(
    test_db, social_account_with_oauth
):
    """
    Test: refresh_oauth_token successfully refreshes token when refresh_token exists.
    
    Expected:
    - Returns OAuthRefreshResult with success=True
    - oauth_access_token is updated in database
    - oauth_expires_at is updated to future time
    - new_access_token starts with "refreshed_"
    """
    old_token = social_account_with_oauth.oauth_access_token
    old_expires = social_account_with_oauth.oauth_expires_at
    
    result = await refresh_oauth_token(test_db, social_account_with_oauth)
    
    # Verify result
    assert result.success is True
    assert result.provider == "instagram"
    assert result.reason is None
    assert result.new_access_token is not None
    assert result.new_access_token.startswith("refreshed_")
    assert result.new_expires_at is not None
    assert result.new_expires_at > datetime.utcnow()
    
    # Verify database was updated
    await test_db.refresh(social_account_with_oauth)
    assert social_account_with_oauth.oauth_access_token != old_token
    assert social_account_with_oauth.oauth_access_token == result.new_access_token
    assert social_account_with_oauth.oauth_expires_at != old_expires
    assert social_account_with_oauth.oauth_expires_at == result.new_expires_at


# Test 8: refresh_oauth_token without refresh_token fails
@pytest.mark.asyncio
async def test_refresh_oauth_token_without_refresh_token_fails(
    test_db, social_account_without_oauth
):
    """
    Test: refresh_oauth_token fails when account has no refresh_token.
    
    Expected:
    - Returns OAuthRefreshResult with success=False
    - reason="no_refresh_token"
    - new_access_token is None
    """
    # Set access token but no refresh token
    social_account_without_oauth.oauth_provider = "instagram"
    social_account_without_oauth.oauth_access_token = "test_access_only"
    social_account_without_oauth.oauth_refresh_token = None
    await test_db.commit()
    
    result = await refresh_oauth_token(test_db, social_account_without_oauth)
    
    assert result.success is False
    assert result.reason == "no_refresh_token"
    assert result.new_access_token is None
    assert result.new_expires_at is None


# Test 9: ensure_valid_access_token refreshes when close to expiry
@pytest.mark.asyncio
async def test_ensure_valid_access_token_refreshes_when_close_to_expiry(
    test_db, social_account_with_close_expiry
):
    """
    Test: ensure_valid_access_token refreshes token when close to expiration.
    
    Expected:
    - Returns tuple (account, refresh_result)
    - refresh_result is not None
    - refresh_result.success is True
    - Token is updated
    """
    old_token = social_account_with_close_expiry.oauth_access_token
    
    account, refresh_result = await ensure_valid_access_token(
        test_db, social_account_with_close_expiry
    )
    
    # Verify refresh was attempted and successful
    assert refresh_result is not None, "Should attempt refresh for token close to expiry"
    assert refresh_result.success is True
    assert refresh_result.new_access_token is not None
    
    # Verify account was updated
    assert account.oauth_access_token != old_token
    assert account.oauth_access_token.startswith("refreshed_")


# Test 10: ensure_valid_access_token skips when far from expiry
@pytest.mark.asyncio
async def test_ensure_valid_access_token_skips_when_far_from_expiry(
    test_db, social_account_with_oauth
):
    """
    Test: ensure_valid_access_token skips refresh when token is far from expiration.
    
    Expected:
    - Returns tuple (account, None)
    - refresh_result is None (no refresh attempted)
    - Token is not changed
    """
    old_token = social_account_with_oauth.oauth_access_token
    
    account, refresh_result = await ensure_valid_access_token(
        test_db, social_account_with_oauth
    )
    
    # Verify no refresh was attempted
    assert refresh_result is None, "Should not refresh token far from expiry"
    
    # Verify token unchanged
    assert account.oauth_access_token == old_token


# Test 11: ensure_valid_access_token returns None when no OAuth token
@pytest.mark.asyncio
async def test_ensure_valid_access_token_none_when_no_token(
    test_db, social_account_without_oauth
):
    """
    Test: ensure_valid_access_token returns None result when account has no OAuth token.
    
    Expected:
    - Returns tuple (account, None)
    - No refresh attempted
    - No errors
    """
    account, refresh_result = await ensure_valid_access_token(
        test_db, social_account_without_oauth
    )
    
    assert refresh_result is None, "Should not attempt refresh when no OAuth token"
    assert account.id == social_account_without_oauth.id


# Test 12: binding calls ensure_valid_access_token before provider construction
@pytest.mark.asyncio
async def test_binding_calls_ensure_valid_access_token_before_provider_construction(
    test_db, social_account_with_oauth, configure_test_key, monkeypatch
):
    """
    Test: get_provider_client_for_account calls ensure_valid_access_token.
    
    Expected:
    - ensure_valid_access_token is called
    - Provider client is still constructed
    - Integration works correctly
    """
    from app.publishing_integrations.account_binding import get_provider_client_for_account
    from app.services.social_accounts import set_account_credentials
    
    # Set up credentials so binding doesn't fail
    credentials = {
        "access_token": "ig_test_token",
        "instagram_account_id": "222222222",
        "facebook_page_id": "page_123"
    }
    await set_account_credentials(test_db, social_account_with_oauth.id, credentials)
    
    # Track if ensure_valid_access_token was called
    original_ensure = ensure_valid_access_token
    ensure_called = False
    
    async def mock_ensure(db, account):
        nonlocal ensure_called
        ensure_called = True
        # Call original function
        return await original_ensure(db, account)
    
    monkeypatch.setattr(
        "app.publishing_integrations.account_binding.ensure_valid_access_token",
        mock_ensure
    )
    
    # Call get_provider_client_for_account
    client = await get_provider_client_for_account(test_db, social_account_with_oauth)
    
    # Verify ensure_valid_access_token was called
    assert ensure_called, "ensure_valid_access_token should be called in binding"
    
    # Verify client was created
    assert client is not None
    assert client.platform_name == "instagram"


# Test 13: refresh with expired token
@pytest.mark.asyncio
async def test_refresh_oauth_token_with_expired_token(
    test_db, social_account_with_expired_token
):
    """
    Test: refresh_oauth_token works even when current token is expired.
    
    Expected:
    - Refresh succeeds
    - New token is generated
    - New expiration is in the future
    """
    result = await refresh_oauth_token(test_db, social_account_with_expired_token)
    
    assert result.success is True
    assert result.new_access_token is not None
    assert result.new_expires_at > datetime.utcnow()
    
    # Verify database
    await test_db.refresh(social_account_with_expired_token)
    assert social_account_with_expired_token.oauth_expires_at > datetime.utcnow()
