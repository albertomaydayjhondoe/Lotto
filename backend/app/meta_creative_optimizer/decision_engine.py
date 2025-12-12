"""Decision Engine for Creative Optimizer (PASO 10.16)"""
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
import random

from app.meta_creative_optimizer import schemas


class CreativeDecisionEngine:
    """Makes optimization decisions for creatives"""
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def make_decisions(
        self,
        creatives: List[schemas.UnifiedCreativeData],
        winner: schemas.WinnerSelectionResult
    ) -> List[schemas.CreativeDecision]:
        """Make optimization decisions for all creatives"""
        decisions = []
        
        for creative in creatives:
            is_winner = creative.creative_id == winner.winner_creative_id
            decision = await self._decide_for_creative(creative, is_winner)
            decisions.append(decision)
        
        return decisions
    
    async def _decide_for_creative(
        self, creative: schemas.UnifiedCreativeData, is_winner: bool
    ) -> schemas.CreativeDecision:
        """Make decision for single creative"""
        # Assign role
        if is_winner:
            role = schemas.CreativeRole.WINNER
        elif creative.is_fatigued:
            role = schemas.CreativeRole.FATIGUE
        elif creative.overall_score < 50:
            role = schemas.CreativeRole.ARCHIVE
        else:
            role = schemas.CreativeRole.TEST
        
        # Determine actions
        actions = self._determine_actions(creative, role)
        
        # Calculate priority (1=highest, 5=lowest)
        priority = self._calculate_priority(creative, role, actions)
        
        # Calculate confidence
        confidence = self._calculate_confidence(creative, role)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(creative, role, actions)
        
        # Budget decisions
        budget_decision = self._decide_budget(creative, role)
        
        # Variant decisions
        variant_decision = self._decide_variants(creative, role)
        
        return schemas.CreativeDecision(
            creative_id=creative.creative_id,
            assigned_role=role,
            previous_role=schemas.CreativeRole.PENDING,  # TODO: Query from DB
            recommended_actions=actions,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning,
            estimated_impact=self._estimate_impact(creative, actions),
            current_budget=budget_decision.get("current"),
            recommended_budget=budget_decision.get("recommended"),
            budget_change_pct=budget_decision.get("change_pct"),
            should_generate_variants=variant_decision["generate"],
            variant_strategy=variant_decision.get("strategy"),
            should_recombine=variant_decision["recombine"],
            decided_at=datetime.utcnow(),
        )
    
    def _determine_actions(
        self, creative: schemas.UnifiedCreativeData, role: schemas.CreativeRole
    ) -> List[schemas.OptimizationAction]:
        """Determine recommended actions"""
        actions = []
        
        if role == schemas.CreativeRole.WINNER:
            actions.append(schemas.OptimizationAction.PROMOTE)
            if creative.roas > 4.0:
                actions.append(schemas.OptimizationAction.SCALE_BUDGET)
        
        elif role == schemas.CreativeRole.FATIGUE:
            if creative.overall_score > 40:
                actions.append(schemas.OptimizationAction.GENERATE_VARIANTS)
                actions.append(schemas.OptimizationAction.RECOMBINE)
            else:
                actions.append(schemas.OptimizationAction.PAUSE)
        
        elif role == schemas.CreativeRole.ARCHIVE:
            actions.append(schemas.OptimizationAction.ARCHIVE)
            actions.append(schemas.OptimizationAction.REDUCE_BUDGET)
        
        elif role == schemas.CreativeRole.TEST:
            if creative.roas > 3.0 and creative.overall_score > 70:
                actions.append(schemas.OptimizationAction.SCALE_BUDGET)
        
        if not actions:
            actions.append(schemas.OptimizationAction.NO_ACTION)
        
        return actions
    
    def _calculate_priority(
        self, creative, role, actions
    ) -> int:
        """Calculate priority (1=highest, 5=lowest)"""
        if role == schemas.CreativeRole.WINNER:
            return 1
        elif schemas.OptimizationAction.PAUSE in actions:
            return 2
        elif schemas.OptimizationAction.GENERATE_VARIANTS in actions:
            return 2
        elif schemas.OptimizationAction.SCALE_BUDGET in actions:
            return 3
        else:
            return 4
    
    def _calculate_confidence(
        self, creative, role
    ) -> schemas.DecisionConfidence:
        """Calculate decision confidence"""
        if creative.impressions > 100000 and creative.conversions > 300:
            return schemas.DecisionConfidence.HIGH
        elif creative.impressions > 50000 and creative.conversions > 100:
            return schemas.DecisionConfidence.MEDIUM
        else:
            return schemas.DecisionConfidence.LOW
    
    def _generate_reasoning(
        self, creative, role, actions
    ) -> str:
        """Generate reasoning for decision"""
        reason = f"Assigned role: {role.value}. "
        reason += f"Score: {creative.overall_score:.1f}, ROAS: {creative.roas:.2f}, "
        reason += f"CTR: {creative.ctr:.2f}%, CVR: {creative.cvr:.2f}%. "
        
        if creative.is_fatigued:
            reason += f"Fatigued ({creative.fatigue_level}). "
        
        reason += f"Actions: {', '.join(a.value for a in actions)}."
        return reason
    
    def _decide_budget(self, creative, role) -> dict:
        """Decide budget changes"""
        current = creative.spend
        
        if role == schemas.CreativeRole.WINNER and creative.roas > 4.0:
            recommended = current * 1.5
            change_pct = 50.0
        elif role == schemas.CreativeRole.ARCHIVE:
            recommended = current * 0.5
            change_pct = -50.0
        else:
            recommended = current
            change_pct = 0.0
        
        return {
            "current": current,
            "recommended": recommended,
            "change_pct": change_pct
        }
    
    def _decide_variants(self, creative, role) -> dict:
        """Decide variant generation"""
        if role == schemas.CreativeRole.FATIGUE and creative.overall_score > 40:
            return {
                "generate": True,
                "strategy": "balanced",
                "recombine": True
            }
        elif role == schemas.CreativeRole.WINNER and creative.days_active > 30:
            return {
                "generate": True,
                "strategy": "conservative",
                "recombine": False
            }
        else:
            return {
                "generate": False,
                "strategy": None,
                "recombine": False
            }
    
    def _estimate_impact(
        self, creative, actions
    ) -> float:
        """Estimate improvement from actions"""
        if schemas.OptimizationAction.SCALE_BUDGET in actions:
            return 30.0
        elif schemas.OptimizationAction.GENERATE_VARIANTS in actions:
            return 15.0
        elif schemas.OptimizationAction.RECOMBINE in actions:
            return 20.0
        else:
            return 0.0
