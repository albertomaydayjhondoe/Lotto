"""
Password hashing utilities.

Uses Argon2 for secure password hashing.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize password hasher with secure defaults
ph = PasswordHasher(
    time_cost=2,      # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=4,    # Number of parallel threads
    hash_len=32,      # Length of hash in bytes
    salt_len=16       # Length of salt in bytes
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        password_hash: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        ph.verify(password_hash, password)
        
        # Check if rehash is needed (parameters changed)
        if ph.check_needs_rehash(password_hash):
            # In production, you'd want to update the hash in DB here
            pass
            
        return True
    except VerifyMismatchError:
        return False
