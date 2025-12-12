"""
Rule Context Builder - Build state snapshot for decision making

Combines data from all system engines:
- Vision Engine: Scene analysis, aesthetics, quality scores
- Community Manager: Content plans, recommendations, sentiment
- Satellite Engine: Performance metrics, retention, CTR
- ML Engine: Clusters, predictions, similarities
- Brand Rules: Artist identity, compliance thresholds
- Trend Signals: External patterns, viral opportunities
- Meta Ads: Campaign performance, budget status
- Orchestrator: System state, recent actions, queues
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum


class ChannelType(str, Enum):
    """Content channel types."""
    OFFICIAL = "official"
    SATELLITE = "satellite"


class Platform(str, Enum):
    """Social media platforms."""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram_reels"
    YOUTUBE = "youtube_shorts"


class StateSnapshot(BaseModel):
    """
    Complete system state snapshot for rule evaluation.
    
    This is the primary input to the Rules Evaluator.
    """
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    snapshot_id: str
    
    # Vision Engine data
    vision_analysis: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: scene_type, detected_objects, color_palette, 
    # aesthetic_score, brand_compliance_score, quality_score
    
    # Community Manager data
    cm_state: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: daily_plan, recommended_content_types, sentiment_analysis,
    # trend_recommendations, content_calendar
    
    # Satellite Engine metrics
    satellite_metrics: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: recent_posts, avg_retention, avg_ctr, avg_engagement,
    # top_performing_content, failed_content
    
    # ML Engine predictions
    ml_predictions: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: predicted_performance, content_cluster, similar_content,
    # audience_match_score, virality_score
    
    # Brand configuration
    brand_rules: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: quality_thresholds, compliance_thresholds, color_palette,
    # allowed_content_types, forbidden_content_types
    
    # Trend signals
    trend_signals: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: trending_sounds, trending_formats, brand_fit_scores,
    # viral_opportunities
    
    # Meta Ads performance
    meta_ads_state: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: active_campaigns, daily_spend, campaign_performance,
    # budget_remaining, cost_per_result
    
    # Orchestrator state
    orchestrator_state: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: pending_actions, recent_decisions, system_health,
    # queue_sizes, error_count
    
    # Cost tracking
    cost_tracking: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys: daily_spend, monthly_spend, per_action_costs,
    # budget_limits
    
    # Content being evaluated
    content: Optional[Dict[str, Any]] = None
    # Expected keys: video_path, duration, channel_type, platform,
    # caption, hashtags


class RuleContextBuilder:
    """
    Builds StateSnapshot from all system components.
    
    Responsibilities:
    1. Fetch latest data from each engine
    2. Combine into unified StateSnapshot
    3. Validate completeness
    4. Handle missing data gracefully
    """
    
    def __init__(self):
        """Initialize context builder."""
        self.last_snapshot: Optional[StateSnapshot] = None
        self.snapshot_cache_ttl = timedelta(minutes=5)
    
    async def build_snapshot(
        self,
        content: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> StateSnapshot:
        """
        Build complete state snapshot.
        
        Args:
            content: Content being evaluated (optional)
            force_refresh: Force refresh even if cached
            
        Returns:
            StateSnapshot with all system data
        """
        # Check cache
        if not force_refresh and self.last_snapshot:
            age = datetime.utcnow() - self.last_snapshot.timestamp
            if age < self.snapshot_cache_ttl:
                if content:
                    self.last_snapshot.content = content
                return self.last_snapshot
        
        # Build new snapshot
        snapshot = StateSnapshot(
            snapshot_id=self._generate_snapshot_id(),
            vision_analysis=await self._fetch_vision_data(content),
            cm_state=await self._fetch_cm_data(),
            satellite_metrics=await self._fetch_satellite_metrics(),
            ml_predictions=await self._fetch_ml_predictions(content),
            brand_rules=await self._fetch_brand_rules(),
            trend_signals=await self._fetch_trend_signals(),
            meta_ads_state=await self._fetch_meta_ads_state(),
            orchestrator_state=await self._fetch_orchestrator_state(),
            cost_tracking=await self._fetch_cost_tracking(),
            content=content
        )
        
        self.last_snapshot = snapshot
        return snapshot
    
    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        return f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def _fetch_vision_data(self, content: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fetch Vision Engine analysis.
        
        If content provided, analyze it. Otherwise return latest analysis.
        """
        if not content:
            return {}
        
        # Mock implementation - replace with actual Vision Engine call
        return {
            "scene_type": "urban_night",
            "detected_objects": ["car", "city", "neon_lights"],
            "color_palette": ["#8B44FF", "#0A0A0A", "#1A1A2E"],
            "color_match_score": 0.82,
            "aesthetic_score": 8.5,
            "brand_compliance_score": 0.87,
            "quality_score": 9.1,
            "dominant_colors": ["purple", "black"],
            "lighting_type": "high_contrast_neon",
            "scene_coherence": 0.91
        }
    
    async def _fetch_cm_data(self) -> Dict[str, Any]:
        """Fetch Community Manager state."""
        # Mock implementation - replace with actual CM API call
        return {
            "daily_plan": {
                "official_posts_scheduled": 1,
                "satellite_posts_scheduled": 3,
                "next_official_post_time": "20:00"
            },
            "recommended_content_types": [
                "teaser_cinematico",
                "behind_scenes_premium"
            ],
            "sentiment_analysis": {
                "recent_comments_sentiment": "positive",
                "sentiment_score": 0.72
            },
            "trend_recommendations": [
                {
                    "trend": "cyberpunk_aesthetic",
                    "brand_fit_score": 0.89,
                    "recommendation": "adapt_for_official"
                }
            ]
        }
    
    async def _fetch_satellite_metrics(self) -> Dict[str, Any]:
        """Fetch Satellite Engine performance metrics."""
        # Mock implementation - replace with actual Satellite Engine API
        return {
            "last_24h": {
                "posts_published": 15,
                "avg_retention": 0.68,
                "avg_ctr": 0.042,
                "avg_engagement": 0.051,
                "total_views": 45230
            },
            "top_performing": [
                {
                    "post_id": "sat_001",
                    "retention": 0.82,
                    "ctr": 0.067,
                    "content_type": "GTA_edit"
                }
            ],
            "failed_content": [
                {
                    "post_id": "sat_012",
                    "retention": 0.31,
                    "issue": "low_quality_video"
                }
            ]
        }
    
    async def _fetch_ml_predictions(self, content: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fetch ML Engine predictions."""
        if not content:
            return {}
        
        # Mock implementation - replace with actual ML Engine call
        return {
            "predicted_retention": 0.74,
            "predicted_engagement": 0.058,
            "virality_score": 0.62,
            "content_cluster": "dark_aesthetic_high_energy",
            "similar_content_ids": ["vid_123", "vid_456"],
            "audience_match_score": 0.81,
            "recommendation": "post_to_official"
        }
    
    async def _fetch_brand_rules(self) -> Dict[str, Any]:
        """Fetch brand rules from onboarding."""
        # Load from brand_static_rules.json
        return {
            "official_quality_threshold": 8.0,
            "satellite_quality_threshold": 5.0,
            "brand_compliance_threshold": 0.8,
            "aesthetic_coherence_threshold": 0.7,
            "color_match_threshold": 0.6,
            "signature_color": "#8B44FF",
            "allowed_content_official": [
                "videoclips_oficiales",
                "teasers_cinematicos",
                "behind_scenes_premium"
            ],
            "forbidden_content_official": [
                "contenido_viral_generico",
                "trends_sin_coherencia"
            ]
        }
    
    async def _fetch_trend_signals(self) -> Dict[str, Any]:
        """Fetch trending signals from platforms."""
        # Mock implementation - replace with actual Trend Miner data
        return {
            "tiktok_trending": [
                {
                    "sound_id": "sound_789",
                    "sound_name": "Dark Trap Beat",
                    "usage_count": 125000,
                    "brand_fit_score": 0.85
                }
            ],
            "instagram_trending": [
                {
                    "format": "cinematic_transitions",
                    "viral_score": 0.78,
                    "brand_fit_score": 0.82
                }
            ],
            "viral_opportunities": [
                {
                    "type": "cyberpunk_aesthetic",
                    "window": "next_48h",
                    "confidence": 0.71
                }
            ]
        }
    
    async def _fetch_meta_ads_state(self) -> Dict[str, Any]:
        """Fetch Meta Ads campaign status."""
        # Mock implementation - replace with actual Meta Ads API
        return {
            "active_campaigns": 2,
            "daily_spend": 3.45,
            "monthly_spend": 87.20,
            "budget_remaining_daily": 6.55,
            "budget_remaining_monthly": 212.80,
            "best_performing_campaign": {
                "campaign_id": "camp_001",
                "cost_per_result": 0.08,
                "results": 43
            }
        }
    
    async def _fetch_orchestrator_state(self) -> Dict[str, Any]:
        """Fetch Orchestrator system state."""
        # Mock implementation - replace with actual Orchestrator API
        return {
            "pending_actions": 3,
            "recent_decisions": [
                {
                    "action": "post_short",
                    "platform": "tiktok",
                    "timestamp": "2024-12-07T14:30:00Z",
                    "result": "success"
                }
            ],
            "system_health": "healthy",
            "queue_sizes": {
                "render_queue": 2,
                "post_queue": 1,
                "approval_queue": 0
            },
            "error_count_24h": 0
        }
    
    async def _fetch_cost_tracking(self) -> Dict[str, Any]:
        """Fetch cost tracking data."""
        return {
            "daily_spend": 5.23,
            "daily_limit": 10.0,
            "monthly_spend": 142.67,
            "monthly_limit": 300.0,
            "per_action_costs": {
                "render_video": 0.05,
                "post_short": 0.01,
                "meta_ads": 3.45
            },
            "budget_alerts": []
        }
    
    def validate_snapshot(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """
        Validate snapshot completeness and quality.
        
        Returns:
            Validation result with warnings/errors
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "completeness": 0.0
        }
        
        # Check required sections
        required_sections = [
            "vision_analysis",
            "cm_state",
            "satellite_metrics",
            "brand_rules",
            "cost_tracking"
        ]
        
        complete_sections = 0
        for section in required_sections:
            data = getattr(snapshot, section, {})
            if data and len(data) > 0:
                complete_sections += 1
            else:
                validation["warnings"].append(f"Section '{section}' is empty")
        
        validation["completeness"] = complete_sections / len(required_sections)
        
        # Check critical data
        if not snapshot.brand_rules:
            validation["errors"].append("Brand rules missing - cannot evaluate compliance")
            validation["valid"] = False
        
        if not snapshot.cost_tracking:
            validation["errors"].append("Cost tracking missing - cannot enforce budgets")
            validation["valid"] = False
        
        return validation
    
    def get_snapshot_summary(self, snapshot: StateSnapshot) -> Dict[str, Any]:
        """Get human-readable snapshot summary."""
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "snapshot_id": snapshot.snapshot_id,
            "has_content": snapshot.content is not None,
            "vision_score": snapshot.vision_analysis.get("quality_score", "N/A"),
            "brand_compliance": snapshot.vision_analysis.get("brand_compliance_score", "N/A"),
            "satellite_retention": snapshot.satellite_metrics.get("last_24h", {}).get("avg_retention", "N/A"),
            "daily_spend": snapshot.cost_tracking.get("daily_spend", 0.0),
            "daily_budget_remaining": snapshot.cost_tracking.get("daily_limit", 10.0) - snapshot.cost_tracking.get("daily_spend", 0.0),
            "system_health": snapshot.orchestrator_state.get("system_health", "unknown")
        }
