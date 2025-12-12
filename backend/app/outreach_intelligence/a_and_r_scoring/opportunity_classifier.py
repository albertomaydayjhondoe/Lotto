"""
A&R Scoring — Opportunity Classifier

Classifies opportunities based on strategic value and resource allocation.

STUB MODE: Returns mock classifications.
"""

from typing import Dict, Any, List
from enum import Enum


class OpportunityTier(Enum):
    """Opportunity tier classification"""
    TIER_1_PRIORITY = "tier_1_priority"  # Must pursue
    TIER_2_STRONG = "tier_2_strong"  # Should pursue
    TIER_3_MODERATE = "tier_3_moderate"  # Consider if capacity
    TIER_4_LOW = "tier_4_low"  # Only if automated


class OpportunityClassifier:
    """
    STUB: Classifies and prioritizes opportunities.
    
    Phase 4: Mock classification.
    """
    
    def __init__(self):
        self.stub_mode = True
        
    def classify_opportunity(
        self,
        opportunity: Dict[str, Any],
        track_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Classify single opportunity.
        
        Returns:
            Classification with tier and reasoning
        """
        # STUB: Simple scoring
        reach = opportunity.get("follower_count", 1000)
        confidence = opportunity.get("confidence_score", 0.5)
        track_quality = track_score.get("overall_hit_score", 70) / 100
        
        composite_score = (reach / 100000 * 0.4 + confidence * 0.3 + track_quality * 0.3)
        
        if composite_score >= 0.80:
            tier = OpportunityTier.TIER_1_PRIORITY
        elif composite_score >= 0.65:
            tier = OpportunityTier.TIER_2_STRONG
        elif composite_score >= 0.45:
            tier = OpportunityTier.TIER_3_MODERATE
        else:
            tier = OpportunityTier.TIER_4_LOW
        
        return {
            "opportunity_id": opportunity.get("playlist_id", "opp_001"),
            "tier": tier.value,
            "composite_score": round(composite_score, 3),
            "recommendation": "pursue" if composite_score >= 0.65 else "consider",
            "effort_required": "low" if tier == OpportunityTier.TIER_1_PRIORITY else "medium",
            "stub_note": "STUB MODE"
        }
    
    def batch_classify(
        self,
        opportunities: List[Dict[str, Any]],
        track_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Classify all opportunities and group by tier.
        
        Returns:
            Classified opportunities grouped by tier
        """
        classified = [
            self.classify_opportunity(opp, track_score)
            for opp in opportunities
        ]
        
        grouped = {
            "tier_1": [c for c in classified if c["tier"] == OpportunityTier.TIER_1_PRIORITY.value],
            "tier_2": [c for c in classified if c["tier"] == OpportunityTier.TIER_2_STRONG.value],
            "tier_3": [c for c in classified if c["tier"] == OpportunityTier.TIER_3_MODERATE.value],
            "tier_4": [c for c in classified if c["tier"] == OpportunityTier.TIER_4_LOW.value]
        }
        
        return {
            "total_opportunities": len(classified),
            "grouped_by_tier": grouped,
            "summary": {
                "tier_1_count": len(grouped["tier_1"]),
                "tier_2_count": len(grouped["tier_2"]),
                "tier_3_count": len(grouped["tier_3"]),
                "tier_4_count": len(grouped["tier_4"])
            },
            "stub_note": "STUB MODE"
        }
