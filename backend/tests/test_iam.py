"""
Comprehensive tests for IAM (Identity & Access Management) system.

Tests authentication, authorization, roles, permissions, and token lifecycle.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.auth.models import UserRegister, UserLogin, RefreshTokenRequest
from app.auth.service import (
    register_user, login_user, refresh_access_token, logout_user,
    get_user_by_id, revoke_all_user_tokens
)
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import (
    create_access_token, create_refresh_token, decode_access_token,
    decode_refresh_token
)
from app.auth.permissions import (
    get_scopes_for_role, has_scope, ROLE_SCOPES
)


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================

def test_password_hashing():
    """Test password hashing and verification."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_password_hash_uniqueness():
    """Test that same password generates different hashes (due to salt)."""
    password = "SamePassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different due to random salt
    assert hash1 != hash2
    # But both should verify correctly
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================

def test_access_token_creation_and_validation():
    """Test access token creation and decoding."""
    user_id = "test-user-123"
    email = "test@example.com"
    role = "admin"
    scopes = ["all"]
    
    token = create_access_token(user_id, email, role, scopes)
    payload = decode_access_token(token)
    
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["role"] == role
    assert payload["scopes"] == scopes
    assert payload["type"] == "access"


def test_refresh_token_creation_and_validation():
    """Test refresh token creation and decoding."""
    user_id = "test-user-456"
    
    token, expires = create_refresh_token(user_id)
    payload = decode_refresh_token(token)
    
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert expires > datetime.utcnow()


def test_access_token_invalid():
    """Test that invalid access token is rejected."""
    invalid_token = "invalid.token.here"
    payload = decode_access_token(invalid_token)
    
    assert payload is None


def test_refresh_token_invalid():
    """Test that invalid refresh token is rejected."""
    invalid_token = "invalid.token.here"
    payload = decode_refresh_token(invalid_token)
    
    assert payload is None


def test_jwt_expiration():
    """Test JWT token expiration detection."""
    # Create token that expires immediately
    import jwt
    from app.auth.jwt import SECRET_KEY, ALGORITHM
    
    expired_payload = {
        "sub": "user-123",
        "type": "access",
        "exp": datetime.utcnow() - timedelta(seconds=1),  # Expired 1 second ago
        "iat": datetime.utcnow() - timedelta(minutes=20)
    }
    
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    payload = decode_access_token(expired_token)
    
    assert payload is None  # Should be None due to expiration


# ============================================================================
# PERMISSIONS AND ROLES TESTS
# ============================================================================

def test_role_scopes_mapping():
    """Test that all roles have defined scopes."""
    for role in ["admin", "manager", "operator", "viewer"]:
        scopes = get_scopes_for_role(role)
        assert isinstance(scopes, list)
        assert len(scopes) > 0


def test_admin_has_all_scope():
    """Test that admin role has 'all' scope."""
    scopes = get_scopes_for_role("admin")
    assert "all" in scopes


def test_has_scope_admin():
    """Test that admin has access to any scope."""
    admin_scopes = ["all"]
    
    assert has_scope(admin_scopes, "publishing:read")
    assert has_scope(admin_scopes, "campaigns:write")
    assert has_scope(admin_scopes, "anything:else")


def test_has_scope_exact_match():
    """Test exact scope matching."""
    user_scopes = ["dashboard:read", "metrics:read"]
    
    assert has_scope(user_scopes, "dashboard:read")
    assert has_scope(user_scopes, "metrics:read")
    assert not has_scope(user_scopes, "dashboard:write")


def test_has_scope_wildcard():
    """Test wildcard scope matching."""
    user_scopes = ["publishing:*"]
    
    assert has_scope(user_scopes, "publishing:read")
    assert has_scope(user_scopes, "publishing:write")
    assert has_scope(user_scopes, "publishing:delete")
    assert not has_scope(user_scopes, "campaigns:read")


# ============================================================================
# USER REGISTRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_auth_register(db_session: AsyncSession):
    """Test user registration."""
    user_data = UserRegister(
        email="newuser@example.com",
        password="SecurePass123!",
        full_name="New User",
        role="viewer"
    )
    
    user = await register_user(db_session, user_data)
    
    assert user.email == "newuser@example.com"
    assert user.full_name == "New User"
    assert user.role == "viewer"
    assert user.is_active is True
    assert user.id is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession):
    """Test that duplicate email registration fails."""
    user_data = UserRegister(
        email="duplicate@example.com",
        password="SecurePass123!",
        full_name="First User",
        role="viewer"
    )
    
    await register_user(db_session, user_data)
    
    # Try to register same email again
    with pytest.raises(ValueError, match="Email already registered"):
        await register_user(db_session, user_data)


# ============================================================================
# USER LOGIN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_auth_login_success(db_session: AsyncSession):
    """Test successful user login."""
    # Register user
    user_data = UserRegister(
        email="logintest@example.com",
        password="SecurePass123!",
        full_name="Login Test",
        role="manager"
    )
    await register_user(db_session, user_data)
    
    # Login
    credentials = UserLogin(
        email="logintest@example.com",
        password="SecurePass123!"
    )
    
    tokens = await login_user(db_session, credentials)
    
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    assert tokens.expires_in > 0


@pytest.mark.asyncio
async def test_auth_login_wrong_password(db_session: AsyncSession):
    """Test login with wrong password."""
    # Register user
    user_data = UserRegister(
        email="wrongpass@example.com",
        password="CorrectPass123!",
        full_name="Wrong Pass Test",
        role="viewer"
    )
    await register_user(db_session, user_data)
    
    # Try login with wrong password
    credentials = UserLogin(
        email="wrongpass@example.com",
        password="WrongPassword123!"
    )
    
    with pytest.raises(ValueError, match="Invalid email or password"):
        await login_user(db_session, credentials)


@pytest.mark.asyncio
async def test_user_inactive_cannot_login(db_session: AsyncSession):
    """Test that inactive user cannot login."""
    from app.models.database import UserModel
    from sqlalchemy import update
    
    # Register user
    user_data = UserRegister(
        email="inactive@example.com",
        password="SecurePass123!",
        full_name="Inactive User",
        role="viewer"
    )
    user = await register_user(db_session, user_data)
    
    # Deactivate user
    await db_session.execute(
        update(UserModel)
        .where(UserModel.id == user.id)
        .values(is_active=0)
    )
    await db_session.commit()
    
    # Try to login
    credentials = UserLogin(
        email="inactive@example.com",
        password="SecurePass123!"
    )
    
    with pytest.raises(ValueError, match="User account is inactive"):
        await login_user(db_session, credentials)


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_auth_refresh(db_session: AsyncSession):
    """Test token refresh flow."""
    # Register and login
    user_data = UserRegister(
        email="refresh@example.com",
        password="SecurePass123!",
        full_name="Refresh Test",
        role="operator"
    )
    await register_user(db_session, user_data)
    
    credentials = UserLogin(
        email="refresh@example.com",
        password="SecurePass123!"
    )
    tokens = await login_user(db_session, credentials)
    
    # Refresh tokens
    new_tokens = await refresh_access_token(db_session, tokens.refresh_token)
    
    assert new_tokens.access_token != tokens.access_token
    assert new_tokens.refresh_token != tokens.refresh_token
    assert new_tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(db_session: AsyncSession):
    """Test that invalid refresh token is rejected."""
    invalid_token = "invalid.refresh.token"
    
    with pytest.raises(ValueError, match="Invalid or expired refresh token"):
        await refresh_access_token(db_session, invalid_token)


@pytest.mark.asyncio
async def test_refresh_token_revocation(db_session: AsyncSession):
    """Test that revoked refresh token cannot be used."""
    # Register, login, and immediately logout
    user_data = UserRegister(
        email="revoked@example.com",
        password="SecurePass123!",
        full_name="Revoked Test",
        role="viewer"
    )
    await register_user(db_session, user_data)
    
    credentials = UserLogin(
        email="revoked@example.com",
        password="SecurePass123!"
    )
    tokens = await login_user(db_session, credentials)
    
    # Logout (revokes token)
    await logout_user(db_session, tokens.refresh_token)
    
    # Try to use revoked token
    with pytest.raises(ValueError, match="Refresh token not found or revoked"):
        await refresh_access_token(db_session, tokens.refresh_token)


@pytest.mark.asyncio
async def test_jwt_refresh_flow(db_session: AsyncSession):
    """Test complete JWT refresh flow."""
    # Register and login
    user_data = UserRegister(
        email="flowtest@example.com",
        password="SecurePass123!",
        full_name="Flow Test",
        role="manager"
    )
    user = await register_user(db_session, user_data)
    
    credentials = UserLogin(
        email="flowtest@example.com",
        password="SecurePass123!"
    )
    tokens1 = await login_user(db_session, credentials)
    
    # Decode first access token
    payload1 = decode_access_token(tokens1.access_token)
    assert payload1["sub"] == user.id
    assert payload1["role"] == "manager"
    
    # Refresh tokens
    tokens2 = await refresh_access_token(db_session, tokens1.refresh_token)
    
    # Decode new access token
    payload2 = decode_access_token(tokens2.access_token)
    assert payload2["sub"] == user.id
    assert payload2["role"] == "manager"
    
    # Old refresh token should be revoked
    with pytest.raises(ValueError):
        await refresh_access_token(db_session, tokens1.refresh_token)


# ============================================================================
# LOGOUT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_auth_logout(db_session: AsyncSession):
    """Test user logout."""
    # Register and login
    user_data = UserRegister(
        email="logout@example.com",
        password="SecurePass123!",
        full_name="Logout Test",
        role="viewer"
    )
    await register_user(db_session, user_data)
    
    credentials = UserLogin(
        email="logout@example.com",
        password="SecurePass123!"
    )
    tokens = await login_user(db_session, credentials)
    
    # Logout
    success = await logout_user(db_session, tokens.refresh_token)
    assert success is True
    
    # Try to logout again with same token
    success2 = await logout_user(db_session, tokens.refresh_token)
    assert success2 is False  # Already revoked


# ============================================================================
# USER MANAGEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_me_endpoint(db_session: AsyncSession):
    """Test getting current user info."""
    # Register user
    user_data = UserRegister(
        email="me@example.com",
        password="SecurePass123!",
        full_name="Me Test",
        role="admin"
    )
    user = await register_user(db_session, user_data)
    
    # Get user by ID
    retrieved_user = await get_user_by_id(db_session, user.id)
    
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email
    assert retrieved_user.full_name == user.full_name
    assert retrieved_user.role == user.role


@pytest.mark.asyncio
async def test_revoke_all_tokens(db_session: AsyncSession):
    """Test revoking all user tokens."""
    # Register and create multiple sessions
    user_data = UserRegister(
        email="revokeall@example.com",
        password="SecurePass123!",
        full_name="Revoke All Test",
        role="viewer"
    )
    user = await register_user(db_session, user_data)
    
    credentials = UserLogin(
        email="revokeall@example.com",
        password="SecurePass123!"
    )
    
    # Login multiple times
    tokens1 = await login_user(db_session, credentials)
    tokens2 = await login_user(db_session, credentials)
    tokens3 = await login_user(db_session, credentials)
    
    # Revoke all
    count = await revoke_all_user_tokens(db_session, user.id)
    assert count == 3
    
    # All tokens should be revoked
    with pytest.raises(ValueError):
        await refresh_access_token(db_session, tokens1.refresh_token)
    with pytest.raises(ValueError):
        await refresh_access_token(db_session, tokens2.refresh_token)
    with pytest.raises(ValueError):
        await refresh_access_token(db_session, tokens3.refresh_token)


# ============================================================================
# ROLE AND PERMISSION TESTS
# ============================================================================

def test_admin_can_create_users():
    """Test that admin role has user creation permission."""
    admin_scopes = get_scopes_for_role("admin")
    assert has_scope(admin_scopes, "users:create")


def test_non_admin_cannot_create_users():
    """Test that non-admin roles don't have user creation permission."""
    for role in ["manager", "operator", "viewer"]:
        scopes = get_scopes_for_role(role)
        # They shouldn't have users:create unless they're admin
        if role != "admin":
            assert not has_scope(scopes, "users:create")


def test_role_scopes_apply_correctly():
    """Test that different roles have appropriate scopes."""
    # Manager should have publishing access
    manager_scopes = get_scopes_for_role("manager")
    assert has_scope(manager_scopes, "publishing:read")
    assert has_scope(manager_scopes, "campaigns:write")
    
    # Operator should have queue access
    operator_scopes = get_scopes_for_role("operator")
    assert has_scope(operator_scopes, "queue:read")
    assert has_scope(operator_scopes, "worker:write")
    
    # Viewer should only have read access
    viewer_scopes = get_scopes_for_role("viewer")
    assert has_scope(viewer_scopes, "dashboard:read")
    assert not has_scope(viewer_scopes, "publishing:write")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
