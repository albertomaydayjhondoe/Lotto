"""
Tests for PASO 5.2: SocialAccount + Credentials → Provider Client Binding

This test suite validates the account binding layer that connects:
- SocialAccountModel (with encrypted credentials)
- Secure credentials service (PASO 5.1)
- Platform-specific publishing clients (Instagram/TikTok/YouTube)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime

from app.models.database import SocialAccountModel
from app.services.social_accounts import set_account_credentials
from app.publishing_integrations import (
    get_provider_client_for_account,
    AccountCredentialsError,
    UnsupportedPlatformError,
    InstagramPublishingClient,
    TikTokPublishingClient,
    YouTubePublishingClient
)
from app.core.config import settings
from cryptography.fernet import Fernet
from test_db import init_test_db, drop_test_db, get_test_session


# Fixtures for test database
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db():
    """Get async test database session"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
def test_encryption_key():
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode('utf-8')


@pytest_asyncio.fixture
def configure_test_key(test_encryption_key, monkeypatch):
    """Configure test encryption key in settings."""
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', test_encryption_key)
    return test_encryption_key


# Test 1: Instagram Provider Binding
@pytest.mark.asyncio
async def test_get_provider_client_for_account_instagram_ok(
    db,
    configure_test_key
):
    """
    Test successful binding of Instagram account with credentials to client.
    
    Validates:
    - SocialAccount is created and credentials stored
    - get_provider_client_for_account returns Instagram client
    - Client has correct configuration from account + credentials
    """
    # Create Instagram account
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@test_ig_account",
        external_id="123456789_ig",
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store credentials
    instagram_creds = {
        "access_token": "IG_TEST_ACCESS_TOKEN_12345",
        "instagram_account_id": "987654321_ig_override",
        "facebook_page_id": "FB_PAGE_123"
    }
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds=instagram_creds
    )
    
    # Get provider client
    client = await get_provider_client_for_account(db, account)
    
    # Validate client type
    assert isinstance(client, InstagramPublishingClient)
    assert client.platform_name == "instagram"
    
    # Validate configuration
    assert client.config["access_token"] == "IG_TEST_ACCESS_TOKEN_12345"
    # account.external_id has priority over creds when set
    assert client.config["instagram_account_id"] == "123456789_ig"
    assert client.config["facebook_page_id"] == "FB_PAGE_123"
    assert client.config["account_handle"] == "@test_ig_account"
    assert client.config["account_id"] == str(account.id)


# Test 2: TikTok Provider Binding
@pytest.mark.asyncio
async def test_get_provider_client_for_account_tiktok_ok(
    db,
    configure_test_key
):
    """
    Test successful binding of TikTok account with credentials to client.
    
    Validates:
    - TikTok-specific configuration is built correctly
    - Client receives client_key, client_secret, access_token
    - Optional fields like open_id and refresh_token are included
    """
    # Create TikTok account
    account = SocialAccountModel(
        id=uuid4(),
        platform="tiktok",
        handle="@test_tiktok",
        external_id="TT_OPEN_ID_12345",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store TikTok credentials
    tiktok_creds = {
        "client_key": "TT_CLIENT_KEY_ABC",
        "client_secret": "TT_CLIENT_SECRET_XYZ",
        "access_token": "TT_ACCESS_TOKEN_789",
        "refresh_token": "TT_REFRESH_TOKEN_456"
    }
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds=tiktok_creds
    )
    
    # Get provider client
    client = await get_provider_client_for_account(db, account)
    
    # Validate client type
    assert isinstance(client, TikTokPublishingClient)
    assert client.platform_name == "tiktok"
    
    # Validate configuration
    assert client.config["client_key"] == "TT_CLIENT_KEY_ABC"
    assert client.config["client_secret"] == "TT_CLIENT_SECRET_XYZ"
    assert client.config["access_token"] == "TT_ACCESS_TOKEN_789"
    assert client.config["refresh_token"] == "TT_REFRESH_TOKEN_456"
    assert client.config["open_id"] == "TT_OPEN_ID_12345"  # From account.external_id
    assert client.config["account_handle"] == "@test_tiktok"


# Test 3: YouTube Provider Binding
@pytest.mark.asyncio
async def test_get_provider_client_for_account_youtube_ok(
    db,
    configure_test_key
):
    """
    Test successful binding of YouTube account with credentials to client.
    
    Validates:
    - YouTube OAuth configuration is built correctly
    - Client receives client_id, client_secret, refresh_token
    - Optional channel_id is included from account or credentials
    """
    # Create YouTube account
    account = SocialAccountModel(
        id=uuid4(),
        platform="youtube",
        handle="@TestYouTubeChannel",
        external_id="UC_CHANNEL_ID_123456",
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store YouTube credentials
    youtube_creds = {
        "client_id": "YT_CLIENT_ID_GOOGLE_123.apps.googleusercontent.com",
        "client_secret": "YT_CLIENT_SECRET_ABC123",
        "refresh_token": "YT_REFRESH_TOKEN_XYZ789",
        "access_token": "YT_ACCESS_TOKEN_CURRENT"  # Optional
    }
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds=youtube_creds
    )
    
    # Get provider client
    client = await get_provider_client_for_account(db, account)
    
    # Validate client type
    assert isinstance(client, YouTubePublishingClient)
    assert client.platform_name == "youtube"
    
    # Validate configuration
    assert client.config["client_id"] == "YT_CLIENT_ID_GOOGLE_123.apps.googleusercontent.com"
    assert client.config["client_secret"] == "YT_CLIENT_SECRET_ABC123"
    assert client.config["refresh_token"] == "YT_REFRESH_TOKEN_XYZ789"
    assert client.config["access_token"] == "YT_ACCESS_TOKEN_CURRENT"
    assert client.config["channel_id"] == "UC_CHANNEL_ID_123456"  # From external_id
    assert client.config["account_handle"] == "@TestYouTubeChannel"


# Test 4: Account Without Credentials Raises Error
@pytest.mark.asyncio
async def test_get_provider_client_for_account_without_credentials_raises(
    db,
    configure_test_key
):
    """
    Test that account without credentials raises AccountCredentialsError.
    
    Validates:
    - Creating account without calling set_account_credentials
    - get_provider_client_for_account raises clear error
    - Error message includes account details for debugging
    """
    # Create account without credentials
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@no_creds_account",
        external_id="NO_CREDS_123",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Try to get client - should fail
    with pytest.raises(AccountCredentialsError) as exc_info:
        await get_provider_client_for_account(db, account)
    
    # Validate error message
    error_message = str(exc_info.value)
    assert "No credentials configured" in error_message
    assert str(account.id) in error_message
    assert "instagram" in error_message
    assert "@no_creds_account" in error_message
    assert "set_account_credentials" in error_message


# Test 5: Unsupported Platform Raises Error
@pytest.mark.asyncio
async def test_get_provider_client_for_account_unsupported_platform(
    db,
    configure_test_key
):
    """
    Test that unsupported platform raises UnsupportedPlatformError.
    
    Validates:
    - Account with unknown platform (not instagram/tiktok/youtube)
    - get_provider_client_for_account raises UnsupportedPlatformError
    - Error message lists supported platforms
    """
    # Create account with unsupported platform
    account = SocialAccountModel(
        id=uuid4(),
        platform="snapchat",  # Not supported yet
        handle="@snap_account",
        external_id="SNAP_123",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store dummy credentials
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds={"access_token": "SNAP_TOKEN"}
    )
    
    # Try to get client - should fail
    with pytest.raises(UnsupportedPlatformError) as exc_info:
        await get_provider_client_for_account(db, account)
    
    # Validate error message
    error_message = str(exc_info.value)
    assert "snapchat" in error_message.lower() or "not supported" in error_message.lower()
    assert "instagram" in error_message.lower() or "tiktok" in error_message.lower()


# Test 6: Instagram with External ID Fallback
@pytest.mark.asyncio
async def test_get_provider_client_instagram_uses_external_id_fallback(
    db,
    configure_test_key
):
    """
    Test that instagram_account_id falls back to account.external_id.
    
    Validates:
    - If credentials don't have instagram_account_id
    - Config uses account.external_id as fallback
    """
    # Create account with external_id but creds without instagram_account_id
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@fallback_test",
        external_id="FALLBACK_IG_ID_999",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store credentials WITHOUT instagram_account_id
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds={"access_token": "IG_TOKEN_ONLY"}
    )
    
    # Get client
    client = await get_provider_client_for_account(db, account)
    
    # Should use external_id as fallback
    assert client.config["instagram_account_id"] == "FALLBACK_IG_ID_999"
    assert client.config["access_token"] == "IG_TOKEN_ONLY"


# Test 7: Case Insensitive Platform Matching
@pytest.mark.asyncio
async def test_get_provider_client_platform_case_insensitive(
    db,
    configure_test_key
):
    """
    Test that platform matching is case-insensitive.
    
    Validates:
    - Platform="INSTAGRAM" works same as "instagram"
    - Platform="TikTok" works same as "tiktok"
    """
    # Create account with uppercase platform
    account = SocialAccountModel(
        id=uuid4(),
        platform="INSTAGRAM",  # Uppercase
        handle="@case_test",
        external_id="CASE_IG_123",
        is_main_account=0,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store credentials
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds={
            "access_token": "CASE_TOKEN",
            "instagram_account_id": "CASE_IG_123"
        }
    )
    
    # Should work despite uppercase
    client = await get_provider_client_for_account(db, account)
    assert isinstance(client, InstagramPublishingClient)


# Test 8: Client Authentication Flow (Stub Mode)
@pytest.mark.asyncio
async def test_provider_client_authentication_flow(
    db,
    configure_test_key
):
    """
    Test that client can be authenticated after creation.
    
    Validates:
    - Client is created in non-authenticated state
    - authenticate() can be called (stub mode)
    - is_authenticated property changes
    
    Note: This is stub mode - no real API calls
    """
    # Create account
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@auth_test",
        external_id="AUTH_IG_123",
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # Store credentials
    await set_account_credentials(
        db=db,
        account_id=account.id,
        creds={
            "access_token": "AUTH_TOKEN",
            "instagram_account_id": "AUTH_IG_123"
        }
    )
    
    # Get client
    client = await get_provider_client_for_account(db, account)
    
    # Initially not authenticated
    assert not client.is_authenticated
    
    # Authenticate (stub mode - no real API call)
    result = await client.authenticate()
    
    # Should now be authenticated
    assert result is True
    assert client.is_authenticated
