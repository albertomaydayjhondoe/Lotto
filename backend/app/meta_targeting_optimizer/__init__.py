"""
Meta Ads Autonomous Targeting Optimizer (PASO 10.12)

Motor de optimización autónoma de targeting usando datos históricos,
insights, píxeles y señales de rendimiento con aprendizaje continuo.
"""

from app.meta_targeting_optimizer.models import (
    MetaTargetingRecommendationModel,
    MetaTargetingHistoryModel,
    MetaTargetingSegmentScoreModel,
)
from app.meta_targeting_optimizer.optimizer import MetaTargetingOptimizer

__all__ = [
    "MetaTargetingRecommendationModel",
    "MetaTargetingHistoryModel",
    "MetaTargetingSegmentScoreModel",
    "MetaTargetingOptimizer",
]
