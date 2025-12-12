"""
Tests for Curator AutoMailer — Email Building & Sending
"""

import pytest
from backend.app.playlist_engine.curator_automailer import (
    EmailBuilderStub,
    EmailSenderStub
)


def test_email_builder_pre_release():
    """Test pre-release email generation"""
    builder = EmailBuilderStub()
    
    email = builder.build_pre_release_email(
        curator_name="Test Curator",
        playlist_name="Test Playlist",
        track_info={
            "artist": "Test Artist",
            "title": "Test Track",
            "genre": "Deep House",
            "mood": "Chill",
            "release_date": "2025-02-01"
        }
    )
    
    assert "subject" in email
    assert "body" in email
    assert "email_type" in email
    assert email["email_type"] == "pre_release_pitch"
    assert "Test Artist" in email["body"]
    assert "Test Track" in email["body"]


def test_email_builder_post_release():
    """Test post-release email generation"""
    builder = EmailBuilderStub()
    
    email = builder.build_post_release_email(
        curator_name="Test Curator",
        playlist_name="Test Playlist",
        track_info={
            "artist": "Test Artist",
            "title": "Test Track",
            "genre": "Tech House",
            "bpm": 128
        },
        spotify_url="https://open.spotify.com/track/test",
        compatibility_score=0.85
    )
    
    assert "subject" in email
    assert "body" in email
    assert email["email_type"] == "post_release_pitch"
    assert "spotify.com" in email["body"]


def test_email_sender_stub():
    """Test STUB email sending"""
    sender = EmailSenderStub()
    
    result = sender.send_email(
        to_email="test.curator@stub.local",
        subject="Test Subject",
        body="Test Body"
    )
    
    assert result["success"] is True
    assert result["status"] == "sent_stub"
    assert "email_id" in result
    assert result["email_id"] is not None


def test_email_batch_sending():
    """Test batch email sending"""
    sender = EmailSenderStub()
    
    emails = [
        {
            "to": "curator1@stub.local",
            "subject": "Test 1",
            "body": "Body 1"
        },
        {
            "to": "curator2@stub.local",
            "subject": "Test 2",
            "body": "Body 2"
        }
    ]
    
    result = sender.send_batch(emails)
    
    assert result["success"] is True
    assert result["total_sent"] == 2
    assert len(result["results"]) == 2
