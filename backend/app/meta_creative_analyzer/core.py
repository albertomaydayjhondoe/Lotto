"""
Creative Intelligence Core (PASO 10.15)

Analiza señales de rendimiento y calcula scoring unificado.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from app.meta_creative_analyzer.schemas import (
    CreativePerformanceMetrics,
    CreativeScore,
)


class CreativeIntelligenceCore:
    """
    Core intelligence for creative analysis and scoring.
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def calculate_creative_score(
        self,
        metrics: CreativePerformanceMetrics,
        fatigue_penalty: float = 0.0
    ) -> CreativeScore:
        """
        Calculate unified creative score based on performance metrics.
        
        Score components:
        - Performance (40%): CTR, CVR, ROAS
        - Engagement (30%): Engagement rate, clicks
        - Completion (20%): Video completion rates
        - Efficiency (10%): CPC, CPM
        - Fatigue penalty (0-50 points)
        """
        
        # Performance score (40 points max)
        perf_score = self._calculate_performance_score(metrics)
        
        # Engagement score (30 points max)
        eng_score = self._calculate_engagement_score(metrics)
        
        # Completion score (20 points max) - only if video
        comp_score = self._calculate_completion_score(metrics)
        
        # Efficiency score (10 points max)
        eff_score = self._calculate_efficiency_score(metrics)
        
        # Overall score (0-100) minus fatigue penalty
        overall = perf_score + eng_score + comp_score + eff_score - fatigue_penalty
        overall = max(0.0, min(100.0, overall))
        
        # Reasoning
        reasoning = self._generate_score_reasoning(
            overall, perf_score, eng_score, comp_score, eff_score, fatigue_penalty
        )
        
        return CreativeScore(
            overall_score=round(overall, 2),
            performance_score=round(perf_score, 2),
            engagement_score=round(eng_score, 2),
            completion_score=round(comp_score, 2) if comp_score else None,
            fatigue_penalty=round(fatigue_penalty, 2),
            components={
                "performance": round(perf_score, 2),
                "engagement": round(eng_score, 2),
                "completion": round(comp_score, 2),
                "efficiency": round(eff_score, 2),
            },
            reasoning=reasoning
        )
    
    def _calculate_performance_score(self, metrics: CreativePerformanceMetrics) -> float:
        """Calculate performance component (40 points max)."""
        # CTR: 0-5% → 0-15 points
        ctr_score = min(15.0, (metrics.ctr / 5.0) * 15.0)
        
        # CVR: 0-8% → 0-15 points
        cvr_score = min(15.0, (metrics.cvr / 8.0) * 15.0)
        
        # ROAS: 0-5 → 0-10 points
        roas_score = min(10.0, (metrics.roas / 5.0) * 10.0)
        
        return ctr_score + cvr_score + roas_score
    
    def _calculate_engagement_score(self, metrics: CreativePerformanceMetrics) -> float:
        """Calculate engagement component (30 points max)."""
        # Engagement rate: 0-10% → 0-20 points
        eng_rate_score = min(20.0, (metrics.engagement_rate / 10.0) * 20.0)
        
        # Volume bonus: impressions ≥10K → +10 points
        volume_bonus = min(10.0, (metrics.impressions / 10000) * 10.0)
        
        return eng_rate_score + volume_bonus
    
    def _calculate_completion_score(self, metrics: CreativePerformanceMetrics) -> float:
        """Calculate video completion component (20 points max)."""
        if not metrics.video_3s:
            return 10.0  # Default for non-video
        
        # Weighted completion: 3s (5), 25% (5), 50% (5), 100% (5)
        score = 0.0
        score += (metrics.video_3s or 0) * 0.05  # 5 points max
        score += (metrics.video_25pct or 0) * 0.05  # 5 points max
        score += (metrics.video_50pct or 0) * 0.05  # 5 points max
        score += (metrics.video_100pct or 0) * 0.05  # 5 points max
        
        return min(20.0, score)
    
    def _calculate_efficiency_score(self, metrics: CreativePerformanceMetrics) -> float:
        """Calculate efficiency component (10 points max)."""
        # CPC: lower is better, $0-5 → 10-0 points
        cpc_score = max(0.0, 5.0 - min(5.0, (metrics.cpc / 5.0) * 5.0))
        
        # CPM: lower is better, $0-50 → 5-0 points
        cpm_score = max(0.0, 5.0 - min(5.0, (metrics.cpm / 50.0) * 5.0))
        
        return cpc_score + cpm_score
    
    def _generate_score_reasoning(
        self,
        overall: float,
        perf: float,
        eng: float,
        comp: float,
        eff: float,
        fatigue: float
    ) -> str:
        """Generate human-readable reasoning for score."""
        level = "Excellent" if overall >= 80 else "Good" if overall >= 60 else "Fair" if overall >= 40 else "Poor"
        
        reasoning = f"{level} creative with overall score {overall:.1f}/100. "
        reasoning += f"Performance: {perf:.1f}/40, "
        reasoning += f"Engagement: {eng:.1f}/30, "
        reasoning += f"Completion: {comp:.1f}/20, "
        reasoning += f"Efficiency: {eff:.1f}/10. "
        
        if fatigue > 0:
            reasoning += f"Fatigue penalty: -{fatigue:.1f} points. "
        
        return reasoning
