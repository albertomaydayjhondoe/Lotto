"""
Test configuration for Outreach Intelligence tests
"""

import pytest


@pytest.fixture
def sample_track_metadata():
    """Sample track metadata for testing"""
    return {
        "track_id": "test_track_phase4_001",
        "title": "Test Track",
        "artist": "Test Artist",
        "genre": "Melodic House & Techno",
        "bpm": 124,
        "key": "Am",
        "mood": "atmospheric",
        "release_date": "2025-12-15",
        "spotify_url": "https://open.spotify.com/track/test",
        "production_quality": 0.85,
        "a_and_r_score": 8.2
    }


@pytest.fixture
def sample_opportunity():
    """Sample opportunity for testing"""
    return {
        "playlist_id": "test_playlist_001",
        "platform": "spotify_playlist",
        "name": "Test Playlist",
        "curator_name": "Test Curator",
        "curator_email": "test@curator.local",
        "follower_count": 50000,
        "confidence_score": 0.85,
        "engagement_rate": 0.68
    }
