"""
Tests for Integration Layer
"""

import pytest
from backend.app.outreach_intelligence.integration import (
    MusicEngineHook,
    ContentEngineHook,
    CommunityManagerHook,
    MasterOrchestratorHook
)


def test_music_engine_hook_get_analysis():
    """Test Music Engine integration - get track analysis"""
    hook = MusicEngineHook()
    
    analysis = hook.get_track_analysis("test_track_001")
    
    assert analysis["track_id"] == "test_track_001"
    assert "a_and_r_score" in analysis
    assert analysis["stub"] is True


def test_music_engine_hook_share_results():
    """Test sharing outreach results to Music Engine"""
    hook = MusicEngineHook()
    
    result = hook.share_outreach_results(
        track_id="test_track_001",
        results={"playlist_adds": 15, "response_rate": 0.23}
    )
    
    assert result["received"] is True
    assert result["learning_updated"] is True


def test_content_engine_hook_placeholder():
    """Test Content Engine placeholder (future)"""
    hook = ContentEngineHook()
    
    content = hook.request_social_content("test_track_001", "release_campaign")
    
    assert content["content_available"] is False
    assert "not yet implemented" in content["note"].lower()