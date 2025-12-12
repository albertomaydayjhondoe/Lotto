"""
Tests for Integration Hooks
"""

import pytest
from backend.app.playlist_engine.integration_hooks import (
    MusicEngineHook,
    BrainOrchestratorHook,
    AdIntegrationsHook
)


def test_music_engine_hook_receive_analysis():
    """Test receiving track analysis from Music Engine"""
    hook = MusicEngineHook()
    
    result = hook.receive_track_analysis(
        track_id="track_001",
        a_and_r_analysis={"score": 8.5, "tier": "premium"}
    )
    
    assert result["status"] == "received"
    assert result["track_id"] == "track_001"
    assert result["a_and_r_score"] == 8.5
    assert "recommended_actions" in result


def test_music_engine_hook_request_recommendations():
    """Test requesting playlist recommendations"""
    hook = MusicEngineHook()
    
    result = hook.request_playlist_recommendations(
        track_metadata={"track_id": "track_002", "genre": "Deep House"}
    )
    
    assert "recommended_playlists" in result
    assert isinstance(result["recommended_playlists"], int)
    assert result["recommended_playlists"] > 0


def test_brain_hook_report_campaign():
    """Test reporting campaign results to Brain"""
    hook = BrainOrchestratorHook()
    
    result = hook.report_campaign_results(
        campaign_id="campaign_001",
        results={"emails_sent": 100, "acceptances": 30}
    )
    
    assert result["status"] == "received_by_brain"
    assert result["campaign_id"] == "campaign_001"
    assert result["insights_generated"] is True


def test_brain_hook_curator_prioritization():
    """Test requesting curator prioritization from Brain"""
    hook = BrainOrchestratorHook()
    
    result = hook.request_curator_prioritization(
        track_metadata={"genre": "Tech House"},
        curator_list=["curator1@test.local", "curator2@test.local"]
    )
    
    assert result["status"] == "prioritized"
    assert "top_curators" in result
    assert len(result["top_curators"]) > 0


def test_ad_hook_suggest_campaign():
    """Test suggesting ad campaign from playlist success"""
    hook = AdIntegrationsHook()
    
    result = hook.suggest_ad_campaign_from_playlists(
        track_id="track_003",
        successful_playlists=[
            {"name": "Playlist 1", "size": 50000},
            {"name": "Playlist 2", "size": 75000}
        ]
    )
    
    assert result["status"] == "suggestions_generated"
    assert "recommended_platforms" in result
    assert isinstance(result["recommended_platforms"], list)
    assert len(result["recommended_platforms"]) > 0


def test_ad_hook_cross_promotion():
    """Test cross-promotion request"""
    hook = AdIntegrationsHook()
    
    result = hook.request_cross_promotion(
        track_id="track_004",
        playlist_ids=["playlist_1", "playlist_2", "playlist_3"]
    )
    
    assert result["status"] == "cross_promotion_planned"
    assert result["track_id"] == "track_004"
    assert result["playlists_included"] == 3
