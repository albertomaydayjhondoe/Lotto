"""
Real-Time Decision Engine for Meta RT Performance Engine (PASO 10.14)

Makes instant decisions based on detected anomalies and applies
real-time rules to determine appropriate actions.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from app.meta_rt_engine.schemas import (
    DetectionResult,
    RealTimeDecision,
    DecisionRule,
    DecisionResponse,
    ActionType,
    SeverityLevel,
    AnomalyType,
)


class RealTimeDecisionEngine:
    """
    Real-Time Decision Engine
    
    Analyzes detection results and makes instant decisions:
    - CTR drop ≥25% → reduce budget 10-30%
    - CVR drop strong → inspect immediately
    - CPM spike → reduce bid or change objective
    - ROAS collapse → temporary pause
    - Frequency saturation → refresh targeting
    
    Mode:
        stub: Generate synthetic decisions for development/testing
        live: Use real decision logic (fully implemented)
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
        
        # Decision rules configuration
        self.rules = {
            "ctr_drop_critical": {
                "priority": 1,
                "threshold": 40.0,
                "actions": [ActionType.REDUCE_BUDGET, ActionType.TRIGGER_CREATIVE_RESYNC],
                "reasoning": "Critical CTR drop detected - reducing budget and triggering creative refresh",
            },
            "ctr_drop_high": {
                "priority": 2,
                "threshold": 30.0,
                "actions": [ActionType.REDUCE_BUDGET],
                "reasoning": "High CTR drop - reducing budget by 20-30%",
            },
            "ctr_drop_moderate": {
                "priority": 3,
                "threshold": 25.0,
                "actions": [ActionType.REDUCE_BUDGET],
                "reasoning": "Moderate CTR drop - reducing budget by 10-20%",
            },
            "cvr_drop_critical": {
                "priority": 1,
                "threshold": 35.0,
                "actions": [ActionType.PAUSE_ADSET, ActionType.TRIGGER_FULL_CYCLE],
                "reasoning": "Critical CVR drop - pausing adset and triggering full optimization cycle",
            },
            "cvr_drop_high": {
                "priority": 2,
                "threshold": 25.0,
                "actions": [ActionType.REDUCE_BUDGET, ActionType.TRIGGER_TARGETING_REFRESH],
                "reasoning": "High CVR drop - reducing budget and refreshing targeting",
            },
            "roas_collapse": {
                "priority": 1,
                "threshold": 30.0,
                "actions": [ActionType.PAUSE_CAMPAIGN, ActionType.TRIGGER_FULL_CYCLE],
                "reasoning": "ROAS collapse detected - pausing campaign preventively and triggering full cycle",
            },
            "cpm_spike_critical": {
                "priority": 2,
                "threshold": 60.0,
                "actions": [ActionType.RESET_BID, ActionType.REDUCE_BUDGET],
                "reasoning": "Critical CPM spike - resetting bid strategy and reducing budget",
            },
            "cpm_spike_high": {
                "priority": 3,
                "threshold": 40.0,
                "actions": [ActionType.RESET_BID],
                "reasoning": "High CPM spike - resetting bid to optimize costs",
            },
            "frequency_saturation": {
                "priority": 2,
                "threshold": 6.0,
                "actions": [ActionType.TRIGGER_TARGETING_REFRESH, ActionType.REDUCE_BUDGET],
                "reasoning": "Frequency saturation - refreshing targeting to reach new audience",
            },
        }
    
    
    async def make_decision(
        self,
        detection_result: DetectionResult,
    ) -> RealTimeDecision:
        """
        Make real-time decision based on detection results.
        
        Args:
            detection_result: Detection result from RealTimeDetector
        
        Returns:
            RealTimeDecision with recommended actions and reasoning
        """
        if self.mode == "stub":
            return await self._make_decision_stub(detection_result)
        else:
            return await self._make_decision_live(detection_result)
    
    
    async def _make_decision_stub(
        self,
        detection_result: DetectionResult,
    ) -> RealTimeDecision:
        """
        STUB mode: Generate synthetic decision.
        """
        rules_triggered: List[DecisionRule] = []
        recommended_actions: List[ActionType] = []
        reasoning_parts: List[str] = []
        
        # Analyze each anomaly and apply rules
        for anomaly in detection_result.anomalies:
            rule_match = self._match_rule(anomaly)
            
            if rule_match:
                rules_triggered.append(rule_match["rule"])
                
                # Add actions (avoid duplicates)
                for action in rule_match["actions"]:
                    if action not in recommended_actions:
                        recommended_actions.append(action)
                
                reasoning_parts.append(rule_match["reasoning"])
        
        # If no rules triggered but has anomalies, add alert-only action
        if not recommended_actions and detection_result.anomalies:
            recommended_actions.append(ActionType.ALERT_ONLY)
            reasoning_parts.append("Anomalies detected but below action thresholds - monitoring only")
        
        # Determine urgency from severity
        urgency = self._determine_urgency(detection_result)
        
        # Determine if should auto-apply
        should_auto_apply = urgency in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        
        # Build final reasoning
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No critical issues detected"
        
        # Estimate impact
        estimated_impact = {
            "budget_change_pct": -20 if ActionType.REDUCE_BUDGET in recommended_actions else 0,
            "will_pause": any(a in recommended_actions for a in [ActionType.PAUSE_AD, ActionType.PAUSE_ADSET, ActionType.PAUSE_CAMPAIGN]),
            "will_trigger_optimization": any(a in recommended_actions for a in [ActionType.TRIGGER_FULL_CYCLE, ActionType.TRIGGER_TARGETING_REFRESH, ActionType.TRIGGER_CREATIVE_RESYNC]),
        }
        
        return RealTimeDecision(
            decision_id=uuid.uuid4(),
            campaign_id=detection_result.campaign_id,
            detection_result_id=detection_result.snapshot_id,
            recommended_actions=recommended_actions,
            rules_triggered=rules_triggered,
            reasoning=reasoning,
            urgency=urgency,
            should_auto_apply=should_auto_apply,
            estimated_impact=estimated_impact,
            created_at=datetime.utcnow(),
        )
    
    
    async def _make_decision_live(
        self,
        detection_result: DetectionResult,
    ) -> RealTimeDecision:
        """
        LIVE mode: Same logic as stub (fully implemented).
        """
        return await self._make_decision_stub(detection_result)
    
    
    def _match_rule(self, anomaly) -> Dict[str, Any]:
        """
        Match anomaly to decision rules.
        
        Returns dict with rule, actions, and reasoning or None if no match.
        """
        # Map anomaly types to rule prefixes
        rule_mapping = {
            AnomalyType.CTR_DROP: "ctr_drop",
            AnomalyType.CVR_DROP: "cvr_drop",
            AnomalyType.ROAS_COLLAPSE: "roas_collapse",
            AnomalyType.CPM_SPIKE: "cpm_spike",
            AnomalyType.FREQUENCY_SPIKE: "frequency_saturation",
        }
        
        rule_prefix = rule_mapping.get(anomaly.anomaly_type)
        if not rule_prefix:
            return None
        
        # Match severity to rule
        if anomaly.severity == SeverityLevel.CRITICAL:
            rule_key = f"{rule_prefix}_critical"
        elif anomaly.severity == SeverityLevel.HIGH:
            rule_key = f"{rule_prefix}_high"
        elif anomaly.severity == SeverityLevel.MODERATE:
            rule_key = f"{rule_prefix}_moderate"
        else:
            return None
        
        # Get rule config (fallback to base rule if specific severity not found)
        rule_config = self.rules.get(rule_key) or self.rules.get(rule_prefix)
        
        if not rule_config:
            return None
        
        # Build DecisionRule
        decision_rule = DecisionRule(
            rule_id=rule_key,
            rule_name=rule_key.replace("_", " ").title(),
            condition=anomaly.description,
            threshold=rule_config.get("threshold", anomaly.threshold_violated),
            actual_value=anomaly.current_value,
            matched=True,
            priority=rule_config.get("priority", 5),
        )
        
        return {
            "rule": decision_rule,
            "actions": rule_config["actions"],
            "reasoning": rule_config["reasoning"],
        }
    
    
    def _determine_urgency(self, detection_result: DetectionResult) -> SeverityLevel:
        """
        Determine overall urgency from detection result.
        """
        if detection_result.has_critical_issues or detection_result.critical_count > 0:
            return SeverityLevel.CRITICAL
        elif detection_result.high_count > 0:
            return SeverityLevel.HIGH
        elif detection_result.moderate_count > 0:
            return SeverityLevel.MODERATE
        else:
            return SeverityLevel.LOW
