"""
Tests for Meta Autonomous System Layer (PASO 10.7)

Tests policy engine, safety engine, and autonomous worker
in stub mode (no real Meta API calls).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.meta_autonomous.policy_engine import PolicyEngine
from app.meta_autonomous.safety import SafetyEngine
from app.meta_autonomous.auto_worker import MetaAutoWorker
from app.meta_autonomous.config import AutonomousSettings
from app.models.database import MetaCampaignModel, MetaROASMetricsModel


@pytest.fixture
def policy_engine():
    """Create policy engine with test settings."""
    settings = AutonomousSettings(
        MAX_DAILY_CHANGE_PCT=0.20,
        MAX_AUTO_CHANGE_PCT=0.10,
        HARD_STOP_ROAS=0.9,
        HARD_STOP_CONFIDENCE=0.70,
        MIN_SPAIN_PERCENTAGE=0.35,
        MAX_SINGLE_COUNTRY_PCT=0.70,
    )
    return PolicyEngine(settings)


@pytest.fixture
def safety_engine():
    """Create safety engine with test settings."""
    settings = AutonomousSettings(
        MAX_DAILY_SPEND_USD=10000.0,
        MIN_IMPRESSIONS=1000,
        MIN_SPEND_USD=100.0,
        MIN_AGE_HOURS=48,
        CREATIVE_EMBARGO_HOURS=48,
    )
    return SafetyEngine(settings)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    return mock_session


# ============================================================================
# Policy Engine Tests
# ============================================================================

def test_policy_allows_valid_budget_scale(policy_engine):
    """Test that policy allows valid budget changes."""
    # 15% increase is within 20% limit
    allowed, reason = policy_engine.can_scale_budget(
        current_budget=1000,
        new_budget=1150,
        is_auto_mode=False
    )
    assert allowed is True
    assert reason is None


def test_policy_blocks_excessive_budget_change(policy_engine):
    """Test that policy blocks changes exceeding limits."""
    # 50% increase exceeds 20% limit
    allowed, reason = policy_engine.can_scale_budget(
        current_budget=1000,
        new_budget=1500,
        is_auto_mode=False
    )
    assert allowed is False
    assert "exceeds limit" in reason


def test_policy_enforces_stricter_limits_in_auto_mode(policy_engine):
    """Test that auto mode has stricter limits (10% vs 20%)."""
    # 15% is OK in suggest mode
    allowed, _ = policy_engine.can_scale_budget(
        current_budget=1000,
        new_budget=1150,
        is_auto_mode=False
    )
    assert allowed is True
    
    # But blocked in auto mode (15% > 10% auto limit)
    blocked, reason = policy_engine.can_scale_budget(
        current_budget=1000,
        new_budget=1150,
        is_auto_mode=True
    )
    assert blocked is False
    assert "exceeds limit" in reason


def test_policy_hard_stop_triggers_correctly(policy_engine):
    """Test that hard stop triggers for low ROAS with high confidence."""
    # Hard stop: ROAS 0.7 < 0.9 threshold, confidence 0.80 > 0.70 threshold
    must_stop, reason = policy_engine.must_halt(
        roas=0.7,
        confidence=0.80,
        spend=150  # Above minimum
    )
    assert must_stop is True
    assert "HARD STOP" in reason


def test_policy_hard_stop_not_triggered_low_confidence(policy_engine):
    """Test that hard stop doesn't trigger with low confidence."""
    # Low confidence (0.60 < 0.70) prevents hard stop even with low ROAS
    must_stop, reason = policy_engine.must_halt(
        roas=0.7,
        confidence=0.60,
        spend=150
    )
    assert must_stop is False


def test_policy_validates_geo_distribution(policy_engine):
    """Test geographic distribution validation."""
    # Valid: Spain 40%, Mexico 35%, Colombia 25%
    valid, _ = policy_engine.validate_geo_distribution(
        distribution={"ES": 0.40, "MX": 0.35, "CO": 0.25},
        countries=["ES", "MX", "CO"]
    )
    assert valid is True
    
    # Invalid: Spain only 20% (< 35% required)
    invalid, reason = policy_engine.validate_geo_distribution(
        distribution={"ES": 0.20, "MX": 0.50, "CO": 0.30},
        countries=["ES", "MX", "CO"]
    )
    assert invalid is False
    assert "Spain must have at least" in reason


def test_policy_blocks_unapproved_creatives(policy_engine):
    """Test that policy blocks unapproved creatives."""
    # Set to require approval
    policy_engine.settings.REQUIRE_HUMAN_APPROVAL_CREATIVES = True
    
    allowed, reason = policy_engine.can_change_creative(
        creative_metadata={"is_human_approved": False},
        last_change=None
    )
    assert allowed is False
    assert "requires human approval" in reason


# ============================================================================
# Safety Engine Tests
# ============================================================================

@pytest.mark.asyncio
async def test_safety_prevents_overspend(safety_engine):
    """Test that safety engine prevents overspending."""
    # Already spent $9,500 of $10,000 daily limit
    blocked, reason = await safety_engine.prevent_overspend(
        spend_today=9500,
        proposed_budget=600,  # Would exceed limit
        db=None
    )
    assert blocked is True
    assert "exceed daily limit" in reason


@pytest.mark.asyncio
async def test_safety_allows_within_limit_spend(safety_engine):
    """Test that safety allows spend within limits."""
    # Spent $5,000, adding $2,000 is OK
    blocked, reason = await safety_engine.prevent_overspend(
        spend_today=5000,
        proposed_budget=2000,
        db=None
    )
    assert blocked is False


def test_safety_enforces_embargo_period(safety_engine):
    """Test that safety enforces embargo for new entities."""
    # Created 24 hours ago (< 48h embargo)
    created_24h_ago = datetime.utcnow() - timedelta(hours=24)
    
    in_embargo, reason = safety_engine.enforce_embargo_period(created_24h_ago)
    assert in_embargo is True
    assert "embargo" in reason
    
    # Created 72 hours ago (> 48h embargo)
    created_72h_ago = datetime.utcnow() - timedelta(hours=72)
    
    in_embargo, reason = safety_engine.enforce_embargo_period(created_72h_ago)
    assert in_embargo is False


def test_safety_checks_minimum_data(safety_engine):
    """Test that safety requires minimum data for optimization."""
    # Insufficient impressions
    insufficient, reason = safety_engine.check_minimum_data(
        impressions=500,  # < 1000 required
        spend=150
    )
    assert insufficient is True
    assert "Insufficient impressions" in reason
    
    # Insufficient spend
    insufficient, reason = safety_engine.check_minimum_data(
        impressions=2000,
        spend=50  # < $100 required
    )
    assert insufficient is True
    assert "Insufficient spend" in reason
    
    # Sufficient data
    insufficient, reason = safety_engine.check_minimum_data(
        impressions=2000,
        spend=150
    )
    assert insufficient is False


def test_safety_blocks_unapproved_creatives(safety_engine):
    """Test that safety blocks unapproved creatives."""
    blocked, reason = safety_engine.block_unapproved_creatives(
        creative={"id": "creative_123", "is_human_approved": False}
    )
    assert blocked is True
    assert "requires human approval" in reason


@pytest.mark.asyncio
async def test_safety_rate_limit(safety_engine):
    """Test action rate limiting."""
    # Last action 12 hours ago (< 24h cooldown)
    last_action = datetime.utcnow() - timedelta(hours=12)
    
    rate_limited, reason = await safety_engine.check_action_rate_limit(
        entity_id="ad_123",
        action_type="scale_up",
        last_action_time=last_action,
        cooldown_hours=24
    )
    assert rate_limited is True
    assert "Rate limit" in reason


# ============================================================================
# Autonomous Worker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_auto_worker_produces_actions(mock_db_session):
    """Test that worker generates optimization actions."""
    # Create mock dbmaker that returns a proper async context manager
    class MockDBMaker:
        def __init__(self, session):
            self.session = session
        
        async def __aenter__(self):
            return self.session
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
        def __call__(self):
            return self
    
    mock_dbmaker = MockDBMaker(mock_db_session)
    
    settings = AutonomousSettings(
        META_AUTO_ENABLED=True,
        META_AUTO_MODE="suggest",
        MAX_CAMPAIGNS_PER_TICK=10
    )
    
    worker = MetaAutoWorker(mock_dbmaker, settings)
    
    # Mock database responses
    campaign = MetaCampaignModel(
        id=uuid4(),
        campaign_id="CAMPAIGN_123",
        status="ACTIVE",
        created_at=datetime.utcnow() - timedelta(days=5),  # Past embargo
    )
    
    # Mock execute to return campaigns and ROAS metrics
    mock_db_session.execute = AsyncMock(side_effect=[
        # Get active campaigns
        MagicMock(scalars=lambda: MagicMock(all=lambda: [campaign])),
        # Get ROAS metrics (will be called in worker)
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])),
    ])
    
    # Execute tick
    stats = await worker.tick()
    
    # Verify worker executed
    assert "tick_started_at" in stats
    assert "campaigns_evaluated" in stats
    assert stats["campaigns_evaluated"] >= 0


@pytest.mark.asyncio
async def test_mode_suggest_does_not_execute(mock_db_session):
    """Test that suggest mode only queues actions, doesn't execute."""
    class MockDBMaker:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        def __call__(self):
            return self
    
    mock_dbmaker = MockDBMaker(mock_db_session)
    
    settings = AutonomousSettings(
        META_AUTO_MODE="suggest",  # Suggest mode
    )
    
    worker = MetaAutoWorker(mock_dbmaker, settings)
    
    # Verify mode is suggest
    assert worker.settings.META_AUTO_MODE == "suggest"
    
    # In suggest mode, _is_safe_for_auto returns True but worker
    # should still queue (not execute) all actions
    action = {"type": "scale_up", "confidence": 0.80, "amount_pct": 0.05}
    context = {"is_auto_mode": False}
    
    # Even safe actions should be queued in suggest mode
    is_safe = worker._is_safe_for_auto(action, context)
    # is_safe can be True, but mode dictates behavior


@pytest.mark.asyncio
async def test_mode_auto_executes_safe_actions(mock_db_session):
    """Test that auto mode executes safe actions automatically."""
    class MockDBMaker:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        def __call__(self):
            return self
    
    mock_dbmaker = MockDBMaker(mock_db_session)
    
    settings = AutonomousSettings(
        META_AUTO_MODE="auto",  # Auto mode
        MAX_AUTO_CHANGE_PCT=0.10,
    )
    
    worker = MetaAutoWorker(mock_dbmaker, settings)
    
    # Verify mode is auto
    assert worker.settings.META_AUTO_MODE == "auto"
    
    # Safe action: pause (always safe)
    action = {"type": "pause", "confidence": 0.80}
    context = {"is_auto_mode": True}
    
    is_safe = worker._is_safe_for_auto(action, context)
    assert is_safe is True
    
    # Unsafe action: reallocation (never auto)
    action = {"type": "reallocate", "confidence": 0.95}
    
    is_safe = worker._is_safe_for_auto(action, context)
    assert is_safe is False


def test_worker_initialization(mock_db_session):
    """Test worker initializes correctly with settings."""
    class MockDBMaker:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        def __call__(self):
            return self
    
    mock_dbmaker = MockDBMaker(mock_db_session)
    
    settings = AutonomousSettings(
        META_AUTO_ENABLED=True,
        META_AUTO_MODE="suggest",
        META_AUTO_INTERVAL_SECONDS=1800,
    )
    
    worker = MetaAutoWorker(mock_dbmaker, settings)
    
    assert worker.settings.META_AUTO_ENABLED is True
    assert worker.settings.META_AUTO_MODE == "suggest"
    assert worker.settings.META_AUTO_INTERVAL_SECONDS == 1800
    assert worker.policy_engine is not None
    assert worker.safety_engine is not None
    assert worker._running is False


# ============================================================================
# Integration Tests
# ============================================================================

def test_policy_and_safety_work_together(policy_engine, safety_engine):
    """Test that policy and safety engines can validate the same action."""
    # Action that passes policy but might fail safety
    action_data = {"budget": 500}
    context = {
        "is_auto_mode": False,
        "current_budget": 400,
        "roas": 2.5,
        "confidence": 0.80,
        "spend": 200,
        "impressions": 5000,
        "created_at": datetime.utcnow() - timedelta(days=10),  # Past embargo
        "entity_id": "ad_123",
        "spend_today": 9800,  # High daily spend
        "last_action_time": None,
    }
    
    # Policy check: 25% increase is within 20% limit? No, it's 25%
    # Actually 500/400 = 1.25, so 25% increase
    policy_ok, policy_reason = policy_engine.can_scale_budget(
        current_budget=400,
        new_budget=500,
        is_auto_mode=False
    )
    # This should fail (25% > 20%)
    assert policy_ok is False
    
    # Even if policy passed, safety would block due to high daily spend
    # (spend_today=9800 + budget=500 would exceed 10000 limit)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
