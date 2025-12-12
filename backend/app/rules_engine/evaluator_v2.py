"""
Rules Evaluator v2 - Evaluate rules against state snapshot

Takes RuleSet + StateSnapshot and returns:
- Triggered rules
- Priority level
- Recommended action
- Reasoning

Performance target: <30ms total evaluation time
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import time

from .loader_v2 import DecisionRule, MergedRuleSet, RulePriority, RuleType
from .rule_context import StateSnapshot, ChannelType, Platform


class ActionType(str, Enum):
    """Types of actions the system can recommend."""
    # Content actions
    POST_SHORT = "post_short"
    HOLD_CONTENT = "hold_content"
    REQUEST_REVIEW = "request_review"
    FORCE_RERENDER = "force_rerender"
    SELECT_NEW_CLIPS = "select_new_clips"
    
    # Satellite actions
    POST_TO_SATELLITE = "post_to_satellite"
    RESCHEDULE_POST = "reschedule_post"
    BOOST_POST = "boost_post"
    
    # CM actions
    UPDATE_CONTENT_PLAN = "update_content_plan"
    REQUEST_BRAND_INTERROGATION = "request_brand_interrogation"
    REFINE_GUIDELINES = "refine_guidelines"
    
    # Meta Ads actions
    ADJUST_BUDGET = "adjust_budget"
    START_CAMPAIGN = "start_campaign"
    PAUSE_CAMPAIGN = "pause_campaign"
    
    # Orchestrator actions
    LOG_DECISION = "log_decision"
    PUSH_ALERT_TELEGRAM = "push_alert_telegram"
    REQUEST_HUMAN_APPROVAL = "request_human_approval"
    
    # Safety actions
    REJECT_CONTENT = "reject_content"
    EMERGENCY_PAUSE = "emergency_pause"


class DecisionResult(BaseModel):
    """Result of rule evaluation."""
    timestamp: datetime
    snapshot_id: str
    
    # Triggered rules
    triggered_rules: List[str]  # rule_ids
    
    # Decision
    recommended_action: ActionType
    action_priority: RulePriority
    confidence: float  # 0.0 to 1.0
    
    # Reasoning
    reasoning: List[str]
    warnings: List[str] = []
    
    # Action parameters
    action_params: Dict[str, Any] = {}
    
    # Performance
    evaluation_time_ms: float
    
    # Approval required?
    requires_human_approval: bool = False


class RulesEvaluatorV2:
    """
    Evaluates rules against state snapshot to make decisions.
    
    Decision flow:
    1. Check CRITICAL rules (safety, cost guards) - REJECT if violated
    2. Check HIGH rules (brand compliance, quality) - EVALUATE for official
    3. Check MEDIUM rules (trends, platform) - RECOMMEND actions
    4. Check LOW rules (ML predictions) - OPTIMIZE actions
    """
    
    def __init__(self, ruleset: MergedRuleSet):
        """
        Initialize evaluator with ruleset.
        
        Args:
            ruleset: Merged rules from RulesLoaderV2
        """
        self.ruleset = ruleset
        self.rules_by_priority = self._organize_rules_by_priority()
    
    def _organize_rules_by_priority(self) -> Dict[RulePriority, List[DecisionRule]]:
        """Organize rules by priority for fast lookup."""
        organized = {
            RulePriority.CRITICAL: [],
            RulePriority.HIGH: [],
            RulePriority.MEDIUM: [],
            RulePriority.LOW: []
        }
        
        for rule in self.ruleset.rules:
            if rule.enabled:
                organized[rule.priority].append(rule)
        
        return organized
    
    async def evaluate(self, snapshot: StateSnapshot) -> DecisionResult:
        """
        Evaluate rules against snapshot and return decision.
        
        Args:
            snapshot: Current system state
            
        Returns:
            DecisionResult with recommended action
        """
        start_time = time.time()
        
        triggered_rules = []
        reasoning = []
        warnings = []
        
        # Step 1: Check CRITICAL rules (safety, cost guards)
        critical_result = await self._evaluate_critical(snapshot)
        triggered_rules.extend(critical_result["triggered"])
        reasoning.extend(critical_result["reasoning"])
        
        if critical_result["reject"]:
            return DecisionResult(
                timestamp=datetime.utcnow(),
                snapshot_id=snapshot.snapshot_id,
                triggered_rules=triggered_rules,
                recommended_action=ActionType.REJECT_CONTENT,
                action_priority=RulePriority.CRITICAL,
                confidence=1.0,
                reasoning=reasoning,
                warnings=critical_result.get("warnings", []),
                evaluation_time_ms=(time.time() - start_time) * 1000,
                requires_human_approval=False
            )
        
        # Step 2: Check HIGH rules (brand compliance, quality)
        high_result = await self._evaluate_high(snapshot)
        triggered_rules.extend(high_result["triggered"])
        reasoning.extend(high_result["reasoning"])
        warnings.extend(high_result.get("warnings", []))
        
        # Step 3: Check MEDIUM rules (trends, platform)
        medium_result = await self._evaluate_medium(snapshot)
        triggered_rules.extend(medium_result["triggered"])
        reasoning.extend(medium_result["reasoning"])
        
        # Step 4: Check LOW rules (ML predictions)
        low_result = await self._evaluate_low(snapshot)
        triggered_rules.extend(low_result["triggered"])
        reasoning.extend(low_result["reasoning"])
        
        # Step 5: Make final decision
        decision = await self._make_decision(
            snapshot, high_result, medium_result, low_result
        )
        
        evaluation_time = (time.time() - start_time) * 1000
        
        return DecisionResult(
            timestamp=datetime.utcnow(),
            snapshot_id=snapshot.snapshot_id,
            triggered_rules=triggered_rules,
            recommended_action=decision["action"],
            action_priority=decision["priority"],
            confidence=decision["confidence"],
            reasoning=reasoning,
            warnings=warnings,
            action_params=decision.get("params", {}),
            evaluation_time_ms=evaluation_time,
            requires_human_approval=decision.get("requires_approval", False)
        )
    
    async def _evaluate_critical(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """Evaluate CRITICAL rules (safety, cost guards)."""
        result = {
            "triggered": [],
            "reasoning": [],
            "warnings": [],
            "reject": False
        }
        
        # Check cost guards
        daily_spend = snapshot.cost_tracking.get("daily_spend", 0.0)
        daily_limit = snapshot.cost_tracking.get("daily_limit", 10.0)
        
        if daily_spend >= daily_limit:
            result["triggered"].append("cost_guard_daily_limit")
            result["reasoning"].append(f"Daily budget exhausted: €{daily_spend:.2f}/€{daily_limit:.2f}")
            result["reject"] = True
            return result
        
        if daily_spend >= daily_limit * 0.9:
            result["warnings"].append(f"Daily budget 90% used: €{daily_spend:.2f}/€{daily_limit:.2f}")
        
        # Check satellite prohibitions
        if snapshot.content:
            channel = snapshot.content.get("channel_type", "")
            if channel == "satellite":
                # Check NO_mostrar_artista_real
                if snapshot.vision_analysis.get("artist_detected", False):
                    result["triggered"].append("satellite_prohibition_no_artist")
                    result["reasoning"].append("Satellite content shows artist - PROHIBITED")
                    result["reject"] = True
                    return result
        
        # Check monthly budget
        monthly_spend = snapshot.cost_tracking.get("monthly_spend", 0.0)
        monthly_limit = snapshot.cost_tracking.get("monthly_limit", 300.0)
        
        if monthly_spend >= monthly_limit:
            result["triggered"].append("cost_guard_monthly_limit")
            result["reasoning"].append(f"Monthly budget exhausted: €{monthly_spend:.2f}/€{monthly_limit:.2f}")
            result["reject"] = True
            return result
        
        return result
    
    async def _evaluate_high(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """Evaluate HIGH priority rules (brand compliance, quality)."""
        result = {
            "triggered": [],
            "reasoning": [],
            "warnings": [],
            "pass": True
        }
        
        if not snapshot.content:
            return result
        
        channel = snapshot.content.get("channel_type", "")
        
        # Official channel quality gate
        if channel == "official":
            quality_threshold = self.ruleset.brand_config.get("quality_standards", {}).get(
                "official_channel", {}
            ).get("minimum_quality_score", 8.0)
            
            quality_score = snapshot.vision_analysis.get("quality_score", 0.0)
            
            if quality_score < quality_threshold:
                result["triggered"].append("brand_quality_official")
                result["reasoning"].append(
                    f"Quality {quality_score:.1f} below official threshold {quality_threshold}"
                )
                result["pass"] = False
            else:
                result["reasoning"].append(
                    f"Quality {quality_score:.1f} meets official threshold {quality_threshold}"
                )
            
            # Brand compliance check
            brand_threshold = self.ruleset.brand_config.get("content_boundaries", {}).get(
                "brand_compliance_threshold", 0.8
            )
            
            brand_score = snapshot.vision_analysis.get("brand_compliance_score", 0.0)
            
            if brand_score < brand_threshold:
                result["triggered"].append("brand_compliance_check")
                result["reasoning"].append(
                    f"Brand compliance {brand_score:.2f} below threshold {brand_threshold}"
                )
                result["pass"] = False
            else:
                result["reasoning"].append(
                    f"Brand compliance {brand_score:.2f} meets threshold {brand_threshold}"
                )
        
        # Satellite channel quality gate (lower threshold)
        elif channel == "satellite":
            satellite_threshold = self.ruleset.satellite_config.get("quality_standards", {}).get(
                "minimum_quality_score", 5.0
            )
            
            quality_score = snapshot.vision_analysis.get("quality_score", 0.0)
            
            if quality_score < satellite_threshold:
                result["triggered"].append("satellite_quality_gate")
                result["reasoning"].append(
                    f"Quality {quality_score:.1f} below satellite threshold {satellite_threshold}"
                )
                result["pass"] = False
            else:
                result["reasoning"].append(
                    f"Quality {quality_score:.1f} meets satellite threshold {satellite_threshold}"
                )
        
        return result
    
    async def _evaluate_medium(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """Evaluate MEDIUM priority rules (trends, platform)."""
        result = {
            "triggered": [],
            "reasoning": [],
            "opportunities": []
        }
        
        # Check trend opportunities
        trends = snapshot.trend_signals.get("viral_opportunities", [])
        for trend in trends:
            if trend.get("confidence", 0.0) > 0.7:
                result["opportunities"].append({
                    "type": "trend",
                    "trend": trend.get("type"),
                    "window": trend.get("window"),
                    "confidence": trend.get("confidence")
                })
                result["reasoning"].append(
                    f"Trend opportunity: {trend.get('type')} (confidence {trend.get('confidence'):.2f})"
                )
        
        # Check posting schedule
        cm_state = snapshot.cm_state.get("daily_plan", {})
        official_scheduled = cm_state.get("official_posts_scheduled", 0)
        
        if official_scheduled < 1:
            result["reasoning"].append("Official channel has capacity (no posts scheduled)")
        else:
            result["reasoning"].append(f"Official channel at capacity ({official_scheduled} posts scheduled)")
        
        return result
    
    async def _evaluate_low(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """Evaluate LOW priority rules (ML predictions)."""
        result = {
            "triggered": [],
            "reasoning": [],
            "ml_insights": {}
        }
        
        if not snapshot.ml_predictions:
            return result
        
        # ML predictions
        predicted_retention = snapshot.ml_predictions.get("predicted_retention", 0.0)
        predicted_engagement = snapshot.ml_predictions.get("predicted_engagement", 0.0)
        virality_score = snapshot.ml_predictions.get("virality_score", 0.0)
        
        result["ml_insights"] = {
            "predicted_retention": predicted_retention,
            "predicted_engagement": predicted_engagement,
            "virality_score": virality_score
        }
        
        result["reasoning"].append(
            f"ML predicts: retention {predicted_retention:.2f}, engagement {predicted_engagement:.3f}, virality {virality_score:.2f}"
        )
        
        # ML recommendation
        ml_recommendation = snapshot.ml_predictions.get("recommendation", "")
        if ml_recommendation:
            result["reasoning"].append(f"ML recommends: {ml_recommendation}")
        
        return result
    
    async def _make_decision(
        self,
        snapshot: StateSnapshot,
        high_result: Dict[str, Any],
        medium_result: Dict[str, Any],
        low_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make final decision based on all rule evaluations.
        
        Returns:
            Decision dict with action, priority, confidence, params
        """
        if not snapshot.content:
            return {
                "action": ActionType.LOG_DECISION,
                "priority": RulePriority.LOW,
                "confidence": 1.0
            }
        
        channel = snapshot.content.get("channel_type", "")
        
        # Official channel decision
        if channel == "official":
            if not high_result.get("pass", True):
                # Failed quality/brand checks
                ml_insights = low_result.get("ml_insights", {})
                predicted_retention = ml_insights.get("predicted_retention", 0.0)
                
                if predicted_retention > 0.7:
                    # High ML prediction but failed brand checks
                    return {
                        "action": ActionType.REQUEST_REVIEW,
                        "priority": RulePriority.HIGH,
                        "confidence": 0.65,
                        "requires_approval": True,
                        "params": {
                            "reason": "Failed brand checks but ML predicts high performance",
                            "ml_prediction": predicted_retention
                        }
                    }
                else:
                    # Failed checks, low ML prediction
                    return {
                        "action": ActionType.HOLD_CONTENT,
                        "priority": RulePriority.HIGH,
                        "confidence": 0.85,
                        "params": {
                            "reason": "Does not meet official channel standards"
                        }
                    }
            else:
                # Passed all checks
                ml_insights = low_result.get("ml_insights", {})
                virality_score = ml_insights.get("virality_score", 0.0)
                
                platform = snapshot.content.get("platform", Platform.TIKTOK)
                
                return {
                    "action": ActionType.POST_SHORT,
                    "priority": RulePriority.HIGH,
                    "confidence": 0.90,
                    "params": {
                        "platform": platform,
                        "schedule_time": snapshot.cm_state.get("daily_plan", {}).get("next_official_post_time"),
                        "boost": virality_score > 0.75
                    }
                }
        
        # Satellite channel decision
        elif channel == "satellite":
            if not high_result.get("pass", True):
                # Failed even satellite quality threshold
                return {
                    "action": ActionType.REJECT_CONTENT,
                    "priority": RulePriority.MEDIUM,
                    "confidence": 0.80,
                    "params": {
                        "reason": "Below minimum watchability threshold"
                    }
                }
            else:
                # Satellite content ready to post
                return {
                    "action": ActionType.POST_TO_SATELLITE,
                    "priority": RulePriority.MEDIUM,
                    "confidence": 0.85,
                    "params": {
                        "platform": snapshot.content.get("platform", Platform.TIKTOK),
                        "immediate": True
                    }
                }
        
        # Default: hold for review
        return {
            "action": ActionType.REQUEST_REVIEW,
            "priority": RulePriority.MEDIUM,
            "confidence": 0.50,
            "requires_approval": True
        }
    
    def get_evaluation_summary(self, result: DecisionResult) -> Dict[str, Any]:
        """Get human-readable evaluation summary."""
        return {
            "timestamp": result.timestamp.isoformat(),
            "decision": result.recommended_action.value,
            "priority": result.action_priority.value,
            "confidence": f"{result.confidence * 100:.0f}%",
            "rules_triggered": len(result.triggered_rules),
            "requires_approval": result.requires_human_approval,
            "evaluation_time": f"{result.evaluation_time_ms:.2f}ms",
            "reasoning_summary": result.reasoning[:3],  # Top 3 reasons
            "warnings": len(result.warnings)
        }
