"""
Virality Predictor - Simple statistical model to predict content virality

Uses:
- Historical performance data
- Vision Engine metadata
- Engagement patterns
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging
import statistics

from ..storage.model_metrics_store import ModelMetricsStore
from ..storage.schemas_metrics import ViralityPrediction, Platform

logger = logging.getLogger(__name__)


class ViralityPredictor:
    """Predict virality score for content based on historical data."""
    
    def __init__(self, metrics_store: ModelMetricsStore):
        self.metrics_store = metrics_store
        self.model_weights = {
            "retention": 0.35,
            "engagement": 0.30,
            "quality": 0.20,
            "timing": 0.15
        }
        logger.info("ViralityPredictor initialized")
    
    async def predict_virality(
        self,
        content_id: str,
        metadata: Dict[str, Any]
    ) -> ViralityPrediction:
        """
        Predict virality score for content.
        
        Args:
            content_id: Content identifier
            metadata: Content metadata from Vision Engine
            
        Returns:
            ViralityPrediction with score and recommendations
        """
        # Extract features
        features = self._extract_features(metadata)
        
        # Calculate component scores
        retention_score = await self._predict_retention(features)
        engagement_score = await self._predict_engagement(features)
        quality_score = features.get("quality_score", 0.5)
        timing_score = self._predict_timing_score()
        
        # Weighted composite score
        virality_score = (
            retention_score * self.model_weights["retention"] +
            engagement_score * self.model_weights["engagement"] +
            quality_score * self.model_weights["quality"] +
            timing_score * self.model_weights["timing"]
        ) * 100  # Scale to 0-100
        
        # Predict views and engagement
        predicted_views = int(virality_score * 100)  # Simple heuristic
        predicted_engagement_rate = virality_score / 1000
        
        # Calculate confidence
        confidence = min(0.95, 0.5 + (virality_score / 200))
        
        # Recommendations
        boost_recommended = virality_score >= 70
        optimal_time = None  # TODO: Implement timing optimization
        platform_rec = self._recommend_platform(features)
        
        return ViralityPrediction(
            content_id=content_id,
            virality_score=virality_score,
            predicted_views=predicted_views,
            predicted_engagement_rate=predicted_engagement_rate,
            confidence=confidence,
            confidence_interval=(
                max(0, virality_score - 15),
                min(100, virality_score + 15)
            ),
            factors={
                "retention": retention_score,
                "engagement": engagement_score,
                "quality": quality_score,
                "timing": timing_score
            },
            boost_recommended=boost_recommended,
            optimal_post_time=optimal_time,
            platform_recommendation=platform_rec
        )
    
    def _extract_features(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract predictive features from metadata."""
        return {
            "quality_score": metadata.get("quality_score", 0.5),
            "aesthetic_score": metadata.get("aesthetic_score", 0.5),
            "objects": metadata.get("scene_objects", []),
            "colors": metadata.get("dominant_colors", []),
            "duration": metadata.get("duration", 30),
            "platform": metadata.get("platform"),
            "caption_length": len(metadata.get("caption", ""))
        }
    
    async def _predict_retention(self, features: Dict[str, Any]) -> float:
        """Predict retention score based on features."""
        # Simple heuristic based on quality and aesthetics
        base_score = (
            features.get("quality_score", 0.5) * 0.6 +
            features.get("aesthetic_score", 0.5) * 0.4
        )
        
        # Adjust for duration (shorter = better retention)
        duration = features.get("duration", 30)
        duration_factor = 1.0 if duration <= 30 else 0.8
        
        return min(1.0, base_score * duration_factor)
    
    async def _predict_engagement(self, features: Dict[str, Any]) -> float:
        """Predict engagement score based on features."""
        # Simple heuristic
        base_score = features.get("quality_score", 0.5)
        
        # Boost for captions
        if features.get("caption_length", 0) > 10:
            base_score *= 1.1
        
        return min(1.0, base_score)
    
    def _predict_timing_score(self) -> float:
        """Predict timing score (current time vs optimal)."""
        hour = datetime.utcnow().hour
        # Peak hours: 6-9 AM, 5-8 PM UTC
        if 6 <= hour <= 9 or 17 <= hour <= 20:
            return 0.9
        elif 10 <= hour <= 16:
            return 0.6
        else:
            return 0.4
    
    def _recommend_platform(self, features: Dict[str, Any]) -> Optional[Platform]:
        """Recommend best platform for content."""
        quality = features.get("quality_score", 0.5)
        
        if quality >= 0.8:
            return Platform.INSTAGRAM
        elif quality >= 0.6:
            return Platform.TIKTOK
        else:
            return Platform.YOUTUBE
