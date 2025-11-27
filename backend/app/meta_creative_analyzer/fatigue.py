"""Fatigue Detector (PASO 10.15)"""
import uuid, random
from datetime import datetime, timedelta
from uuid import UUID
from typing import List
from app.meta_creative_analyzer.schemas import (
    FatigueSignal, FatigueDetectionResult, CreativePerformanceMetrics
)

class FatigueDetector:
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def detect_fatigue(
        self, creative_id: UUID, current_metrics: CreativePerformanceMetrics,
        days_active: int = 14, impressions_total: int = 50000
    ) -> FatigueDetectionResult:
        """Detect creative fatigue. Fatigue if CTR/CVR drops ≥30% vs baseline."""
        if self.mode == "stub":
            return await self._detect_fatigue_stub(creative_id, current_metrics, days_active, impressions_total)
        # TODO LIVE: Query baseline from MetaInsightsCollector (PASO 10.7)
        raise NotImplementedError("LIVE mode requires MetaInsightsCollector integration")
    
    async def _detect_fatigue_stub(
        self, creative_id: UUID, current_metrics: CreativePerformanceMetrics,
        days_active: int, impressions_total: int
    ) -> FatigueDetectionResult:
        """Stub fatigue detection with synthetic baselines."""
        signals = []
        
        # Simulate baseline (7-14 days ago)
        baseline_ctr = current_metrics.ctr * random.uniform(1.2, 1.8)
        baseline_cvr = current_metrics.cvr * random.uniform(1.15, 1.6)
        baseline_roas = current_metrics.roas * random.uniform(1.1, 1.4)
        baseline_eng = current_metrics.engagement_rate * random.uniform(1.1, 1.5)
        
        # CTR drop
        ctr_drop = ((baseline_ctr - current_metrics.ctr) / baseline_ctr) * 100 if baseline_ctr > 0 else 0
        if ctr_drop >= 30:
            signals.append(FatigueSignal(
                metric="ctr", baseline_value=baseline_ctr, current_value=current_metrics.ctr,
                drop_pct=ctr_drop, is_significant=True
            ))
        
        # CVR drop
        cvr_drop = ((baseline_cvr - current_metrics.cvr) / baseline_cvr) * 100 if baseline_cvr > 0 else 0
        if cvr_drop >= 30:
            signals.append(FatigueSignal(
                metric="cvr", baseline_value=baseline_cvr, current_value=current_metrics.cvr,
                drop_pct=cvr_drop, is_significant=True
            ))
        
        # Calculate fatigue score (0-100)
        fatigue_score = self._calculate_fatigue_score(signals, days_active, impressions_total)
        
        # Determine level and recommendation
        is_fatigued, level, recommendation, urgency = self._classify_fatigue(fatigue_score, signals)
        
        return FatigueDetectionResult(
            creative_id=creative_id, is_fatigued=is_fatigued, fatigue_score=fatigue_score,
            fatigue_level=level, signals=signals, days_active=days_active,
            impressions_total=impressions_total, recommendation=recommendation, urgency=urgency
        )
    
    def _calculate_fatigue_score(self, signals: List[FatigueSignal], days: int, imps: int) -> float:
        """Calculate 0-100 fatigue score."""
        score = 0.0
        for sig in signals:
            if sig.metric == "ctr":
                score += min(40.0, sig.drop_pct * 0.8)
            elif sig.metric == "cvr":
                score += min(30.0, sig.drop_pct * 0.6)
        if days > 30: score += 15.0
        if imps > 100000: score += 10.0
        return min(100.0, score)
    
    def _classify_fatigue(self, score: float, signals: List[FatigueSignal]):
        """Classify fatigue level and generate recommendation."""
        if score < 30:
            return False, "healthy", "Creative is healthy. Continue monitoring.", "low"
        elif score < 50:
            return True, "mild", "Mild fatigue detected. Consider generating variants.", "medium"
        elif score < 70:
            return True, "moderate", "Moderate fatigue. Refresh creative strongly recommended.", "high"
        elif score < 85:
            return True, "severe", "Severe fatigue. Immediate creative refresh required.", "high"
        else:
            return True, "critical", "Critical fatigue. Pause or replace creative immediately.", "critical"
