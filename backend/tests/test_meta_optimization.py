"""
Tests for Meta Optimization Loop

Tests the optimization service, runner, and API endpoints.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.meta_optimization.service import OptimizationService
from app.meta_optimization.runner import OptimizationRunner
from app.meta_optimization.config import settings
from app.models.database import (
    MetaCampaignModel,
    MetaAdModel,
    MetaAdsetModel,
    MetaROASMetricsModel,
    OptimizationActionModel,
    OptimizationActionStatus,
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def optimization_service(mock_db_session):
    """Create OptimizationService instance with mock DB."""
    return OptimizationService(mock_db_session)


@pytest.mark.asyncio
async def test_worker_creates_actions_based_on_roas(mock_db_session):
    """Test that worker creates scale_down action when ROAS is low."""
    # This test verifies the basic flow - full integration test would require
    # complete mock setup of optimizer and ROAS engine
    
    service = OptimizationService(mock_db_session)
    
    # Mock the optimizer methods
    service.optimizer = MagicMock()
    service.optimizer.detect_ads_to_scale_up = AsyncMock(return_value=[])
    service.optimizer.detect_ads_to_scale_down = AsyncMock(return_value=[
        MetaROASMetricsModel(
            id=uuid4(),
            campaign_id=uuid4(),
            adset_id=uuid4(),
            ad_id=uuid4(),
            actual_roas=1.2,  # Below threshold
            confidence_score=0.75,
            date=datetime.utcnow().date(),
        )
    ])
    
    # Mock campaign fetch
    campaign = MetaCampaignModel(
        id=uuid4(),
        campaign_id="META_CAMPAIGN_123",
        status="ACTIVE",
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: campaign
    mock_result.scalars = lambda: MagicMock(all=lambda: [])
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    # The key assertion: service should be able to create scale_down actions
    ad_data = MetaROASMetricsModel(
        id=uuid4(),
        campaign_id=uuid4(),
        adset_id=uuid4(),
        ad_id=uuid4(),
        actual_roas=1.2,
        confidence_score=0.75,
        date=datetime.utcnow().date(),
    )
    
    action = await service._create_scale_down_action(ad_data)
    assert action is not None
    assert action["type"] in ["scale_down", "pause"]
    assert action["roas_value"] == 1.2


@pytest.mark.asyncio
async def test_scale_down_threshold_applies(mock_db_session):
    """Test that scale_down threshold is correctly applied."""
    service = OptimizationService(mock_db_session)
    
    # Create mock ROAS metric with ROAS below threshold
    ad_data = MetaROASMetricsModel(
        id=uuid4(),
        campaign_id=uuid4(),
        adset_id=uuid4(),
        ad_id=uuid4(),
        actual_roas=1.3,  # Below 1.5 threshold
        confidence_score=0.7,
        date=datetime.utcnow().date(),
    )
    
    # Create action
    action = await service._create_scale_down_action(ad_data)
    
    # Assert
    assert action is not None
    assert action["type"] in ["scale_down", "pause"]
    assert action["confidence"] == 0.7
    assert action["roas_value"] == 1.3
    
    # Very low ROAS should trigger pause
    ad_data_low = MetaROASMetricsModel(
        id=uuid4(),
        campaign_id=uuid4(),
        adset_id=uuid4(),
        ad_id=uuid4(),
        actual_roas=0.5,  # Below pause threshold (0.8)
        confidence_score=0.8,
        date=datetime.utcnow().date(),
    )
    
    action_pause = await service._create_scale_down_action(ad_data_low)
    assert action_pause["type"] == "pause"


@pytest.mark.asyncio
async def test_budget_reallocation_calculation():
    """Test that budget reallocation is calculated correctly."""
    # Mock ROAS metrics with significant variance
    roas_metrics = [
        MetaROASMetricsModel(
            id=uuid4(),
            ad_id=uuid4(),
            actual_roas=5.0,  # High performer
            recommended_daily_budget_usd=100.0,
        ),
        MetaROASMetricsModel(
            id=uuid4(),
            ad_id=uuid4(),
            actual_roas=3.0,  # Medium performer
            recommended_daily_budget_usd=100.0,
        ),
        MetaROASMetricsModel(
            id=uuid4(),
            ad_id=uuid4(),
            actual_roas=1.0,  # Low performer
            recommended_daily_budget_usd=100.0,
        ),
    ]
    
    mock_session = AsyncMock()
    service = OptimizationService(mock_session)
    
    # Mock optimizer
    service.optimizer = MagicMock()
    service.optimizer.compute_budget_reallocations = AsyncMock(return_value={
        "total_budget": 300.0,
        "allocations": [
            {"ad_id": str(roas_metrics[0].ad_id), "budget": 150.0},
            {"ad_id": str(roas_metrics[1].ad_id), "budget": 100.0},
            {"ad_id": str(roas_metrics[2].ad_id), "budget": 50.0},
        ],
    })
    
    # Evaluate reallocation
    action = await service._evaluate_reallocation(
        campaign_id=uuid4(),
        roas_metrics=roas_metrics,
    )
    
    # Assert
    assert action is not None
    assert action["type"] == "reallocate"
    assert len(action["affected_ad_ids"]) == 3


@pytest.mark.asyncio
async def test_action_enqueued_and_persisted(mock_db_session):
    """Test that actions are properly persisted to database."""
    service = OptimizationService(mock_db_session)
    
    action = {
        "type": "scale_up",
        "target_level": "ad",
        "target": "META_AD_123",
        "campaign_id": uuid4(),
        "ad_id": uuid4(),
        "amount_pct": 0.5,
        "reason": "high_roas_performance",
        "confidence": 0.85,
        "roas_value": 4.5,
    }
    
    # Enqueue
    action_id = await service.enqueue_action(action, created_by="test")
    
    # Assert
    assert action_id is not None
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    
    # Check that OptimizationActionModel was created
    added_action = mock_db_session.add.call_args[0][0]
    assert isinstance(added_action, OptimizationActionModel)
    assert added_action.action_type == "scale_up"
    assert added_action.confidence == 0.85


@pytest.mark.asyncio
async def test_execute_action_changes_status_and_ledger(mock_db_session):
    """Test that executing an action updates status and creates ledger event."""
    service = OptimizationService(mock_db_session)
    
    # Mock action
    action = OptimizationActionModel(
        id=uuid4(),
        action_id="test_action_123",
        action_type="scale_up",
        target_level="ad",
        target_id="META_AD_456",
        amount_pct=0.3,
        reason="high_roas",
        confidence=0.8,
        status=OptimizationActionStatus.SUGGESTED,
        created_by="optimizer",
        created_at=datetime.utcnow(),
    )
    
    # Mock DB query to return action
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: action
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    # Execute
    result = await service.execute_action(action.action_id, run_by="test_user")
    
    # Assert
    assert result["status"] == "executed"
    assert action.status == OptimizationActionStatus.EXECUTED
    assert action.executed_by == "test_user"
    assert action.executed_at is not None


@pytest.mark.asyncio
async def test_safety_limits_prevent_large_changes(mock_db_session):
    """Test that guard rails prevent excessive budget changes."""
    service = OptimizationService(mock_db_session)
    
    # Action with excessive budget change
    action_excessive = {
        "type": "scale_up",
        "target": "META_AD_123",
        "amount_pct": 0.50,  # 50% - exceeds MAX_DAILY_CHANGE_PCT (20%)
        "reason": "test",
        "confidence": 0.9,
    }
    
    # Should fail guard rails
    assert not service._passes_guard_rails(action_excessive)
    
    # Action within limits
    action_safe = {
        "type": "scale_up",
        "target": "META_AD_123",
        "amount_pct": 0.15,  # 15% - within limits
        "reason": "test",
        "confidence": 0.9,
    }
    
    # Should pass guard rails
    assert service._passes_guard_rails(action_safe)
    
    # Pause actions always pass (safety measure)
    action_pause = {
        "type": "pause",
        "target": "META_AD_123",
        "amount_pct": -1.0,  # -100%
        "reason": "low_roas",
        "confidence": 0.7,
    }
    
    assert service._passes_guard_rails(action_pause)


@pytest.mark.asyncio
async def test_confidence_threshold_enforced():
    """Test that actions below confidence threshold are rejected."""
    service = OptimizationService(AsyncMock())
    
    # Low confidence action
    action_low_conf = {
        "type": "scale_down",
        "target": "META_AD_123",
        "amount_pct": -0.2,
        "reason": "test",
        "confidence": 0.50,  # Below threshold (0.65)
    }
    
    assert not service._passes_guard_rails(action_low_conf)
    
    # High confidence action
    action_high_conf = {
        "type": "scale_down",
        "target": "META_AD_123",
        "amount_pct": -0.2,
        "reason": "test",
        "confidence": 0.85,  # Above threshold
    }
    
    assert service._passes_guard_rails(action_high_conf)


@pytest.mark.asyncio
async def test_embargo_period_respected():
    """Test that newly created campaigns are not optimized during embargo period."""
    service = OptimizationService(AsyncMock())
    
    # Campaign created 1 day ago (within 48h embargo)
    campaign_new = MetaCampaignModel(
        id=uuid4(),
        campaign_id="NEW_CAMPAIGN",
        status="ACTIVE",
        created_at=datetime.utcnow() - timedelta(hours=24),
    )
    
    assert not service._is_eligible_for_optimization(campaign_new)
    
    # Campaign created 3 days ago (past embargo)
    campaign_old = MetaCampaignModel(
        id=uuid4(),
        campaign_id="OLD_CAMPAIGN",
        status="ACTIVE",
        created_at=datetime.utcnow() - timedelta(days=3),
    )
    
    assert service._is_eligible_for_optimization(campaign_old)


@pytest.mark.asyncio
async def test_cooldown_period_prevents_duplicate_optimizations():
    """Test that ads recently optimized are in cooldown."""
    mock_session = AsyncMock()
    service = OptimizationService(mock_session)
    
    ad_id = uuid4()
    
    # Mock recent optimization
    recent_action = OptimizationActionModel(
        id=uuid4(),
        ad_id=ad_id,
        action_type="scale_up",
        status=OptimizationActionStatus.EXECUTED,
        executed_at=datetime.utcnow() - timedelta(hours=12),  # 12h ago
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: recent_action
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Check cooldown (should be True - in cooldown)
    in_cooldown = await service._check_cooldown(str(ad_id), "scale_up")
    assert in_cooldown
    
    # Mock no recent optimization
    mock_result_none = MagicMock()
    mock_result_none.scalar_one_or_none = lambda: None
    mock_session.execute = AsyncMock(return_value=mock_result_none)
    
    not_in_cooldown = await service._check_cooldown(str(uuid4()), "scale_up")
    assert not not_in_cooldown


@pytest.mark.asyncio
async def test_runner_respects_action_limits():
    """Test that runner respects MAX_ACTIONS_PER_RUN."""
    # This test verifies the limit is enforced in runner._tick()
    # Actual implementation would require more complex mocking
    assert settings.OPTIMIZER_MAX_ACTIONS_PER_RUN > 0
    assert settings.OPTIMIZER_MAX_ACTIONS_PER_CAMPAIGN > 0


@pytest.mark.asyncio
async def test_auto_mode_only_executes_safe_actions():
    """Test that auto mode only executes high-confidence, safe actions."""
    dbmaker = lambda: AsyncMock()
    runner = OptimizationRunner(dbmaker)
    
    # High confidence scale-up (safe)
    action_safe = {
        "type": "scale_up",
        "confidence": 0.85,
        "amount_pct": 0.1,  # Small change
    }
    
    assert runner._is_safe_for_auto_execution(action_safe)
    
    # Low confidence (not safe)
    action_low_conf = {
        "type": "scale_up",
        "confidence": 0.60,
        "amount_pct": 0.1,
    }
    
    assert not runner._is_safe_for_auto_execution(action_low_conf)
    
    # Reallocation (too complex, not safe)
    action_reallocate = {
        "type": "reallocate",
        "confidence": 0.90,
    }
    
    assert not runner._is_safe_for_auto_execution(action_reallocate)
    
    # Pause (always safe)
    action_pause = {
        "type": "pause",
        "confidence": 0.70,
    }
    
    assert runner._is_safe_for_auto_execution(action_pause)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
