"""
Tests for ACL (Access Control List) System

Phase 1: STUB mode tests
"""
import pytest

from app.core.acl import (
    ACLChecker,
    Role,
    Resource,
    Permission,
    check_permission,
    require_permission
)


@pytest.fixture
def acl_checker():
    """Create ACL checker instance"""
    return ACLChecker(mode="STUB")


def test_acl_initialization(acl_checker):
    """Test ACL checker initializes correctly"""
    assert acl_checker.mode == "STUB"
    assert len(acl_checker.matrix) > 0


def test_orchestrator_permissions(acl_checker):
    """Test orchestrator role permissions"""
    # Should have read/write on campaign_history
    allowed, perm, reason = acl_checker.check_permission(
        "orchestrator", "campaign_history", "r"
    )
    assert allowed is True
    assert perm == "r/w"
    
    allowed, perm, reason = acl_checker.check_permission(
        "orchestrator", "campaign_history", "w"
    )
    assert allowed is True
    assert perm == "r/w"
    
    # Should have NO access to backups
    allowed, perm, reason = acl_checker.check_permission(
        "orchestrator", "backups", "r"
    )
    assert allowed is False
    assert perm == "-"
    assert "no access" in reason.lower()


def test_worker_permissions(acl_checker):
    """Test worker role permissions"""
    # Should have read/write on ml_features
    allowed, perm, reason = acl_checker.check_permission(
        "worker", "ml_features", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "worker", "ml_features", "w"
    )
    assert allowed is True
    
    # Should have read-only on campaign_history
    allowed, perm, reason = acl_checker.check_permission(
        "worker", "campaign_history", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "worker", "campaign_history", "w"
    )
    assert allowed is False
    assert "does not have write permission" in reason.lower()


def test_auditor_permissions(acl_checker):
    """Test auditor role permissions"""
    # Should have read/write on audits
    allowed, perm, reason = acl_checker.check_permission(
        "auditor", "audits", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "auditor", "audits", "w"
    )
    assert allowed is True
    
    # Should have read-only on campaign_history
    allowed, perm, reason = acl_checker.check_permission(
        "auditor", "campaign_history", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "auditor", "campaign_history", "w"
    )
    assert allowed is False


def test_dashboard_permissions(acl_checker):
    """Test dashboard role permissions"""
    # Should have read-only on most resources
    allowed, perm, reason = acl_checker.check_permission(
        "dashboard", "campaign_history", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "dashboard", "campaign_history", "w"
    )
    assert allowed is False
    
    # Should have NO access to audits
    allowed, perm, reason = acl_checker.check_permission(
        "dashboard", "audits", "r"
    )
    assert allowed is False


def test_devops_permissions(acl_checker):
    """Test devops role permissions"""
    # Should have full access to backups
    allowed, perm, reason = acl_checker.check_permission(
        "devops", "backups", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "devops", "backups", "w"
    )
    assert allowed is True
    
    # Should have full access to config
    allowed, perm, reason = acl_checker.check_permission(
        "devops", "config", "r"
    )
    assert allowed is True
    
    allowed, perm, reason = acl_checker.check_permission(
        "devops", "config", "w"
    )
    assert allowed is True


def test_invalid_role(acl_checker):
    """Test handling of invalid role"""
    allowed, perm, reason = acl_checker.check_permission(
        "invalid_role", "campaign_history", "r"
    )
    assert allowed is False
    assert "invalid" in reason.lower()


def test_invalid_resource(acl_checker):
    """Test handling of invalid resource"""
    allowed, perm, reason = acl_checker.check_permission(
        "orchestrator", "invalid_resource", "r"
    )
    assert allowed is False
    assert "invalid" in reason.lower()


def test_invalid_action(acl_checker):
    """Test handling of invalid action"""
    allowed, perm, reason = acl_checker.check_permission(
        "orchestrator", "campaign_history", "x"  # Invalid action
    )
    assert allowed is False
    assert "invalid action" in reason.lower()


def test_get_role_permissions(acl_checker):
    """Test getting all permissions for a role"""
    perms = acl_checker.get_role_permissions("orchestrator")
    assert len(perms) > 0
    assert "campaign_history" in perms
    assert perms["campaign_history"] == "r/w"


def test_get_resource_access(acl_checker):
    """Test getting which roles can access a resource"""
    access = acl_checker.get_resource_access("ml_features")
    assert len(access) > 0
    assert "orchestrator" in access
    assert "worker" in access
    assert access["orchestrator"] == "r/w"
    assert access["worker"] == "r/w"


def test_require_permission_success():
    """Test require_permission helper function (success)"""
    # Should not raise exception
    result = require_permission("orchestrator", "campaign_history", "r")
    assert result is True


def test_require_permission_failure():
    """Test require_permission helper function (failure)"""
    # Should raise PermissionError
    with pytest.raises(PermissionError):
        require_permission("worker", "backups", "r")


def test_check_permission_convenience_function():
    """Test check_permission convenience function"""
    allowed, perm, reason = check_permission("orchestrator", "ml_features", "w")
    assert allowed is True
    assert perm == "r/w"
