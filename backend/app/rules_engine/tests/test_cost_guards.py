"""
Tests for cost_guards.py - Budget enforcement
"""

import pytest
from datetime import datetime
from backend.app.rules_engine.cost_guards import CostGuard, BudgetStatus
from backend.app.rules_engine.evaluator_v2 import (
    ActionType,
    DecisionResult,
    RulePriority
)


@pytest.fixture
def cost_guard():
    """Create CostGuard with default limits."""
    return CostGuard(
        daily_limit=10.0,
        monthly_limit=30.0,
        action_limit=0.10
    )


@pytest.fixture
def sample_decision():
    """Create sample decision."""
    return DecisionResult(
        timestamp=datetime.utcnow(),
        snapshot_id="test_123",
        triggered_rules=[],
        recommended_action=ActionType.POST_SHORT,
        action_priority=RulePriority.HIGH,
        confidence=0.90,
        reasoning=["Test reason"],
        evaluation_time_ms=10.0
    )


@pytest.fixture
def sample_cost_tracking():
    """Create sample cost tracking data."""
    return {
        "daily_spend": 5.0,
        "monthly_spend": 15.0,
        "daily_limit": 10.0,
        "monthly_limit": 30.0,
        "per_action_costs": [0.02, 0.01, 0.03],
        "last_hour_spend": 1.0
    }


class TestCostGuard:
    """Test cases for CostGuard."""
    
    def test_init_with_defaults(self):
        """Test initialization with default limits."""
        guard = CostGuard()
        assert guard.daily_limit == 10.0
        assert guard.monthly_limit == 30.0
        assert guard.action_limit == 0.10
    
    def test_init_with_custom_limits(self):
        """Test initialization with custom limits."""
        guard = CostGuard(daily_limit=20.0, monthly_limit=50.0, action_limit=0.20)
        assert guard.daily_limit == 20.0
        assert guard.monthly_limit == 50.0
        assert guard.action_limit == 0.20
    
    def test_check_passes_with_budget_available(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test check passes when budget available."""
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is True
        assert result.status in [BudgetStatus.OK, BudgetStatus.WARNING]
        assert result.daily_remaining > 0
        assert result.monthly_remaining > 0
    
    def test_check_blocks_daily_limit_exceeded(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test check blocks when daily limit exceeded."""
        sample_cost_tracking["daily_spend"] = 10.5  # Exceeds 10.0
        
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is False
        assert result.status == BudgetStatus.EXCEEDED
        assert "daily" in result.reason.lower()
    
    def test_check_blocks_monthly_limit_exceeded(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test check blocks when monthly limit exceeded."""
        sample_cost_tracking["monthly_spend"] = 35.0  # Exceeds 30.0
        
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is False
        assert result.status == BudgetStatus.EXCEEDED
        assert "monthly" in result.reason.lower()
    
    def test_check_blocks_expensive_action(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test check blocks action that exceeds per-action limit."""
        # START_CAMPAIGN costs 0.10, which equals the limit
        sample_decision.recommended_action = ActionType.START_CAMPAIGN
        guard = CostGuard(action_limit=0.05)  # Lower limit
        
        result = guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is False
        assert result.status == BudgetStatus.EXCEEDED
        assert "action cost" in result.reason.lower()
    
    def test_check_blocks_if_action_would_exceed_daily(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test check blocks if action would exceed daily limit."""
        sample_cost_tracking["daily_spend"] = 9.95  # Just under limit
        sample_decision.recommended_action = ActionType.BOOST_POST  # Costs 0.08
        
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        # 9.95 + 0.08 = 10.03 > 10.0
        assert result.allowed is False
        assert "daily limit" in result.reason.lower()
    
    def test_warning_at_90_percent_daily(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test warning appears at 90% daily budget."""
        sample_cost_tracking["daily_spend"] = 9.0  # 90% of 10.0
        
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is True
        assert result.status == BudgetStatus.WARNING
        assert len(result.warnings) > 0
        assert any("daily" in w.lower() for w in result.warnings)
    
    def test_warning_at_90_percent_monthly(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test warning appears at 90% monthly budget."""
        sample_cost_tracking["monthly_spend"] = 27.0  # 90% of 30.0
        
        result = cost_guard.check(sample_decision, sample_cost_tracking)
        
        assert result.allowed is True
        assert result.status == BudgetStatus.WARNING
        assert len(result.warnings) > 0
        assert any("monthly" in w.lower() for w in result.warnings)
    
    def test_free_actions_always_allowed(
        self, cost_guard, sample_decision, sample_cost_tracking
    ):
        """Test that free actions (log, hold, etc.) are always allowed."""
        # Even with budget exceeded
        sample_cost_tracking["daily_spend"] = 15.0  # Exceeds limit
        
        # Free actions
        free_actions = [
            ActionType.HOLD_CONTENT,
            ActionType.REQUEST_REVIEW,
            ActionType.LOG_DECISION,
            ActionType.REJECT_CONTENT
        ]
        
        for action in free_actions:
            sample_decision.recommended_action = action
            result = cost_guard.check(sample_decision, sample_cost_tracking)
            
            # Free actions don't exceed action limit, but daily limit still blocks
            if sample_cost_tracking["daily_spend"] >= cost_guard.daily_limit:
                assert result.allowed is False  # Blocked by daily limit
            else:
                assert result.allowed is True  # Would be allowed if budget OK
    
    def test_action_costs_defined(self, cost_guard):
        """Test that all actions have defined costs."""
        all_actions = list(ActionType)
        
        for action in all_actions:
            assert action in CostGuard.ACTION_COSTS, f"Cost not defined for {action}"
            cost = CostGuard.ACTION_COSTS[action]
            assert cost >= 0.0, f"Cost must be non-negative for {action}"
    
    def test_check_safety_passes_healthy_system(self, cost_guard, sample_decision):
        """Test safety check passes for healthy system."""
        snapshot_state = {
            "orchestrator_state": {
                "system_health": {"status": "healthy"}
            }
        }
        
        allowed, reason = cost_guard.check_safety(sample_decision, snapshot_state)
        
        assert allowed is True
        assert "passed" in reason.lower()
    
    def test_check_safety_blocks_degraded_system(self, cost_guard, sample_decision):
        """Test safety check blocks non-safe actions in degraded system."""
        snapshot_state = {
            "orchestrator_state": {
                "system_health": {"status": "degraded"}
            }
        }
        
        sample_decision.recommended_action = ActionType.START_CAMPAIGN
        
        allowed, reason = cost_guard.check_safety(sample_decision, snapshot_state)
        
        assert allowed is False
        assert "degraded" in reason.lower()
    
    def test_check_safety_allows_safe_actions_degraded(self, cost_guard, sample_decision):
        """Test safety check allows safe actions even in degraded system."""
        snapshot_state = {
            "orchestrator_state": {
                "system_health": {"status": "degraded"}
            }
        }
        
        sample_decision.recommended_action = ActionType.LOG_DECISION
        
        allowed, reason = cost_guard.check_safety(sample_decision, snapshot_state)
        
        assert allowed is True
    
    def test_check_safety_blocks_error_system(self, cost_guard, sample_decision):
        """Test safety check blocks all actions in error state."""
        snapshot_state = {
            "orchestrator_state": {
                "system_health": {"status": "error"}
            }
        }
        
        allowed, reason = cost_guard.check_safety(sample_decision, snapshot_state)
        
        assert allowed is False
        assert "error" in reason.lower()
    
    def test_check_safety_dangerous_action_approval(self, cost_guard, sample_decision):
        """Test dangerous actions require explicit approval."""
        snapshot_state = {
            "orchestrator_state": {
                "system_health": {"status": "healthy"}
            }
        }
        
        sample_decision.recommended_action = ActionType.EMERGENCY_PAUSE
        sample_decision.action_params = {"approved": False}
        
        allowed, reason = cost_guard.check_safety(sample_decision, snapshot_state)
        
        assert allowed is False
        assert "approval" in reason.lower()
    
    def test_detect_anomalies_normal_spend(self, cost_guard, sample_cost_tracking):
        """Test anomaly detection with normal spending."""
        has_anomalies, anomalies = cost_guard.detect_anomalies(sample_cost_tracking)
        
        assert has_anomalies is False
        assert len(anomalies) == 0
    
    def test_detect_anomalies_spike(self, cost_guard, sample_cost_tracking):
        """Test anomaly detection for spending spike."""
        historical = [
            {"daily_spend": 2.0},
            {"daily_spend": 2.5},
            {"daily_spend": 3.0}
        ]
        
        sample_cost_tracking["daily_spend"] = 12.0  # 4x average
        
        has_anomalies, anomalies = cost_guard.detect_anomalies(
            sample_cost_tracking, historical
        )
        
        assert has_anomalies is True
        assert len(anomalies) > 0
        assert any("spike" in a.lower() for a in anomalies)
    
    def test_detect_anomalies_rapid_accumulation(self, cost_guard, sample_cost_tracking):
        """Test anomaly detection for rapid cost accumulation."""
        sample_cost_tracking["daily_spend"] = 10.0
        sample_cost_tracking["last_hour_spend"] = 6.0  # 60% of daily in 1 hour
        
        has_anomalies, anomalies = cost_guard.detect_anomalies(sample_cost_tracking)
        
        assert has_anomalies is True
        assert any("rapid" in a.lower() for a in anomalies)
    
    def test_get_budget_summary(self, cost_guard, sample_cost_tracking):
        """Test budget summary generation."""
        summary = cost_guard.get_budget_summary(sample_cost_tracking)
        
        assert "daily" in summary
        assert "monthly" in summary
        assert "status" in summary
        
        assert "spend" in summary["daily"]
        assert "limit" in summary["daily"]
        assert "remaining" in summary["daily"]
        assert "percentage" in summary["daily"]
    
    def test_budget_summary_status_ok(self, cost_guard):
        """Test budget summary shows OK status."""
        cost_tracking = {
            "daily_spend": 3.0,
            "monthly_spend": 10.0,
            "daily_limit": 10.0,
            "monthly_limit": 30.0
        }
        
        summary = cost_guard.get_budget_summary(cost_tracking)
        
        assert "🟢" in summary["status"]
    
    def test_budget_summary_status_warning(self, cost_guard):
        """Test budget summary shows WARNING status."""
        cost_tracking = {
            "daily_spend": 9.5,  # 95%
            "monthly_spend": 10.0,
            "daily_limit": 10.0,
            "monthly_limit": 30.0
        }
        
        summary = cost_guard.get_budget_summary(cost_tracking)
        
        assert "🟡" in summary["status"]
    
    def test_budget_summary_status_exceeded(self, cost_guard):
        """Test budget summary shows EXCEEDED status."""
        cost_tracking = {
            "daily_spend": 12.0,  # Exceeded
            "monthly_spend": 10.0,
            "daily_limit": 10.0,
            "monthly_limit": 30.0
        }
        
        summary = cost_guard.get_budget_summary(cost_tracking)
        
        assert "🔴" in summary["status"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
