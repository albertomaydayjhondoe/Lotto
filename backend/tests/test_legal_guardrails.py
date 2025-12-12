"""
Tests for Legal Guardrails System

Phase 1: STUB mode tests
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.legal.guardrails import (
    LegalGuardrails,
    CopyrightConfirmation,
    require_copyright_approval
)


@pytest.fixture
def legal_guardrails():
    """Create legal guardrails instance"""
    return LegalGuardrails(mode="STUB")


def test_legal_guardrails_initialization(legal_guardrails):
    """Test legal guardrails initializes correctly"""
    assert legal_guardrails.mode == "STUB"
    assert len(legal_guardrails.approval_logs) == 0


def test_get_disclaimer(legal_guardrails):
    """Test getting disclaimer text"""
    disclaimer = legal_guardrails.get_disclaimer()
    
    assert len(disclaimer) > 0
    assert "AVISO LEGAL" in disclaimer
    assert "copyright" in disclaimer.lower()
    assert "responsabilidad" in disclaimer.lower()


def test_validate_confirmation_success(legal_guardrails):
    """Test validating valid confirmation"""
    confirmation = CopyrightConfirmation(
        user_id=uuid4(),
        copyright_confirmed=True,
        legal_disclaimer_accepted=True,
        content_description="Test video content",
        rights_type="owned"
    )
    
    valid, error = legal_guardrails.validate_confirmation(confirmation)
    
    assert valid is True
    assert error is None


def test_validate_confirmation_missing_copyright(legal_guardrails):
    """Test validation fails without copyright confirmation"""
    confirmation = CopyrightConfirmation(
        user_id=uuid4(),
        copyright_confirmed=False,  # Not confirmed
        legal_disclaimer_accepted=True
    )
    
    valid, error = legal_guardrails.validate_confirmation(confirmation)
    
    assert valid is False
    assert "copyright confirmation" in error.lower()


def test_validate_confirmation_missing_disclaimer(legal_guardrails):
    """Test validation fails without disclaimer acceptance"""
    confirmation = CopyrightConfirmation(
        user_id=uuid4(),
        copyright_confirmed=True,
        legal_disclaimer_accepted=False  # Not accepted
    )
    
    valid, error = legal_guardrails.validate_confirmation(confirmation)
    
    assert valid is False
    assert "legal disclaimer" in error.lower()


def test_log_approval(legal_guardrails):
    """Test logging approval for audit trail"""
    entity_id = uuid4()
    user_id = uuid4()
    
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True,
        content_description="Marketing video",
        rights_type="licensed"
    )
    
    log = legal_guardrails.log_approval(
        entity_type="campaign",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        metadata={"platform": "instagram"}
    )
    
    assert log.id is not None
    assert log.entity_type == "campaign"
    assert log.entity_id == entity_id
    assert log.user_id == user_id
    assert log.copyright_confirmed is True
    assert log.legal_disclaimer_accepted is True
    assert log.ip_address == "192.168.1.1"
    assert log.approved_at is not None


def test_check_approval_exists(legal_guardrails):
    """Test checking if approval exists"""
    entity_id = uuid4()
    user_id = uuid4()
    
    # Should not exist initially
    exists = legal_guardrails.check_approval_exists("clip", entity_id)
    assert exists is False
    
    # Log approval
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    legal_guardrails.log_approval(
        entity_type="clip",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation
    )
    
    # Should exist now
    exists = legal_guardrails.check_approval_exists("clip", entity_id)
    assert exists is True


def test_require_approval_success(legal_guardrails):
    """Test require_approval passes with valid approval"""
    entity_id = uuid4()
    user_id = uuid4()
    
    # Log approval
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    legal_guardrails.log_approval(
        entity_type="campaign",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation
    )
    
    # Should not raise exception
    result = legal_guardrails.require_approval("campaign", entity_id)
    assert result is True


def test_require_approval_failure(legal_guardrails):
    """Test require_approval raises exception without approval"""
    entity_id = uuid4()
    
    # Should raise PermissionError
    with pytest.raises(PermissionError, match="Legal approval required"):
        legal_guardrails.require_approval("campaign", entity_id)


def test_get_approval_log(legal_guardrails):
    """Test retrieving approval log"""
    entity_id = uuid4()
    user_id = uuid4()
    
    # Log approval
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True,
        rights_type="public_domain"
    )
    
    legal_guardrails.log_approval(
        entity_type="clip",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation
    )
    
    # Retrieve log
    log = legal_guardrails.get_approval_log("clip", entity_id)
    
    assert log is not None
    assert log.entity_id == entity_id
    assert log.rights_type == "public_domain"


def test_get_approval_log_nonexistent(legal_guardrails):
    """Test retrieving non-existent approval log returns None"""
    entity_id = uuid4()
    
    log = legal_guardrails.get_approval_log("campaign", entity_id)
    assert log is None


def test_revoke_approval(legal_guardrails):
    """Test revoking an approval"""
    entity_id = uuid4()
    user_id = uuid4()
    
    # Log approval
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    log = legal_guardrails.log_approval(
        entity_type="clip",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation
    )
    
    # Revoke approval
    revoked = legal_guardrails.revoke_approval(log.id, "Copyright infringement reported")
    assert revoked is True
    
    # Should no longer exist
    exists = legal_guardrails.check_approval_exists("clip", entity_id)
    assert exists is False


def test_revoke_nonexistent_approval(legal_guardrails):
    """Test revoking non-existent approval returns False"""
    fake_id = uuid4()
    
    revoked = legal_guardrails.revoke_approval(fake_id, "Test reason")
    assert revoked is False


def test_require_copyright_approval_helper():
    """Test require_copyright_approval helper function"""
    from app.legal import legal_guardrails as global_instance
    
    entity_id = uuid4()
    user_id = uuid4()
    
    # Log approval
    confirmation = CopyrightConfirmation(
        user_id=user_id,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    global_instance.log_approval(
        entity_type="campaign",
        entity_id=entity_id,
        user_id=user_id,
        confirmation=confirmation
    )
    
    # Should not raise exception
    result = require_copyright_approval("campaign", entity_id)
    assert result is True


def test_multiple_approvals_same_entity(legal_guardrails):
    """Test multiple approvals for same entity (only latest counts)"""
    entity_id = uuid4()
    user1 = uuid4()
    user2 = uuid4()
    
    # First approval
    confirmation1 = CopyrightConfirmation(
        user_id=user1,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    legal_guardrails.log_approval(
        entity_type="clip",
        entity_id=entity_id,
        user_id=user1,
        confirmation=confirmation1
    )
    
    # Second approval
    confirmation2 = CopyrightConfirmation(
        user_id=user2,
        copyright_confirmed=True,
        legal_disclaimer_accepted=True
    )
    
    legal_guardrails.log_approval(
        entity_type="clip",
        entity_id=entity_id,
        user_id=user2,
        confirmation=confirmation2
    )
    
    # Should still pass approval check
    exists = legal_guardrails.check_approval_exists("clip", entity_id)
    assert exists is True
