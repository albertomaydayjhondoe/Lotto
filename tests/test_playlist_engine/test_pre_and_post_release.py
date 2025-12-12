"""
Tests for Playlist Intelligence — Pre-Release & Post-Release Engines
"""

import pytest
from backend.app.playlist_engine.playlist_intelligence import (
    PreReleaseEngine,
    PostReleaseEngine,
    PlaylistAnalyzerStub
)


def test_pre_release_strategy_creation():
    """Test pre-release strategy generation"""
    engine = PreReleaseEngine()
    
    strategy = engine.create_pre_release_strategy(
        track_metadata={
            "track_id": "test_001",
            "artist": "Test Artist",
            "title": "Test Track",
            "genre": "Deep House",
            "bpm": 124,
            "mood": "Chill",
            "a_and_r_score": 8.0
        },
        release_date="2025-02-01T00:00:00Z"
    )
    
    assert strategy["status"] == "pre_release"
    assert strategy["track_id"] == "test_001"
    assert "phases" in strategy
    assert "unreleased_opportunities" in strategy
    assert isinstance(strategy["unreleased_opportunities"], int)
    assert strategy["unreleased_opportunities"] > 0


def test_post_release_strategy_creation():
    """Test post-release strategy generation"""
    engine = PostReleaseEngine()
    
    strategy = engine.create_post_release_strategy(
        track_metadata={
            "track_id": "test_002",
            "genre": "Tech House",
            "bpm": 128,
            "mood": "Energetic"
        },
        spotify_url="https://open.spotify.com/track/test_002"
    )
    
    assert strategy["status"] == "post_release"
    assert "spotify_url" in strategy
    assert "campaign_tiers" in strategy
    assert "tier_1_premium" in strategy["campaign_tiers"]
    assert "tier_2_core" in strategy["campaign_tiers"]
    assert "tier_3_volume" in strategy["campaign_tiers"]


def test_unreleased_playlists_filtering():
    """Test filtering for unreleased-accepting playlists"""
    engine = PreReleaseEngine()
    
    # Test without genre filter - should return some unreleased-accepting playlists
    unreleased_playlists = engine.get_unreleased_playlists_only()
    
    assert isinstance(unreleased_playlists, list)
    # Database has ~1/3 of medium playlists accepting unreleased (~33)
    assert len(unreleased_playlists) >= 30
    
    # Verify all accept unreleased
    for playlist in unreleased_playlists:
        assert "curator_email" in playlist
        assert "name" in playlist


def test_post_release_performance_tracking():
    """Test performance tracking (STUB)"""
    engine = PostReleaseEngine()
    
    performance = engine.track_playlist_performance(
        track_id="test_003",
        playlist_ids=["playlist_001", "playlist_002", "playlist_003"]
    )
    
    assert performance["track_id"] == "test_003"
    assert "metrics" in performance
    assert "stub_note" in performance
    # Verify it's a stub response
    assert "STUB MODE" in performance["stub_note"]
