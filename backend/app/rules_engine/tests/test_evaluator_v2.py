"""
Tests for evaluator_v2.py - Rules evaluator
"""

import pytest
from datetime import datetime
from backend.app.rules_engine.evaluator_v2 import (
    RulesEvaluatorV2,
    DecisionResult,
    ActionType
)
from backend.app.rules_engine.loader_v2 import (
    RulesLoaderV2,
    DecisionRule,
    MergedRuleSet,
    RulePriority,
    RuleType
)
from backend.app.rules_engine.rule_context import StateSnapshot, Platform


@pytest.fixture
def sample_ruleset():
    """Create sample ruleset for testing."""
    rules = [
        DecisionRule(
            rule_id="cost_guard_daily",
            rule_type=RuleType.COST_GUARD,
            priority=RulePriority.CRITICAL,
            name="Daily budget",
            description="Daily limit",
            conditions={"daily_limit": 10.0},
            actions=["reject"],
            enabled=True
        ),
        DecisionRule(
            rule_id="quality_gate_official",
            rule_type=RuleType.QUALITY_GATE,
            priority=RulePriority.HIGH,
            name="Quality gate",
            description="Official quality",
            conditions={"min_quality": 8.0},
            actions=["reject_if_below"],
            enabled=True
        )
    ]
    
    return MergedRuleSet(
        version="1.0",
        rules=rules,
        brand_config={
            "quality_standards": {
                "official_channel": {"minimum_quality_score": 8.0}
            },
            "content_boundaries": {
                "brand_compliance_threshold": 0.8
            }
        },
        satellite_config={
            "quality_standards": {"minimum_quality_score": 5.0}
        },
        strategy_config={}
    )


@pytest.fixture
def sample_snapshot():
    """Create sample state snapshot."""
    return StateSnapshot(
        snapshot_id="test_snapshot_123",
        vision_analysis={
            "quality_score": 8.5,
            "brand_compliance_score": 0.85,
            "aesthetic_score": 8.0
        },
        cm_state={
            "daily_plan": {
                "official_posts_scheduled": 0,
                "next_official_post_time": "2024-01-01T14:00:00Z"
            }
        },
        satellite_metrics={},
        ml_predictions={
            "predicted_retention": 0.75,
            "predicted_engagement": 0.08,
            "virality_score": 0.70
        },
        brand_rules={},
        trend_signals={},
        meta_ads_state={},
        orchestrator_state={
            "system_health": {"status": "healthy"}
        },
        cost_tracking={
            "daily_spend": 5.0,
            "monthly_spend": 15.0,
            "daily_limit": 10.0,
            "monthly_limit": 30.0
        },
        content={
            "channel_type": "official",
            "platform": Platform.TIKTOK
        }
    )


class TestRulesEvaluatorV2:
    """Test cases for RulesEvaluatorV2."""
    
    def test_init(self, sample_ruleset):
        """Test evaluator initialization."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        assert evaluator.ruleset == sample_ruleset
        assert len(evaluator.rules_by_priority) == 4  # All priority levels
    
    @pytest.mark.asyncio
    async def test_evaluate_returns_decision(self, sample_ruleset, sample_snapshot):
        """Test that evaluate returns DecisionResult."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        assert isinstance(decision, DecisionResult)
        assert isinstance(decision.recommended_action, ActionType)
        assert isinstance(decision.action_priority, RulePriority)
        assert 0.0 <= decision.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_evaluate_performance(self, sample_ruleset, sample_snapshot):
        """Test that evaluation completes in <30ms."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Check performance target
        assert decision.evaluation_time_ms < 30.0, \
            f"Evaluation took {decision.evaluation_time_ms:.2f}ms (target: <30ms)"
    
    @pytest.mark.asyncio
    async def test_critical_rules_budget_exceeded(self, sample_ruleset, sample_snapshot):
        """Test CRITICAL rules block when daily budget exceeded."""
        # Set daily spend to exceed limit
        sample_snapshot.cost_tracking["daily_spend"] = 10.5
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should reject due to budget
        assert decision.recommended_action == ActionType.REJECT_CONTENT
        assert decision.action_priority == RulePriority.CRITICAL
        assert any("budget" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_high_rules_quality_check_passes(self, sample_ruleset, sample_snapshot):
        """Test HIGH rules pass when quality meets threshold."""
        # Good quality
        sample_snapshot.vision_analysis["quality_score"] = 8.5
        sample_snapshot.vision_analysis["brand_compliance_score"] = 0.85
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should pass quality checks
        assert decision.recommended_action == ActionType.POST_SHORT
        assert any("quality" in r.lower() or "meets" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_high_rules_quality_check_fails(self, sample_ruleset, sample_snapshot):
        """Test HIGH rules fail when quality below threshold."""
        # Low quality
        sample_snapshot.vision_analysis["quality_score"] = 6.0
        sample_snapshot.vision_analysis["brand_compliance_score"] = 0.85
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should hold content
        assert decision.recommended_action == ActionType.HOLD_CONTENT
        assert any("quality" in r.lower() or "below" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_satellite_content_lower_threshold(self, sample_ruleset, sample_snapshot):
        """Test satellite content uses lower quality threshold."""
        # Satellite content with moderate quality
        sample_snapshot.content["channel_type"] = "satellite"
        sample_snapshot.vision_analysis["quality_score"] = 6.0
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should pass satellite threshold (5.0) and post
        assert decision.recommended_action == ActionType.POST_TO_SATELLITE
    
    @pytest.mark.asyncio
    async def test_satellite_content_below_threshold(self, sample_ruleset, sample_snapshot):
        """Test satellite content rejected if below threshold."""
        # Satellite content with very low quality
        sample_snapshot.content["channel_type"] = "satellite"
        sample_snapshot.vision_analysis["quality_score"] = 3.0
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should reject
        assert decision.recommended_action == ActionType.REJECT_CONTENT
    
    @pytest.mark.asyncio
    async def test_ml_high_prediction_triggers_review(self, sample_ruleset, sample_snapshot):
        """Test high ML prediction triggers review despite failed brand checks."""
        # Fail brand checks but high ML prediction
        sample_snapshot.vision_analysis["quality_score"] = 7.0  # Below 8.0
        sample_snapshot.ml_predictions["predicted_retention"] = 0.85  # High
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should request review
        assert decision.recommended_action == ActionType.REQUEST_REVIEW
        assert decision.requires_human_approval is True
    
    @pytest.mark.asyncio
    async def test_decision_includes_reasoning(self, sample_ruleset, sample_snapshot):
        """Test that decision includes reasoning."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        assert len(decision.reasoning) > 0
        assert all(isinstance(r, str) for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_decision_includes_triggered_rules(self, sample_ruleset, sample_snapshot):
        """Test that decision tracks triggered rules."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        assert isinstance(decision.triggered_rules, list)
    
    @pytest.mark.asyncio
    async def test_budget_warning_threshold(self, sample_ruleset, sample_snapshot):
        """Test warnings appear at 90% budget usage."""
        # Set spend to 90% of limit
        sample_snapshot.cost_tracking["daily_spend"] = 9.0  # 90% of 10.0
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should have warnings but still allow action
        assert len(decision.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_monthly_budget_exceeded(self, sample_ruleset, sample_snapshot):
        """Test monthly budget enforcement."""
        # Exceed monthly limit
        sample_snapshot.cost_tracking["monthly_spend"] = 35.0
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should reject
        assert decision.recommended_action == ActionType.REJECT_CONTENT
        assert any("monthly" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_no_content_returns_log_decision(self, sample_ruleset, sample_snapshot):
        """Test evaluation without content returns LOG_DECISION."""
        sample_snapshot.content = None
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        assert decision.recommended_action == ActionType.LOG_DECISION
    
    @pytest.mark.asyncio
    async def test_brand_compliance_check(self, sample_ruleset, sample_snapshot):
        """Test brand compliance threshold enforcement."""
        # Fail brand compliance
        sample_snapshot.vision_analysis["quality_score"] = 8.5  # Good quality
        sample_snapshot.vision_analysis["brand_compliance_score"] = 0.70  # Below 0.8
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should hold due to brand compliance
        assert decision.recommended_action in [ActionType.HOLD_CONTENT, ActionType.REQUEST_REVIEW]
        assert any("brand" in r.lower() or "compliance" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_virality_boost_flag(self, sample_ruleset, sample_snapshot):
        """Test that high virality score sets boost flag in action params."""
        # High virality score
        sample_snapshot.ml_predictions["virality_score"] = 0.80
        sample_snapshot.vision_analysis["quality_score"] = 8.5
        sample_snapshot.vision_analysis["brand_compliance_score"] = 0.85
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should recommend post with boost
        if decision.recommended_action == ActionType.POST_SHORT:
            assert decision.action_params.get("boost") is True
    
    @pytest.mark.asyncio
    async def test_get_evaluation_summary(self, sample_ruleset, sample_snapshot):
        """Test evaluation summary generation."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        summary = evaluator.get_evaluation_summary(decision)
        
        assert "decision" in summary
        assert "priority" in summary
        assert "confidence" in summary
        assert "evaluation_time" in summary
    
    @pytest.mark.asyncio
    async def test_satellite_prohibition_artist_detected(self, sample_ruleset, sample_snapshot):
        """Test satellite prohibition when artist detected."""
        # Satellite content with artist
        sample_snapshot.content["channel_type"] = "satellite"
        sample_snapshot.vision_analysis["artist_detected"] = True
        
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Should reject due to prohibition
        assert decision.recommended_action == ActionType.REJECT_CONTENT
        assert any("artist" in r.lower() or "prohibited" in r.lower() for r in decision.reasoning)
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, sample_ruleset, sample_snapshot):
        """Test that confidence scores are reasonable."""
        evaluator = RulesEvaluatorV2(sample_ruleset)
        decision = await evaluator.evaluate(sample_snapshot)
        
        # Confidence should be between 0 and 1
        assert 0.0 <= decision.confidence <= 1.0
        
        # High confidence for clear decisions
        if decision.recommended_action in [ActionType.REJECT_CONTENT, ActionType.POST_SHORT]:
            assert decision.confidence >= 0.80


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
