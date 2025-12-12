"""
Tests for Blacklist Manager
"""

import pytest
from backend.app.playlist_engine.curator_automailer import (
    BlacklistManagerStub,
    BlacklistType
)


def test_add_to_permanent_blacklist():
    """Test adding curator to permanent blacklist"""
    manager = BlacklistManagerStub()
    
    result = manager.add_to_permanent_blacklist(
        curator_email="spam@curator.local",
        reason="unsubscribe_request"
    )
    
    assert result["status"] == "blacklisted_permanent"
    assert result["curator_email"] == "spam@curator.local"
    
    # Verify blacklisted
    status = manager.is_blacklisted("spam@curator.local")
    assert status["is_blacklisted"] is True
    assert status["blacklist_type"] == "permanent"


def test_add_to_project_blacklist():
    """Test project-specific blacklist"""
    manager = BlacklistManagerStub()
    
    result = manager.add_to_project_blacklist(
        curator_email="curator@test.local",
        project_id="project_123",
        reason="not_interested"
    )
    
    assert result["status"] == "blacklisted_project"
    
    # Check with project ID
    status = manager.is_blacklisted("curator@test.local", project_id="project_123")
    assert status["is_blacklisted"] is True
    assert status["blacklist_type"] == "project"
    
    # Check without project ID (should not be blacklisted)
    status_no_project = manager.is_blacklisted("curator@test.local")
    assert status_no_project["is_blacklisted"] is False


def test_add_to_temporary_blacklist():
    """Test temporary blacklist with expiry"""
    manager = BlacklistManagerStub()
    
    result = manager.add_to_temporary_blacklist(
        curator_email="temp@curator.local",
        days=30,
        reason="try_again_later"
    )
    
    assert result["status"] == "blacklisted_temporary"
    assert "expires_at" in result
    
    # Verify temporarily blacklisted
    status = manager.is_blacklisted("temp@curator.local")
    assert status["is_blacklisted"] is True
    assert status["blacklist_type"] == "temporary"


def test_remove_from_blacklist():
    """Test removing curator from blacklist"""
    manager = BlacklistManagerStub()
    
    # Add to blacklist
    manager.add_to_permanent_blacklist("remove@test.local")
    
    # Verify blacklisted
    assert manager.is_blacklisted("remove@test.local")["is_blacklisted"] is True
    
    # Remove
    result = manager.remove_from_blacklist("remove@test.local", blacklist_type="permanent")
    
    assert result["status"] == "removed"
    assert "permanent" in result["removed_from"]
    
    # Verify no longer blacklisted
    assert manager.is_blacklisted("remove@test.local")["is_blacklisted"] is False


def test_blacklist_stats():
    """Test blacklist statistics"""
    manager = BlacklistManagerStub()
    
    # Add various blacklists
    manager.add_to_permanent_blacklist("perm1@test.local")
    manager.add_to_permanent_blacklist("perm2@test.local")
    manager.add_to_temporary_blacklist("temp1@test.local", days=30)
    manager.add_to_project_blacklist("proj1@test.local", "project_1")
    
    stats = manager.get_blacklist_stats()
    
    assert stats["permanent_blacklist_count"] == 2
    assert stats["temporary_blacklist_count"] == 1
    assert stats["project_blacklist_count"] >= 1
    assert stats["total_blacklisted"] >= 4
