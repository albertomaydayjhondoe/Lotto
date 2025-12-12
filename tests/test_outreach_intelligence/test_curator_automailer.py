"""
Tests for Curator AutoMailer subsystem
"""

import pytest
from backend.app.outreach_intelligence.curator_automailer import (
    EmailTemplateBuilder,
    AutoSenderStub,
    FollowUpSchedulerStub,
    InboxMonitorStub,
    ResponseType
)


def test_email_template_initial_pitch(sample_track_metadata, sample_opportunity):
    """Test initial pitch email generation"""
    builder = EmailTemplateBuilder()
    
    email = builder.build_initial_pitch(
        curator_info={"email": sample_opportunity["curator_email"], "name": sample_opportunity["curator_name"], "playlist_name": sample_opportunity["name"]},
        track_info=sample_track_metadata,
        artist_info={"name": "Test Artist", "email": "artist@test.com"},
        reasoning="Perfect fit for your playlist style"
    )
    
    assert email["type"] == "initial_pitch"
    assert email["to"] == sample_opportunity["curator_email"]
    assert email["auto_send"] is True
    assert sample_track_metadata["title"] in email["subject"]


def test_auto_sender_rate_limiting():
    """Test email rate limiting"""
    sender = AutoSenderStub()
    
    # Send email within limits
    result = sender.send_email({
        "to": "test@curator.local",
        "subject": "Test",
        "body": "Test body"
    })
    
    assert result["status"].value == "sent"
    assert "email_id" in result

