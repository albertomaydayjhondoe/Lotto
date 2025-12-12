"""
Test configuration for Playlist Engine tests
"""

import pytest


@pytest.fixture
def sample_track_metadata():
    """Sample track metadata for testing"""
    return {
        "track_id": "test_track_001",
        "artist": "Test Artist",
        "title": "Test Track",
        "genre": "Deep House",
        "subgenre": "Organic House",
        "bpm": 124,
        "key": "Am",
        "mood": "Chill",
        "energy": 0.75,
        "a_and_r_score": 8.0,
        "production_quality": 0.85
    }


@pytest.fixture
def sample_curator_data():
    """Sample curator data for testing"""
    return {
        "curator_id": "test_curator_001",
        "name": "Test Curator",
        "email": "test.curator@stub.local",
        "playlists": ["Test Playlist 1", "Test Playlist 2"],
        "total_followers": 50000,
        "accepts_unreleased": True,
        "language": "en",
        "timezone": "America/Los_Angeles",
        "response_rate": 0.65,
        "specialties": ["Deep House", "Tech House"]
    }
