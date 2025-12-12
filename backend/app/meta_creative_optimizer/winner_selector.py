"""Winner Selector for Creative Optimizer (PASO 10.16)"""
from datetime import datetime
from typing import List
import random

from app.meta_creative_optimizer import schemas


class WinnerSelector:
    """Selects Creative Winner of the Day"""
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
        # Weights for composite score
        self.weights = {
            "overall_score": 0.30,  # Creative analyzer score
            "roas": 0.25,  # Revenue efficiency
            "conversions": 0.20,  # Volume
            "ctr": 0.10,  # Engagement
            "cvr": 0.10,  # Conversion efficiency
            "freshness": 0.05,  # Recency bonus
        }
    
    async def select_winner(
        self, creatives: List[schemas.UnifiedCreativeData]
    ) -> schemas.WinnerSelectionResult:
        """Select winner from candidates"""
        if not creatives:
            raise ValueError("No creatives to evaluate")
        
        # Filter out fatigued and low performers
        candidates = [c for c in creatives if not c.is_fatigued and c.overall_score > 50]
        
        if not candidates:
            # Fallback: select best from all
            candidates = creatives
        
        # Calculate composite scores
        scored_candidates = []
        for creative in candidates:
            composite = self._calculate_composite_score(creative)
            confidence = self._calculate_confidence(creative)
            
            scored_candidates.append(schemas.WinnerCandidate(
                creative_id=creative.creative_id,
                overall_score=creative.overall_score,
                composite_score=composite,
                roas=creative.roas,
                ctr=creative.ctr,
                cvr=creative.cvr,
                spend=creative.spend,
                conversions=creative.conversions,
                days_active=creative.days_active,
                is_fatigued=creative.is_fatigued,
                confidence=confidence,
            ))
        
        # Sort by composite score
        scored_candidates.sort(key=lambda x: x.composite_score, reverse=True)
        
        winner = scored_candidates[0]
        runner_up = scored_candidates[1] if len(scored_candidates) > 1 else None
        
        # Determine confidence level
        confidence = self._classify_confidence(winner.confidence)
        
        reasoning = self._generate_reasoning(winner, runner_up, scored_candidates)
        
        return schemas.WinnerSelectionResult(
            winner_creative_id=winner.creative_id,
            winner_score=winner.composite_score,
            candidates_evaluated=len(scored_candidates),
            runner_up_creative_id=runner_up.creative_id if runner_up else None,
            runner_up_score=runner_up.composite_score if runner_up else None,
            confidence=confidence,
            reasoning=reasoning,
            selected_at=datetime.utcnow(),
        )
    
    def _calculate_composite_score(self, creative: schemas.UnifiedCreativeData) -> float:
        """Calculate weighted composite score"""
        # Normalize metrics to 0-100
        norm_overall = creative.overall_score
        norm_roas = min(100, creative.roas * 20)  # 5.0 ROAS = 100
        norm_conv = min(100, creative.conversions / 10)  # 1000 conversions = 100
        norm_ctr = min(100, creative.ctr * 20)  # 5% CTR = 100
        norm_cvr = min(100, creative.cvr * 12.5)  # 8% CVR = 100
        norm_fresh = max(0, 100 - creative.days_active)  # Newer = higher
        
        composite = (
            norm_overall * self.weights["overall_score"] +
            norm_roas * self.weights["roas"] +
            norm_conv * self.weights["conversions"] +
            norm_ctr * self.weights["ctr"] +
            norm_cvr * self.weights["cvr"] +
            norm_fresh * self.weights["freshness"]
        )
        
        return round(composite, 2)
    
    def _calculate_confidence(self, creative: schemas.UnifiedCreativeData) -> float:
        """Calculate confidence in creative performance"""
        # Based on volume and consistency
        volume_score = min(1.0, creative.impressions / 100000)
        conversion_score = min(1.0, creative.conversions / 500)
        score_quality = creative.overall_score / 100
        
        confidence = (volume_score * 0.4 + conversion_score * 0.3 + score_quality * 0.3)
        return round(confidence, 2)
    
    def _classify_confidence(self, confidence: float) -> schemas.DecisionConfidence:
        """Classify confidence level"""
        if confidence >= 0.8:
            return schemas.DecisionConfidence.HIGH
        elif confidence >= 0.5:
            return schemas.DecisionConfidence.MEDIUM
        else:
            return schemas.DecisionConfidence.LOW
    
    def _generate_reasoning(
        self, winner, runner_up, all_candidates
    ) -> str:
        """Generate human-readable reasoning"""
        reason = f"Selected based on composite score of {winner.composite_score:.1f}/100. "
        reason += f"Evaluated {len(all_candidates)} candidates. "
        
        if runner_up:
            margin = winner.composite_score - runner_up.composite_score
            reason += f"Margin over runner-up: {margin:.1f} points. "
        
        reason += f"ROAS: {winner.roas:.2f}, Conversions: {winner.conversions}, CTR: {winner.ctr:.2f}%."
        return reason
