"""
Credentials encryption/decryption service for social media accounts.

This module provides secure storage of platform credentials using Fernet symmetric encryption.
All credentials are encrypted before storage and decrypted on retrieval.

PASO 5.1: Secure Credentials System
"""
import json
from typing import Dict, Any
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    """
    Get configured Fernet cipher instance.
    
    Raises:
        ValueError: If CREDENTIALS_ENCRYPTION_KEY is not configured in settings
    
    Returns:
        Fernet: Configured Fernet cipher for encryption/decryption
    """
    if not settings.CREDENTIALS_ENCRYPTION_KEY:
        raise ValueError(
            "CREDENTIALS_ENCRYPTION_KEY must be configured in environment variables. "
            "Generate a key using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    try:
        # Ensure key is bytes
        key = settings.CREDENTIALS_ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode('utf-8')
        return Fernet(key)
    except Exception as e:
        raise ValueError(f"Invalid CREDENTIALS_ENCRYPTION_KEY format: {e}")


def encrypt_credentials(raw: Dict[str, Any]) -> bytes:
    """
    Encrypt credentials dictionary to encrypted bytes.
    
    The credentials dictionary is serialized to JSON (UTF-8) and then encrypted
    using Fernet symmetric encryption.
    
    Args:
        raw: Dictionary containing credentials (e.g., access_token, refresh_token)
    
    Returns:
        bytes: Encrypted credentials token
    
    Raises:
        ValueError: If CREDENTIALS_ENCRYPTION_KEY is not configured
        
    Example:
        >>> creds = {"access_token": "abc123", "refresh_token": "xyz789"}
        >>> token = encrypt_credentials(creds)
        >>> # token is now encrypted bytes suitable for database storage
    """
    fernet = _get_fernet()
    
    # Serialize dict to JSON bytes
    json_bytes = json.dumps(raw, ensure_ascii=False).encode('utf-8')
    
    # Encrypt and return
    return fernet.encrypt(json_bytes)


def decrypt_credentials(token: bytes) -> Dict[str, Any]:
    """
    Decrypt credentials token back to dictionary.
    
    Args:
        token: Encrypted credentials bytes (from encrypt_credentials)
    
    Returns:
        dict: Decrypted credentials dictionary
    
    Raises:
        InvalidToken: If token is invalid or encryption key doesn't match
        ValueError: If CREDENTIALS_ENCRYPTION_KEY is not configured
        
    Example:
        >>> creds = decrypt_credentials(token)
        >>> print(creds["access_token"])
        'abc123'
    """
    fernet = _get_fernet()
    
    try:
        # Decrypt to JSON bytes
        json_bytes = fernet.decrypt(token)
        
        # Parse JSON and return dict
        return json.loads(json_bytes.decode('utf-8'))
    except InvalidToken:
        # Re-raise InvalidToken as-is for proper error handling
        raise
    except Exception as e:
        # Wrap other errors
        raise ValueError(f"Failed to decrypt credentials: {e}")
