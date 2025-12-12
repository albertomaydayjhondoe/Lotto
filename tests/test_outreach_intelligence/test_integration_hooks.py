"""
Tests for Integration Hooks subsystem
"""

import pytest
from backend.app.outreach_intelligence.integration import (
    MusicEngineHook,
    ContentEngineHook,
    CommunityManagerHook,
    MasterOrchestratorHook
)


def test_music_engine_get_track_analysis():
    """Test getting track analysis from Phase 2"""
    hook = MusicEngineHook()
    
    analysis = hook.get_track_analysis("track_001")
    
    assert analysis["track_id"] == "track_001"
    assert "a_and_r_score" in analysis
    assert "production_quality" in analysis
    assert analysis["stub"] is True


def test_music_engine_share_results():
    """Test sharing outreach results back to Phase 2"""
    hook = MusicEngineHook()
    
    result = hook.share_outreach_results(
        "track_001",
        {"playlist_adds": 25, "response_rate": 0.30}
    )
    
    assert result["received"] is True
    assert result["learning_updated"] is True


def test_content_engine_placeholder():
    """Test Content Engine hook placeholder (future)"""
    hook = ContentEngineHook()
    
    result = hook.request_social_content("track_001", "release")
    
    assert result["content_available"] is False
    assert "not yet implemented" in result["note"].lower()


def test_community_manager_placeholder():
    """Test Community Manager hook placeholder (future)"""
    hook = CommunityManagerHook()
    
    result = hook.notify_community_of_release(
        "track_001",
        {"title": "New Release"}
    )
    
    assert result["notified"] is False
    assert "not yet implemented" in result["note"].lower()


def test_master_orchestrator_report_status():
    """Test reporting campaign status to Brain"""
    hook = MasterOrchestratorHook()
    
    result = hook.report_campaign_status(
        "campaign_001",
        {"emails_sent": 50, "responses": 12}
    )
    
    assert result["status_received"] is True
    assert "next_actions" in result


def test_master_orchestrator_budget_request():
    """Test requesting budget allocation"""
    hook = MasterOrchestratorHook()
    
    result = hook.request_budget_allocation(
        campaign_id="campaign_001",
        requested_amount=1500.00,
        justification="High-quality opportunities"
    )
    
    assert result["approved"] is True
    assert result["allocated_amount"] == 1500.00


def test_master_orchestrator_strategic_consultation():
    """Test consulting Brain for decisions"""
    hook = MasterOrchestratorHook()
    
    decision = hook.consult_strategic_decision(
        "campaign_launch",
        {"hit_score": 85, "opportunities": 50}
    )
    
    assert "recommendation" in decision
    assert "confidence" in decision
    assert "reasoning" in decision


def test_master_orchestrator_learning_feedback():
    """Test sharing learning feedback"""
    hook = MasterOrchestratorHook()
    
    result = hook.register_learning_feedback({
        "campaign_id": "campaign_001",
        "success_rate": 0.32,
        "insights": ["Genre performed well"]
    })
    
    assert result["results_received"] is True
    assert result["learning_models_updated"] is True
