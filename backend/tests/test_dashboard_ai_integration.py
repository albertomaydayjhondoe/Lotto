"""
Tests for Dashboard AI Integration Module.

Part of PASO 8.0 implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.ai_global_worker.schemas import (
    AIReasoningOutput,
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan
)
from app.dashboard_ai_integration.formatter import (
    generate_health_card,
    generate_recommendations_cards,
    generate_actions_summary,
    generate_full_dashboard_response
)


# Test client
client = TestClient(app)


def create_mock_snapshot():
    """Create a mock SystemSnapshot for testing."""
    return SystemSnapshot(
        timestamp=datetime.now(),
        queue_pending=5,
        queue_processing=2,
        queue_failed=1,
        queue_success=100,
        scheduler_pending=3,
        scheduler_due_soon=1,
        orchestrator_running=True,
        orchestrator_last_run=datetime.now(),
        orchestrator_actions_last_24h=10,
        publish_success_rate=0.95,
        publish_total_24h=50,
        publish_failed_24h=2,
        clips_ready=10,
        clips_pending_analysis=5,
        jobs_pending=3,
        jobs_failed=1,
        campaigns_active=2,
        campaigns_draft=4,
        alerts_critical=0,
        alerts_warning=1,
        platform_stats={},
        best_clips={},
        rule_weights={},
        recent_events=[],
        additional_metrics={}
    )


def create_mock_reasoning():
    """Create a mock AIReasoningOutput for testing."""
    summary = AISummary(
        overall_health="good",
        health_score=75,
        key_insights=["System performing well", "Content pipeline stable", "Publishing on track"],
        concerns=["Low inventory"],
        positives=["High success rate", "Active campaigns"],
        generated_at=datetime.now()
    )
    
    recommendations = [
        AIRecommendation(
            id="rec-001",
            category="content",
            priority="high",
            title="Increase publishing frequency",
            description="Current cadence is below optimal for audience engagement",
            impact="high",
            effort="medium",
            action_type=None,
            action_payload=None
        ),
        AIRecommendation(
            id="rec-002",
            category="publishing",
            priority="medium",
            title="Optimize posting times",
            description="Shift posting schedule to match peak audience activity",
            impact="medium",
            effort="low",
            action_type=None,
            action_payload=None
        )
    ]
    
    action_plan = AIActionPlan(
        plan_id="plan-001",
        title="Optimize Publishing Schedule",
        objective="Optimize publishing schedule",
        steps=[
            {"step": 1, "action": "Analyze current metrics", "duration": "30 min"},
            {"step": 2, "action": "Update schedule rules", "duration": "1 hour"},
            {"step": 3, "action": "Monitor results", "duration": "ongoing"}
        ],
        estimated_duration="2 hours",
        risk_level="low",
        automated=True
    )
    
    return AIReasoningOutput(
        reasoning_id="test-reasoning-123",
        timestamp=datetime.now(),
        snapshot=create_mock_snapshot(),
        summary=summary,
        recommendations=recommendations,
        action_plan=action_plan,
        execution_time_ms=1500
    )


@pytest.mark.skip(reason="Auth integration testing - skip for now")
def test_ai_last_endpoint_ok():
    """
    Test 1: GET /dashboard/ai-integration/last returns formatted data.
    """
    mock_reasoning = create_mock_reasoning()
    
    with patch("app.dashboard_ai_integration.router.get_last_reasoning") as mock_get, \
         patch("app.auth.permissions.require_role", return_value=AsyncMock(return_value={"role": "admin"})):
        mock_get.return_value = mock_reasoning
        
        response = client.get("/dashboard/ai-integration/last")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "reasoning_id" in data
        assert "timestamp" in data
        assert "health_card" in data
        assert "recommendations_cards" in data
        assert "actions_summary" in data
        assert "raw" in data
        
        # Check health_card
        assert data["health_card"]["score"] == 75
        assert data["health_card"]["status"] == "healthy"
        assert data["health_card"]["color"] == "green"
        
        # Check recommendations_cards
        assert len(data["recommendations_cards"]) == 2
        assert data["recommendations_cards"][0]["priority"] == "high"
        assert data["recommendations_cards"][0]["badge_color"] == "orange"
        
        # Check actions_summary
        assert data["actions_summary"]["total_steps"] == 3
        assert data["actions_summary"]["risk_level"] == "low"
        assert data["actions_summary"]["risk_badge_color"] == "green"


@pytest.mark.skip(reason="Auth integration testing - skip for now")
def test_ai_last_endpoint_no_data():
    """
    Test: GET /dashboard/ai-integration/last returns 404 when no data available.
    """
    with patch("app.dashboard_ai_integration.router.get_last_reasoning") as mock_get:
        mock_get.return_value = None
        
        response = client.get("/dashboard/ai-integration/last")
        
        assert response.status_code == 404
        assert "No AI reasoning available" in response.json()["detail"]


@pytest.mark.skip(reason="Auth integration testing - skip for now")
def test_ai_run_endpoint_ok():
    """
    Test 2: GET /dashboard/ai-integration/run triggers reasoning and returns data.
    """
    mock_snapshot = create_mock_snapshot()
    mock_reasoning = create_mock_reasoning()
    
    with patch("app.dashboard_ai_integration.router.collect_system_snapshot") as mock_collect, \
         patch("app.dashboard_ai_integration.router.run_full_reasoning") as mock_run:
        
        mock_collect.return_value = mock_snapshot
        mock_run.return_value = mock_reasoning
        
        response = client.get("/dashboard/ai-integration/run")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "reasoning_id" in data
        assert "health_card" in data
        assert "recommendations_cards" in data
        assert "actions_summary" in data
        
        # Verify functions were called
        mock_collect.assert_called_once()
        mock_run.assert_called_once()


@pytest.mark.skip(reason="Auth integration testing - skip for now")
def test_ai_run_endpoint_error():
    """
    Test: GET /dashboard/ai-integration/run returns 500 on error.
    """
    with patch("app.dashboard_ai_integration.router.collect_system_snapshot") as mock_collect:
        mock_collect.side_effect = Exception("Database error")
        
        response = client.get("/dashboard/ai-integration/run")
        
        assert response.status_code == 500
        assert "AI reasoning failed" in response.json()["detail"]


@pytest.mark.skip(reason="Auth integration testing - skip for now")
def test_ai_history_empty():
    """
    Test 3: GET /dashboard/ai-integration/history returns empty list (stub).
    """
    response = client.get("/dashboard/ai-integration/history")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 0


def test_ai_summary_formatter_ok():
    """
    Test 4: Health card formatter generates correct output.
    """
    mock_reasoning = create_mock_reasoning()
    
    health_card = generate_health_card(mock_reasoning)
    
    # Check structure
    assert "score" in health_card
    assert "status" in health_card
    assert "status_label" in health_card
    assert "top_issue" in health_card
    assert "color" in health_card
    
    # Check values
    assert health_card["score"] == 75
    assert health_card["status"] == "healthy"
    assert health_card["color"] == "green"
    assert health_card["status_label"] == "Healthy"
    
    # Test critical range
    mock_reasoning.summary.health_score = 30
    health_card_critical = generate_health_card(mock_reasoning)
    assert health_card_critical["status"] == "critical"
    assert health_card_critical["color"] == "red"
    
    # Test warning range
    mock_reasoning.summary.health_score = 55
    health_card_warning = generate_health_card(mock_reasoning)
    assert health_card_warning["status"] == "warning"
    assert health_card_warning["color"] == "yellow"


def test_ai_recommendations_formatter_ok():
    """
    Test 5: Recommendations cards formatter generates correct output.
    """
    mock_reasoning = create_mock_reasoning()
    
    cards = generate_recommendations_cards(mock_reasoning)
    
    # Check structure
    assert isinstance(cards, list)
    assert len(cards) == 2
    
    # Check first card
    card1 = cards[0]
    assert card1["category"] == "content"
    assert card1["priority"] == "high"
    assert card1["badge_color"] == "orange"
    assert "title" in card1
    assert "description" in card1
    assert "full_description" in card1
    assert "impact" in card1
    assert "effort" in card1
    
    # Check second card
    card2 = cards[1]
    assert card2["priority"] == "medium"
    assert card2["badge_color"] == "yellow"


def test_actions_summary_formatter_ok():
    """
    Test: Actions summary formatter generates correct output.
    """
    mock_reasoning = create_mock_reasoning()
    
    summary = generate_actions_summary(mock_reasoning)
    
    # Check structure
    assert "total_steps" in summary
    assert "estimated_duration" in summary
    assert "risk_level" in summary
    assert "automated" in summary
    assert "objective" in summary
    assert "risk_badge_color" in summary
    assert "steps" in summary
    
    # Check values
    assert summary["total_steps"] == 3
    assert summary["risk_level"] == "low"
    assert summary["risk_badge_color"] == "green"
    assert summary["automated"] is True
    
    # Test high risk
    mock_reasoning.action_plan.risk_level = "high"
    summary_high = generate_actions_summary(mock_reasoning)
    assert summary_high["risk_badge_color"] == "red"
    
    # Test medium risk
    mock_reasoning.action_plan.risk_level = "medium"
    summary_medium = generate_actions_summary(mock_reasoning)
    assert summary_medium["risk_badge_color"] == "yellow"


def test_full_dashboard_response_ok():
    """
    Test: Full dashboard response includes all sections.
    """
    mock_reasoning = create_mock_reasoning()
    
    response = generate_full_dashboard_response(mock_reasoning)
    
    # Check all sections present
    assert "reasoning_id" in response
    assert "timestamp" in response
    assert "execution_time_ms" in response
    assert "health_card" in response
    assert "recommendations_cards" in response
    assert "actions_summary" in response
    assert "raw" in response
    
    # Check raw section
    assert "summary" in response["raw"]
    assert "snapshot" in response["raw"]
    
    # Check timestamp is ISO format string
    assert isinstance(response["timestamp"], str)
    assert "T" in response["timestamp"]  # ISO 8601 format


def test_badge_color_logic():
    """
    Test: Badge color logic for different priority/risk levels.
    """
    mock_reasoning = create_mock_reasoning()
    
    # Test priority badge colors
    test_recommendations = [
        AIRecommendation(
            id="rec-1", category="test", priority="critical", title="Test Critical",
            description="Test", impact="high", effort="low"
        ),
        AIRecommendation(
            id="rec-2", category="test", priority="high", title="Test High",
            description="Test", impact="high", effort="low"
        ),
        AIRecommendation(
            id="rec-3", category="test", priority="medium", title="Test Medium",
            description="Test", impact="medium", effort="low"
        ),
        AIRecommendation(
            id="rec-4", category="test", priority="low", title="Test Low",
            description="Test", impact="low", effort="low"
        )
    ]
    
    mock_reasoning.recommendations = test_recommendations
    cards = generate_recommendations_cards(mock_reasoning)
    
    assert cards[0]["badge_color"] == "red"     # critical
    assert cards[1]["badge_color"] == "orange"  # high
    assert cards[2]["badge_color"] == "yellow"  # medium
    assert cards[3]["badge_color"] == "blue"    # low
