"""
Tests for Meta Ads Orchestrator (Simplified)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.meta_ads_orchestrator.orchestrator import MetaAdsOrchestrator
from app.meta_ads_orchestrator.models import OrchestrationRequest


# ============================================================================
# Tests
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_validate_clip_fails_if_not_found():
    """Test that validation raises ValueError for missing clip."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    
    orchestrator = MetaAdsOrchestrator(mock_db)
    
    with pytest.raises(ValueError, match="Clip .* not found"):
        await orchestrator._validate_clip(uuid4())


@pytest.mark.asyncio
async def test_orchestrator_has_action_queue():
    """Test that orchestrator has action queue methods."""
    mock_db = AsyncMock()
    orchestrator = MetaAdsOrchestrator(mock_db)
    
    # Test queue methods exist
    orchestrator.add_action_to_queue({"type": "test"})
    assert len(orchestrator.action_queue) == 1
    
    result = await orchestrator.process_action_queue()
    assert result["total"] == 1
    assert result["processed"] == 1


@pytest.mark.asyncio
async def test_orchestration_request_model():
    """Test OrchestrationRequest model validation."""
    request = OrchestrationRequest(
        social_account_id=uuid4(),
        clip_id=uuid4(),
        campaign_name="Test Campaign",
        campaign_objective="OUTCOME_SALES",
        daily_budget_cents=10000,
        creative_title="Test Creative",
        creative_description="Test description",
        landing_url="https://example.com",
        targeting={"age_min": 18, "age_max": 65},
        optimization_goal="LINK_CLICKS",
        auto_publish=False,
    )
    
    assert request.campaign_name == "Test Campaign"
    assert request.daily_budget_cents == 10000
    assert request.auto_publish == False


@pytest.mark.asyncio
async def test_orchestrator_instantiation():
    """Test that orchestrator can be instantiated."""
    mock_db = AsyncMock()
    orchestrator = MetaAdsOrchestrator(mock_db)
    
    assert orchestrator.db == mock_db
    assert orchestrator.action_queue == []
    assert orchestrator.max_retries == 3


@pytest.mark.asyncio
async def test_orchestrate_campaign_returns_result():
    """Test that orchestrate_campaign returns OrchestrationResult."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    ))
    
    orchestrator = MetaAdsOrchestrator(mock_db)
    
    request = OrchestrationRequest(
        social_account_id=uuid4(),
        clip_id=uuid4(),
        campaign_name="Test",
        campaign_objective="OUTCOME_SALES",
        daily_budget_cents=5000,
        creative_title="Title",
        creative_description="Desc",
        landing_url="https://example.com",
        targeting={"age_min": 18},
        optimization_goal="LINK_CLICKS",
        auto_publish=False,
    )
    
    # Should fail because clip doesn't exist
    result = await orchestrator.orchestrate_campaign(request)
    
    assert result.overall_success == False
    assert "not found" in str(result.errors)
    assert result.request_id is not None
    assert isinstance(result.started_at, datetime)


@pytest.mark.asyncio
async def test_orchestrator_respects_budget():
    """Test that budget parameter is respected."""
    request = OrchestrationRequest(
        social_account_id=uuid4(),
        clip_id=uuid4(),
        campaign_name="Budget Test",
        campaign_objective="OUTCOME_SALES",
        daily_budget_cents=15000,  # $150
        creative_title="Title",
        creative_description="Desc",
        landing_url="https://example.com",
        targeting={"age_min": 18},
        optimization_goal="LINK_CLICKS",
        auto_publish=False,
    )
    
    assert request.daily_budget_cents == 15000
    # This validates that the Pydantic model accepts and stores the budget
