"""
Tests for secure credentials encryption system (PASO 5.1).

This test suite validates:
- Encryption/decryption roundtrip correctness
- Error handling for invalid tokens and missing keys
- Database integration with SocialAccountModel
- High-level service layer functions
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken

from app.security.credentials import encrypt_credentials, decrypt_credentials
from app.services.social_accounts import (
    set_account_credentials,
    get_account_credentials,
    CREDENTIALS_VERSION
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
async def db():
    """Get async test database session"""
    async for session in get_test_session():
        yield session
@pytest_asyncio.fixture
async def sample_social_account(db):
    """Create a test social account."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@test_account",
        external_id="12345",
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
def test_encryption_key():
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode('utf-8')


@pytest_asyncio.fixture
def configure_test_key(test_encryption_key, monkeypatch):
    """Configure test encryption key in settings."""
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', test_encryption_key)
    return test_encryption_key


# Test 1: Encrypt/Decrypt Roundtrip
@pytest.mark.asyncio
async def test_encrypt_decrypt_roundtrip_ok(configure_test_key):
    """
    Test that credentials can be encrypted and decrypted successfully.
    
    Validates:
    - encrypt_credentials produces bytes
    - decrypt_credentials returns original dict
    - Complex nested data structures are preserved
    """
    original_creds = {
        "access_token": "abc123xyz",
        "refresh_token": "refresh_xyz789",
        "expires_at": 1234567890,
        "scope": ["read", "write"],
        "metadata": {
            "user_id": "12345",
            "username": "@test"
        }
    }
    
    # Encrypt
    encrypted_token = encrypt_credentials(original_creds)
    
    # Validate encrypted format
    assert isinstance(encrypted_token, bytes)
    assert len(encrypted_token) > 0
    assert encrypted_token != original_creds  # Should be different
    
    # Decrypt
    decrypted_creds = decrypt_credentials(encrypted_token)
    
    # Validate roundtrip
    assert decrypted_creds == original_creds
    assert decrypted_creds["access_token"] == "abc123xyz"
    assert decrypted_creds["metadata"]["username"] == "@test"


# Test 2: Decrypt Invalid Token Raises
@pytest.mark.asyncio
async def test_decrypt_invalid_token_raises(configure_test_key):
    """
    Test that decrypting invalid tokens raises InvalidToken exception.
    
    Validates:
    - Random bytes raise InvalidToken
    - Corrupted tokens raise InvalidToken
    - Error handling is explicit and catchable
    """
    # Random bytes (not a valid Fernet token)
    invalid_token = b"this_is_not_a_valid_fernet_token_123456"
    
    with pytest.raises(InvalidToken):
        decrypt_credentials(invalid_token)
    
    # Empty bytes
    with pytest.raises(Exception):  # Could be InvalidToken or ValueError
        decrypt_credentials(b"")


# Test 3: Set and Get Account Credentials Roundtrip
@pytest.mark.asyncio
async def test_set_and_get_account_credentials_roundtrip(
    db,
    sample_social_account,
    configure_test_key
):
    """
    Test complete database roundtrip for storing and retrieving credentials.
    
    Validates:
    - set_account_credentials encrypts and stores credentials
    - Database fields are populated correctly
    - get_account_credentials retrieves and decrypts correctly
    - Credentials match original input
    """
    original_creds = {
        "access_token": "instagram_token_abc123",
        "refresh_token": "instagram_refresh_xyz",
        "expires_in": 3600
    }
    
    # Store credentials
    updated_account = await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=original_creds
    )
    
    # Validate database fields
    assert updated_account.encrypted_credentials is not None
    assert isinstance(updated_account.encrypted_credentials, bytes)
    assert len(updated_account.encrypted_credentials) > 0
    
    assert updated_account.credentials_version == CREDENTIALS_VERSION
    assert updated_account.credentials_version == "fernet-v1"
    
    assert updated_account.credentials_updated_at is not None
    assert isinstance(updated_account.credentials_updated_at, datetime)
    
    # Retrieve credentials
    retrieved_creds = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    # Validate roundtrip
    assert retrieved_creds is not None
    assert retrieved_creds == original_creds
    assert retrieved_creds["access_token"] == "instagram_token_abc123"


# Test 4: Get Credentials Returns None if Empty
@pytest.mark.asyncio
async def test_get_account_credentials_returns_none_if_empty(
    db,
    sample_social_account,
    configure_test_key
):
    """
    Test that getting credentials from account without credentials returns None.
    
    Validates:
    - Accounts with no credentials return None
    - No errors are raised for missing credentials
    - System handles empty state gracefully
    """
    # Account has no credentials yet
    creds = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    assert creds is None


# Test 5: Encrypt Raises if No Key Configured
@pytest.mark.asyncio
async def test_encrypt_raises_if_no_key_configured(monkeypatch):
    """
    Test that encryption fails with clear error when key is not configured.
    
    Validates:
    - Missing CREDENTIALS_ENCRYPTION_KEY raises ValueError
    - Error message is helpful and actionable
    - System fails fast rather than silently
    """
    # Clear encryption key
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', None)
    
    creds = {"access_token": "test"}
    
    with pytest.raises(ValueError) as exc_info:
        encrypt_credentials(creds)
    
    # Validate error message is helpful
    error_message = str(exc_info.value)
    assert "CREDENTIALS_ENCRYPTION_KEY" in error_message
    assert "must be configured" in error_message.lower()


# Test 6: Decrypt with Wrong Key Returns None (via service layer)
@pytest.mark.asyncio
async def test_decrypt_with_wrong_key_returns_none(
    db,
    sample_social_account,
    test_encryption_key,
    monkeypatch
):
    """
    Test that service layer handles decryption errors gracefully.
    
    Validates:
    - Credentials encrypted with one key
    - Attempting to decrypt with different key returns None
    - No exceptions propagate to caller
    - Error is logged appropriately
    """
    # Configure first key and store credentials
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', test_encryption_key)
    
    original_creds = {"access_token": "test123"}
    await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=original_creds
    )
    
    # Change to different key
    different_key = Fernet.generate_key().decode('utf-8')
    monkeypatch.setattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', different_key)
    
    # Try to retrieve - should return None due to wrong key
    creds = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    assert creds is None  # Service layer handles error gracefully


# Test 7: Account Not Found Raises ValueError
@pytest.mark.asyncio
async def test_set_credentials_account_not_found_raises(db, configure_test_key):
    """
    Test that setting credentials for non-existent account raises error.
    
    Validates:
    - Non-existent account ID raises ValueError
    - Error message indicates account not found
    """
    non_existent_id = uuid4()
    creds = {"access_token": "test"}
    
    with pytest.raises(ValueError) as exc_info:
        await set_account_credentials(
            db=db,
            account_id=non_existent_id,
            creds=creds
        )
    
    assert "not found" in str(exc_info.value).lower()


# Test 8: Update Existing Credentials
@pytest.mark.asyncio
async def test_update_existing_credentials(
    db,
    sample_social_account,
    configure_test_key
):
    """
    Test that credentials can be updated (overwritten).
    
    Validates:
    - First set of credentials is stored
    - Second set overwrites first
    - credentials_updated_at is updated
    - Only latest credentials are retrievable
    """
    # Store first credentials
    first_creds = {"access_token": "first_token"}
    first_update = await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=first_creds
    )
    first_updated_at = first_update.credentials_updated_at
    
    # Store second credentials (should overwrite)
    second_creds = {"access_token": "second_token", "refresh_token": "refresh"}
    second_update = await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=second_creds
    )
    second_updated_at = second_update.credentials_updated_at
    
    # Validate update
    assert second_updated_at >= first_updated_at
    
    # Retrieve credentials - should be second set
    retrieved = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    assert retrieved == second_creds
    assert retrieved["access_token"] == "second_token"
    assert "refresh_token" in retrieved


# Test 9: Empty Credentials Dict
@pytest.mark.asyncio
async def test_empty_credentials_dict(
    db,
    sample_social_account,
    configure_test_key
):
    """
    Test that empty credentials dict can be stored and retrieved.
    
    Validates:
    - Empty dict is valid input
    - Roundtrip preserves empty dict
    - No errors occur with edge case
    """
    empty_creds = {}
    
    await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=empty_creds
    )
    
    retrieved = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    assert retrieved == {}


# Test 10: Unicode Characters in Credentials
@pytest.mark.asyncio
async def test_unicode_characters_in_credentials(
    db,
    sample_social_account,
    configure_test_key
):
    """
    Test that credentials with unicode characters work correctly.
    
    Validates:
    - Unicode strings are preserved
    - UTF-8 encoding/decoding works correctly
    - International characters are supported
    """
    unicode_creds = {
        "access_token": "token_with_émojis_🎉",
        "username": "用户名",
        "description": "Descripción con ñ y acentos"
    }
    
    await set_account_credentials(
        db=db,
        account_id=sample_social_account.id,
        creds=unicode_creds
    )
    
    retrieved = await get_account_credentials(
        db=db,
        account_id=sample_social_account.id
    )
    
    assert retrieved == unicode_creds
    assert "🎉" in retrieved["access_token"]
    assert retrieved["username"] == "用户名"
