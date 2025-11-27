"""
Bayesian Scoring Engine for segment performance evaluation.

Implements Bayesian smoothing with historical priors to compute reliable
scores even with limited data.
"""
import math
from typing import Dict, List
from app.meta_targeting_optimizer.schemas import SegmentMetrics, SegmentScore, SegmentType


class BayesianScoringEngine:
    """
    Bayesian scoring engine with configurable priors and weights.
    
    Weighted scoring formula:
    - CTR: 25%
    - CVR: 40%
    - ROAS: 35%
    """
    
    # Global priors (based on Meta Ads benchmarks)
    PRIOR_CTR = 0.015  # 1.5% baseline CTR
    PRIOR_CVR = 0.02   # 2% baseline CVR
    PRIOR_ROAS = 2.5   # 2.5x baseline ROAS
    
    # Prior strength (equivalent sample size)
    PRIOR_STRENGTH = 100
    
    # Weights for composite score
    WEIGHT_CTR = 0.25
    WEIGHT_CVR = 0.40
    WEIGHT_ROAS = 0.35
    
    # Minimum impressions for confidence
    MIN_IMPRESSIONS_LOW = 100
    MIN_IMPRESSIONS_MEDIUM = 500
    MIN_IMPRESSIONS_HIGH = 2000
    
    def __init__(self, prior_ctr: float = None, prior_cvr: float = None, prior_roas: float = None):
        """Initialize with optional custom priors."""
        self.prior_ctr = prior_ctr or self.PRIOR_CTR
        self.prior_cvr = prior_cvr or self.PRIOR_CVR
        self.prior_roas = prior_roas or self.PRIOR_ROAS
    
    def bayesian_smoothing(self, observed: float, prior: float, sample_size: int) -> float:
        """
        Apply Bayesian smoothing to observed metric.
        
        Formula:
        smoothed = (prior * prior_strength + observed * sample_size) / (prior_strength + sample_size)
        
        Args:
            observed: Observed metric value
            prior: Prior belief (baseline)
            sample_size: Number of samples (e.g., impressions)
        
        Returns:
            Smoothed metric value
        """
        numerator = (prior * self.PRIOR_STRENGTH) + (observed * sample_size)
        denominator = self.PRIOR_STRENGTH + sample_size
        
        if denominator == 0:
            return prior
        
        return numerator / denominator
    
    def compute_confidence(self, impressions: int) -> float:
        """
        Compute confidence score based on sample size.
        
        Returns value between 0.0 and 1.0:
        - < 100 impressions: 0.0 - 0.3 (low)
        - 100-500: 0.3 - 0.6 (medium)
        - 500-2000: 0.6 - 0.9 (high)
        - > 2000: 0.9 - 1.0 (very high)
        """
        if impressions < self.MIN_IMPRESSIONS_LOW:
            return impressions / self.MIN_IMPRESSIONS_LOW * 0.3
        elif impressions < self.MIN_IMPRESSIONS_MEDIUM:
            progress = (impressions - self.MIN_IMPRESSIONS_LOW) / (self.MIN_IMPRESSIONS_MEDIUM - self.MIN_IMPRESSIONS_LOW)
            return 0.3 + progress * 0.3
        elif impressions < self.MIN_IMPRESSIONS_HIGH:
            progress = (impressions - self.MIN_IMPRESSIONS_MEDIUM) / (self.MIN_IMPRESSIONS_HIGH - self.MIN_IMPRESSIONS_MEDIUM)
            return 0.6 + progress * 0.3
        else:
            # Cap at 0.95 to never claim 100% confidence
            excess = min(impressions - self.MIN_IMPRESSIONS_HIGH, 5000)
            return 0.9 + (excess / 5000) * 0.05
    
    def normalize_score(self, value: float, target: float, max_value: float = None) -> float:
        """
        Normalize a metric to 0-1 range for scoring.
        
        Args:
            value: Current value
            target: Target value (ideal performance)
            max_value: Maximum expected value (optional)
        
        Returns:
            Normalized score 0.0-1.0
        """
        if max_value is None:
            max_value = target * 2  # Assume 2x target is maximum
        
        if value >= max_value:
            return 1.0
        elif value <= 0:
            return 0.0
        
        # Linear normalization
        return min(value / max_value, 1.0)
    
    def compute_composite_score(
        self,
        bayesian_ctr: float,
        bayesian_cvr: float,
        bayesian_roas: float,
        confidence: float
    ) -> float:
        """
        Compute weighted composite score.
        
        Formula:
        score = (CTR_norm * 0.25 + CVR_norm * 0.40 + ROAS_norm * 0.35) * confidence
        
        Returns:
            Composite score 0.0-1.0
        """
        # Normalize each metric
        ctr_norm = self.normalize_score(bayesian_ctr, self.PRIOR_CTR, self.PRIOR_CTR * 3)
        cvr_norm = self.normalize_score(bayesian_cvr, self.PRIOR_CVR, self.PRIOR_CVR * 3)
        roas_norm = self.normalize_score(bayesian_roas, self.PRIOR_ROAS, self.PRIOR_ROAS * 2)
        
        # Weighted sum
        weighted_score = (
            ctr_norm * self.WEIGHT_CTR +
            cvr_norm * self.WEIGHT_CVR +
            roas_norm * self.WEIGHT_ROAS
        )
        
        # Apply confidence penalty
        return weighted_score * confidence
    
    def score_segment(self, metrics: SegmentMetrics, segment_id: str, segment_name: str, segment_type: SegmentType) -> SegmentScore:
        """
        Score a segment using Bayesian smoothing and weighted composite scoring.
        
        Args:
            metrics: Raw segment metrics
            segment_id: Segment identifier
            segment_name: Human-readable segment name
            segment_type: Type of segment
        
        Returns:
            SegmentScore with all computed fields
        """
        # Compute raw CTR, CVR, ROAS if not provided
        if metrics.ctr == 0.0 and metrics.clicks > 0:
            metrics.ctr = metrics.clicks / metrics.impressions if metrics.impressions > 0 else 0.0
        
        if metrics.cvr == 0.0 and metrics.conversions > 0:
            metrics.cvr = metrics.conversions / metrics.clicks if metrics.clicks > 0 else 0.0
        
        if metrics.roas == 0.0 and metrics.revenue > 0:
            metrics.roas = metrics.revenue / metrics.spend if metrics.spend > 0 else 0.0
        
        # Apply Bayesian smoothing
        bayesian_ctr = self.bayesian_smoothing(metrics.ctr, self.prior_ctr, metrics.impressions)
        bayesian_cvr = self.bayesian_smoothing(metrics.cvr, self.prior_cvr, metrics.clicks)
        bayesian_roas = self.bayesian_smoothing(metrics.roas, self.prior_roas, metrics.conversions)
        
        # Compute confidence
        confidence = self.compute_confidence(metrics.impressions)
        
        # Compute composite score
        composite_score = self.compute_composite_score(
            bayesian_ctr, bayesian_cvr, bayesian_roas, confidence
        )
        
        # Detect fatigue (CTR drops below 50% of prior)
        is_fatigued = metrics.impressions >= self.MIN_IMPRESSIONS_MEDIUM and bayesian_ctr < (self.prior_ctr * 0.5)
        
        return SegmentScore(
            segment_id=segment_id,
            segment_name=segment_name,
            segment_type=segment_type,
            metrics=metrics,
            bayesian_ctr=bayesian_ctr,
            bayesian_cvr=bayesian_cvr,
            bayesian_roas=bayesian_roas,
            composite_score=composite_score,
            confidence=confidence,
            is_fatigued=is_fatigued,
        )
    
    def rank_segments(self, scores: List[SegmentScore]) -> List[SegmentScore]:
        """
        Rank segments by composite score (descending).
        
        Filters out fatigued segments before ranking.
        
        Args:
            scores: List of SegmentScore objects
        
        Returns:
            Sorted and ranked list of SegmentScore objects
        """
        # Filter out fatigued segments
        active_scores = [s for s in scores if not s.is_fatigued]
        
        # Sort by composite score (descending)
        sorted_scores = sorted(active_scores, key=lambda s: s.composite_score, reverse=True)
        
        # Assign ranks
        for rank, score in enumerate(sorted_scores, start=1):
            score.rank = rank
        
        return sorted_scores
    
    def select_top_segments(
        self,
        scores: List[SegmentScore],
        top_n: int = 10,
        min_confidence: float = 0.3
    ) -> List[SegmentScore]:
        """
        Select top N segments with minimum confidence threshold.
        
        Args:
            scores: List of SegmentScore objects
            top_n: Number of top segments to select
            min_confidence: Minimum confidence threshold
        
        Returns:
            Top N segments meeting confidence threshold
        """
        # Rank segments
        ranked = self.rank_segments(scores)
        
        # Filter by confidence
        qualified = [s for s in ranked if s.confidence >= min_confidence]
        
        # Return top N
        return qualified[:top_n]
