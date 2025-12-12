"""
Sprint 15: Decision Policy Engine - Policy Learning & Feedback

Adaptive learning system that tracks policy performance and automatically
adjusts policy ranking, degrades toxic policies, and reinforces successful ones.

Author: STAKAZO Project
Date: 2025-12-12
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import defaultdict
from enum import Enum

from .decision_policy_models import Policy, SuccessSignal


class PerformanceRating(Enum):
    """Policy performance ratings"""
    EXCELLENT = "excellent"  # Success rate > 80%, positive metrics
    GOOD = "good"  # Success rate 60-80%
    ACCEPTABLE = "acceptable"  # Success rate 40-60%
    POOR = "poor"  # Success rate 20-40%
    TOXIC = "toxic"  # Success rate < 20% or negative metrics


@dataclass
class PolicyOutcome:
    """Record of a single policy execution outcome"""
    policy_id: str
    timestamp: datetime
    success: bool
    success_signals_met: List[str]
    metrics: Dict[str, float]  # velocity_lift, risk_delta, engagement_change, etc.
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'success_signals_met': self.success_signals_met,
            'metrics': self.metrics,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyOutcome':
        return cls(
            policy_id=data['policy_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            success=data['success'],
            success_signals_met=data['success_signals_met'],
            metrics=data['metrics'],
            context=data['context']
        )


@dataclass
class PolicyPerformance:
    """Aggregated performance metrics for a policy"""
    policy_id: str
    total_executions: int
    success_count: int
    failure_count: int
    success_rate: float
    average_velocity_lift: float
    average_risk_delta: float
    average_engagement_change: float
    performance_rating: PerformanceRating
    confidence_adjustment: float  # Multiplier for policy confidence (0.5-1.5)
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'total_executions': self.total_executions,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'average_velocity_lift': self.average_velocity_lift,
            'average_risk_delta': self.average_risk_delta,
            'average_engagement_change': self.average_engagement_change,
            'performance_rating': self.performance_rating.value,
            'confidence_adjustment': self.confidence_adjustment,
            'last_updated': self.last_updated.isoformat()
        }


class PolicyLearningFeedback:
    """
    Learning system that tracks policy performance and adapts policy selection.
    
    Features:
    - Log policy execution outcomes
    - Calculate performance metrics
    - Adjust policy confidence based on results
    - Auto-degrade toxic policies
    - Reinforce successful policies
    - Provide performance insights
    """
    
    def __init__(self, storage_path: str = "storage/policy_learning"):
        """
        Initialize learning system.
        
        Args:
            storage_path: Path for storing learning data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Outcome tracking
        self._outcomes: Dict[str, List[PolicyOutcome]] = defaultdict(list)
        self._performance_cache: Dict[str, PolicyPerformance] = {}
        
        # Load existing data
        self._load_outcomes()
    
    def _load_outcomes(self):
        """Load historical outcomes from storage"""
        outcomes_file = self.storage_path / "policy_outcomes.jsonl"
        
        if not outcomes_file.exists():
            return
        
        try:
            with open(outcomes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        outcome = PolicyOutcome.from_dict(data)
                        self._outcomes[outcome.policy_id].append(outcome)
        
        except Exception as e:
            print(f"Warning: Failed to load outcomes: {e}")
    
    def log_outcome(
        self,
        policy_id: str,
        success: bool,
        success_signals_met: List[SuccessSignal],
        metrics: Dict[str, float],
        context: Dict[str, Any]
    ):
        """
        Log a policy execution outcome.
        
        Args:
            policy_id: Policy that was executed
            success: Whether execution succeeded
            success_signals_met: Which success signals were achieved
            metrics: Performance metrics (velocity_lift, risk_delta, etc.)
            context: Execution context
        """
        outcome = PolicyOutcome(
            policy_id=policy_id,
            timestamp=datetime.now(),
            success=success,
            success_signals_met=[s.value for s in success_signals_met],
            metrics=metrics,
            context=context
        )
        
        # Add to memory
        self._outcomes[policy_id].append(outcome)
        
        # Persist to storage
        outcomes_file = self.storage_path / "policy_outcomes.jsonl"
        with open(outcomes_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(outcome.to_dict()) + '\n')
        
        # Update performance cache
        self._update_performance(policy_id)
        
        # Check for toxic policy
        performance = self._performance_cache.get(policy_id)
        if performance and performance.performance_rating == PerformanceRating.TOXIC:
            print(f"⚠️ WARNING: Policy {policy_id} is TOXIC (success rate: {performance.success_rate:.1%})")
    
    def _update_performance(self, policy_id: str):
        """Recalculate performance metrics for a policy"""
        outcomes = self._outcomes.get(policy_id, [])
        
        if not outcomes:
            return
        
        # Calculate basic metrics
        total = len(outcomes)
        success_count = sum(1 for o in outcomes if o.success)
        failure_count = total - success_count
        success_rate = success_count / total if total > 0 else 0
        
        # Calculate average metric changes
        velocity_lifts = [o.metrics.get('velocity_lift', 0) for o in outcomes if o.success]
        risk_deltas = [o.metrics.get('risk_delta', 0) for o in outcomes]
        engagement_changes = [o.metrics.get('engagement_change', 0) for o in outcomes if o.success]
        
        avg_velocity_lift = sum(velocity_lifts) / len(velocity_lifts) if velocity_lifts else 0
        avg_risk_delta = sum(risk_deltas) / len(risk_deltas) if risk_deltas else 0
        avg_engagement_change = sum(engagement_changes) / len(engagement_changes) if engagement_changes else 0
        
        # Determine performance rating
        rating = self._calculate_performance_rating(
            success_rate,
            avg_velocity_lift,
            avg_risk_delta,
            avg_engagement_change
        )
        
        # Calculate confidence adjustment
        confidence_adjustment = self._calculate_confidence_adjustment(
            rating,
            success_rate,
            avg_velocity_lift
        )
        
        # Create performance record
        performance = PolicyPerformance(
            policy_id=policy_id,
            total_executions=total,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            average_velocity_lift=avg_velocity_lift,
            average_risk_delta=avg_risk_delta,
            average_engagement_change=avg_engagement_change,
            performance_rating=rating,
            confidence_adjustment=confidence_adjustment,
            last_updated=datetime.now()
        )
        
        self._performance_cache[policy_id] = performance
    
    def _calculate_performance_rating(
        self,
        success_rate: float,
        avg_velocity_lift: float,
        avg_risk_delta: float,
        avg_engagement_change: float
    ) -> PerformanceRating:
        """Calculate overall performance rating"""
        # Check for toxic indicators
        if success_rate < 0.2 or avg_risk_delta > 0.3 or avg_engagement_change < -0.3:
            return PerformanceRating.TOXIC
        
        # Excellent performance
        if success_rate > 0.8 and avg_velocity_lift > 0.1 and avg_risk_delta < 0:
            return PerformanceRating.EXCELLENT
        
        # Good performance
        if success_rate > 0.6 and avg_velocity_lift > 0:
            return PerformanceRating.GOOD
        
        # Acceptable performance
        if success_rate > 0.4:
            return PerformanceRating.ACCEPTABLE
        
        # Poor performance
        return PerformanceRating.POOR
    
    def _calculate_confidence_adjustment(
        self,
        rating: PerformanceRating,
        success_rate: float,
        avg_velocity_lift: float
    ) -> float:
        """
        Calculate confidence multiplier based on performance.
        
        Returns:
            Multiplier between 0.5 (toxic) and 1.5 (excellent)
        """
        if rating == PerformanceRating.EXCELLENT:
            return 1.3 + min(0.2, avg_velocity_lift)  # 1.3-1.5
        
        elif rating == PerformanceRating.GOOD:
            return 1.1 + (success_rate - 0.6) * 0.5  # 1.1-1.2
        
        elif rating == PerformanceRating.ACCEPTABLE:
            return 1.0  # No adjustment
        
        elif rating == PerformanceRating.POOR:
            return 0.8 - (0.4 - success_rate) * 0.5  # 0.7-0.8
        
        else:  # TOXIC
            return 0.5  # Significant degradation
    
    def get_performance(self, policy_id: str) -> Optional[PolicyPerformance]:
        """
        Get performance metrics for a policy.
        
        Args:
            policy_id: Policy to get performance for
        
        Returns:
            PolicyPerformance or None if no data
        """
        if policy_id not in self._performance_cache:
            self._update_performance(policy_id)
        
        return self._performance_cache.get(policy_id)
    
    def get_adjusted_confidence(
        self,
        policy: Policy
    ) -> float:
        """
        Get confidence weight adjusted by learning.
        
        Args:
            policy: Policy to get adjusted confidence for
        
        Returns:
            Adjusted confidence (original * adjustment)
        """
        performance = self.get_performance(policy.policy_id)
        
        if not performance:
            return policy.confidence_weight
        
        adjusted = policy.confidence_weight * performance.confidence_adjustment
        
        return max(0.1, min(1.0, adjusted))  # Clamp to 0.1-1.0
    
    def is_policy_toxic(self, policy_id: str) -> bool:
        """
        Check if policy is toxic and should be disabled.
        
        Args:
            policy_id: Policy to check
        
        Returns:
            True if toxic, False otherwise
        """
        performance = self.get_performance(policy_id)
        
        if not performance:
            return False
        
        return performance.performance_rating == PerformanceRating.TOXIC
    
    def get_toxic_policies(self) -> List[str]:
        """
        Get list of toxic policy IDs.
        
        Returns:
            List of toxic policy IDs
        """
        toxic = []
        
        for policy_id in self._outcomes.keys():
            if self.is_policy_toxic(policy_id):
                toxic.append(policy_id)
        
        return toxic
    
    def get_top_performing_policies(
        self,
        n: int = 5,
        min_executions: int = 3
    ) -> List[PolicyPerformance]:
        """
        Get top N performing policies.
        
        Args:
            n: Number of policies to return
            min_executions: Minimum executions required
        
        Returns:
            List of top PolicyPerformance records
        """
        # Update all performances
        for policy_id in self._outcomes.keys():
            if policy_id not in self._performance_cache:
                self._update_performance(policy_id)
        
        # Filter by minimum executions
        candidates = [
            perf for perf in self._performance_cache.values()
            if perf.total_executions >= min_executions
        ]
        
        # Sort by success rate
        candidates.sort(key=lambda p: p.success_rate, reverse=True)
        
        return candidates[:n]
    
    def get_policy_insights(
        self,
        policy_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed insights for a policy.
        
        Args:
            policy_id: Policy to analyze
        
        Returns:
            Dictionary with insights
        """
        performance = self.get_performance(policy_id)
        
        if not performance:
            return {'error': 'No data available for this policy'}
        
        outcomes = self._outcomes.get(policy_id, [])
        recent_outcomes = outcomes[-10:] if len(outcomes) > 10 else outcomes
        
        insights = {
            'policy_id': policy_id,
            'performance': performance.to_dict(),
            'recent_success_rate': sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes) if recent_outcomes else 0,
            'trend': self._calculate_trend(policy_id),
            'recommendations': self._generate_recommendations(performance)
        }
        
        return insights
    
    def _calculate_trend(self, policy_id: str) -> str:
        """Calculate performance trend (improving/declining/stable)"""
        outcomes = self._outcomes.get(policy_id, [])
        
        if len(outcomes) < 10:
            return "insufficient_data"
        
        # Compare recent vs older success rates
        recent = outcomes[-10:]
        older = outcomes[-20:-10] if len(outcomes) >= 20 else outcomes[:-10]
        
        recent_rate = sum(1 for o in recent if o.success) / len(recent)
        older_rate = sum(1 for o in older if o.success) / len(older)
        
        diff = recent_rate - older_rate
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(
        self,
        performance: PolicyPerformance
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if performance.performance_rating == PerformanceRating.TOXIC:
            recommendations.append("🚫 DISABLE THIS POLICY IMMEDIATELY - Toxic performance")
            recommendations.append("Review policy conditions and adjust thresholds")
        
        elif performance.performance_rating == PerformanceRating.POOR:
            recommendations.append("⚠️ Consider disabling or revising this policy")
            recommendations.append("Analyze failure patterns to identify issues")
        
        elif performance.performance_rating == PerformanceRating.EXCELLENT:
            recommendations.append("✅ Excellent performance - consider increasing confidence weight")
            recommendations.append("Use as template for similar policies")
        
        if performance.average_risk_delta > 0.1:
            recommendations.append("⚠️ Policy increases risk - tighten risk constraints")
        
        if performance.average_velocity_lift < 0:
            recommendations.append("⚠️ Policy decreases velocity - review effectiveness")
        
        return recommendations
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall learning system statistics"""
        total_policies = len(self._outcomes)
        total_outcomes = sum(len(outcomes) for outcomes in self._outcomes.values())
        
        rating_counts = defaultdict(int)
        for perf in self._performance_cache.values():
            rating_counts[perf.performance_rating.value] += 1
        
        return {
            'total_policies_tracked': total_policies,
            'total_outcomes_logged': total_outcomes,
            'performance_distribution': dict(rating_counts),
            'toxic_policies': len(self.get_toxic_policies()),
            'policies_with_data': len(self._performance_cache)
        }


if __name__ == "__main__":
    # Example usage
    from decision_policy_models import SuccessSignal
    
    learning = PolicyLearningFeedback()
    
    # Log some outcomes
    policy_id = "YT_BREAKOUT_SUPPORT_v1.3"
    
    for i in range(10):
        success = i % 3 != 0  # 67% success rate
        
        learning.log_outcome(
            policy_id=policy_id,
            success=success,
            success_signals_met=[SuccessSignal.VELOCITY_INCREASE] if success else [],
            metrics={
                'velocity_lift': 0.15 if success else -0.05,
                'risk_delta': -0.02 if success else 0.05,
                'engagement_change': 0.1 if success else -0.1
            },
            context={'platform': 'youtube'}
        )
    
    # Get performance
    performance = learning.get_performance(policy_id)
    if performance:
        print(f"✓ Policy performance:")
        print(f"  Success rate: {performance.success_rate:.1%}")
        print(f"  Rating: {performance.performance_rating.value}")
        print(f"  Confidence adjustment: {performance.confidence_adjustment:.2f}x")
    
    # Get insights
    insights = learning.get_policy_insights(policy_id)
    print(f"\n✓ Policy insights:")
    print(f"  Trend: {insights['trend']}")
    print(f"  Recommendations: {len(insights['recommendations'])}")
