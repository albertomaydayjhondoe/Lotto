"""
High-level service layer for managing social account credentials.

This module provides business logic for securely storing and retrieving
encrypted credentials for social media platform accounts.

PASO 5.1: Secure Credentials System
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import InvalidToken

from app.models.database import SocialAccountModel
from app.security.credentials import encrypt_credentials, decrypt_credentials


logger = logging.getLogger(__name__)

# Version string for current encryption format
CREDENTIALS_VERSION = "fernet-v1"


async def set_account_credentials(
    db: AsyncSession,
    account_id: UUID,
    creds: Dict[str, Any]
) -> SocialAccountModel:
    """
    Store encrypted credentials for a social account.
    
    This function:
    1. Fetches the social account by ID
    2. Encrypts the credentials dictionary using Fernet
    3. Stores encrypted data in encrypted_credentials field
    4. Updates credentials_version and credentials_updated_at
    5. Commits changes and returns updated model
    
    Args:
        db: Database session
        account_id: UUID of the social account
        creds: Dictionary containing platform credentials
               (e.g., {"access_token": "...", "refresh_token": "..."})
    
    Returns:
        SocialAccountModel: Updated account with encrypted credentials
    
    Raises:
        ValueError: If account not found or encryption key not configured
        
    Example:
        >>> account = await set_account_credentials(
        ...     db=db,
        ...     account_id=account.id,
        ...     creds={"access_token": "abc123", "refresh_token": "xyz789"}
        ... )
        >>> print(account.credentials_version)
        'fernet-v1'
    """
    # Fetch account
    result = await db.execute(
        select(SocialAccountModel).where(SocialAccountModel.id == account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise ValueError(f"Social account with id {account_id} not found")
    
    # Encrypt credentials
    try:
        encrypted_token = encrypt_credentials(creds)
    except Exception as e:
        logger.error(f"Failed to encrypt credentials for account {account_id}: {e}")
        raise
    
    # Update account
    account.encrypted_credentials = encrypted_token
    account.credentials_version = CREDENTIALS_VERSION
    account.credentials_updated_at = datetime.utcnow()
    
    # Commit changes
    await db.commit()
    await db.refresh(account)
    
    logger.info(
        f"Credentials updated for social account {account_id} "
        f"(platform={account.platform}, version={CREDENTIALS_VERSION})"
    )
    
    return account


async def get_account_credentials(
    db: AsyncSession,
    account_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Retrieve and decrypt credentials for a social account.
    
    This function:
    1. Fetches the social account by ID
    2. Returns None if no encrypted credentials exist
    3. Decrypts and returns credentials dictionary
    4. Handles decryption errors gracefully
    
    Args:
        db: Database session
        account_id: UUID of the social account
    
    Returns:
        dict: Decrypted credentials dictionary, or None if no credentials stored
    
    Raises:
        ValueError: If account not found or encryption key not configured
        
    Example:
        >>> creds = await get_account_credentials(db=db, account_id=account.id)
        >>> if creds:
        ...     print(creds["access_token"])
        ... else:
        ...     print("No credentials stored")
        
    Notes:
        - If decryption fails (e.g., wrong key, corrupted data), this function
          logs the error and returns None rather than raising an exception.
          This is a design decision to prevent application crashes due to
          credential issues - the caller should handle None appropriately.
    """
    # Fetch account
    result = await db.execute(
        select(SocialAccountModel).where(SocialAccountModel.id == account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise ValueError(f"Social account with id {account_id} not found")
    
    # Check if credentials exist
    if not account.encrypted_credentials:
        logger.debug(f"No credentials stored for social account {account_id}")
        return None
    
    # Decrypt credentials
    try:
        creds = decrypt_credentials(account.encrypted_credentials)
        logger.debug(
            f"Credentials retrieved for social account {account_id} "
            f"(platform={account.platform}, version={account.credentials_version})"
        )
        return creds
    except InvalidToken:
        # Invalid token - likely wrong encryption key or corrupted data
        logger.error(
            f"Failed to decrypt credentials for account {account_id}: "
            f"Invalid token (wrong key or corrupted data)"
        )
        # Return None rather than raising - caller should handle missing credentials
        return None
    except Exception as e:
        # Other decryption errors
        logger.error(
            f"Unexpected error decrypting credentials for account {account_id}: {e}"
        )
        # Return None rather than raising - caller should handle missing credentials
        return None
