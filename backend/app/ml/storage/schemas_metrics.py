"""
Schemas for Model Metrics Storage

Defines Pydantic models for:
- Performance metrics (retention, engagement, behavior)
- Daily snapshots
- Learning reports
- Aggregated statistics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics tracked."""
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    VIEWER_BEHAVIOR = "viewer_behavior"
    CONTENT_PERFORMANCE = "content_performance"
    ENGINE_PERFORMANCE = "engine_performance"
    SATELLITE_PERFORMANCE = "satellite_performance"
    LEARNING_SCORE = "learning_score"


class Platform(str, Enum):
    """Platforms tracked."""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram_reels"
    YOUTUBE = "youtube_shorts"


class ChannelType(str, Enum):
    """Channel types."""
    OFFICIAL = "official"
    SATELLITE = "satellite"


class RetentionMetrics(BaseModel):
    """Retention metrics for a piece of content."""
    content_id: str
    platform: Platform
    channel_type: ChannelType
    
    # Retention data
    avg_watch_time_sec: float
    avg_watch_percentage: float
    retention_curve: List[float]  # Retention at each second
    
    # Drop-off analysis
    drop_off_points: List[int]  # Seconds where significant drop-off occurs
    peak_rewatch_time: Optional[int] = None
    
    # Audience behavior
    completion_rate: float
    rewatch_rate: float
    
    # Timestamp
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class EngagementMetrics(BaseModel):
    """Engagement metrics for content."""
    content_id: str
    platform: Platform
    channel_type: ChannelType
    
    # Core metrics
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    
    # Calculated rates
    ctr: float  # Click-through rate
    engagement_rate: float  # (likes + comments + shares) / views
    save_rate: float  # saves / views
    
    # Velocity
    views_velocity: float  # views per hour
    engagement_velocity: float  # engagements per hour
    
    # Timestamp
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class ViewerBehaviorMetrics(BaseModel):
    """Viewer behavior analysis."""
    content_id: str
    platform: Platform
    
    # Behavior patterns
    avg_session_duration: float
    bounce_rate: float
    return_viewer_rate: float
    
    # Interaction timing
    avg_time_to_first_interaction: float
    avg_time_to_like: Optional[float] = None
    avg_time_to_comment: Optional[float] = None
    
    # Device/context
    mobile_vs_desktop: Dict[str, float] = Field(default_factory=dict)
    time_of_day_distribution: Dict[str, float] = Field(default_factory=dict)
    
    # Timestamp
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class EnginePerformanceMetrics(BaseModel):
    """Performance metrics for ML engines."""
    engine_name: str  # "vision_engine", "content_engine", "community_manager"
    
    # Prediction accuracy
    predictions_made: int
    predictions_correct: int
    accuracy: float
    
    # Specific metrics per engine
    mae: Optional[float] = None  # Mean Absolute Error
    rmse: Optional[float] = None  # Root Mean Squared Error
    
    # Examples
    best_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    worst_predictions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance
    avg_inference_time_ms: float
    
    # Timestamp
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class SatellitePerformanceMetrics(BaseModel):
    """Performance metrics for satellite channels."""
    satellite_account_id: str
    platform: Platform
    
    # Growth
    followers_start: int
    followers_end: int
    followers_growth: int
    followers_growth_rate: float
    
    # Content performance
    posts_count: int
    avg_views: float
    avg_engagement_rate: float
    avg_retention: float
    
    # Best performers
    top_content_ids: List[str] = Field(default_factory=list)
    
    # Cost efficiency
    cost_per_follower: Optional[float] = None
    roi: Optional[float] = None
    
    # Timestamp
    period_start: date
    period_end: date
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class MetaLearningScore(BaseModel):
    """Meta-learning score for content."""
    content_id: str
    
    # Composite scores
    overall_score: float  # 0-100
    retention_score: float
    engagement_score: float
    virality_score: float
    brand_alignment_score: float
    
    # Contributing factors
    factors: Dict[str, float] = Field(default_factory=dict)
    
    # Recommendations
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    # Timestamp
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class DailySnapshot(BaseModel):
    """Daily aggregated snapshot of all metrics."""
    snapshot_date: date
    snapshot_id: str
    
    # Aggregated metrics
    total_content_analyzed: int
    total_views: int
    total_engagement: int
    
    # Averages
    avg_retention: float
    avg_engagement_rate: float
    avg_quality_score: float
    
    # Best performers
    best_content_ids: List[str] = Field(default_factory=list)
    best_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Satellite performance
    satellite_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Engine performance
    engine_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Learning insights
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RetentionCluster(BaseModel):
    """Cluster of content with similar retention patterns."""
    cluster_id: str
    cluster_name: str
    
    # Cluster characteristics
    avg_retention: float
    content_count: int
    content_ids: List[str]
    
    # Common patterns
    common_features: Dict[str, Any] = Field(default_factory=dict)
    common_objects: List[str] = Field(default_factory=list)
    common_colors: List[str] = Field(default_factory=list)
    common_aesthetic: Optional[str] = None
    
    # Performance
    avg_engagement_rate: float
    avg_virality_score: float
    
    # Timestamp
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class PatternDiscovery(BaseModel):
    """Discovered pattern in content performance."""
    pattern_id: str
    pattern_type: str  # "aesthetic", "timing", "object", "color", "audio"
    
    # Pattern description
    description: str
    confidence: float
    
    # Pattern data
    pattern_features: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance impact
    avg_retention_lift: float
    avg_engagement_lift: float
    sample_content_ids: List[str] = Field(default_factory=list)
    
    # Recommendations
    recommended_usage: str
    avoid_combinations: List[str] = Field(default_factory=list)
    
    # Timestamp
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class BestTimeToPost(BaseModel):
    """Optimal posting times for a platform/audience."""
    platform: Platform
    channel_type: ChannelType
    
    # Optimal times
    best_hours: List[int]  # Hours of day (0-23)
    best_days: List[str]  # Days of week
    
    # Performance by time
    hourly_performance: Dict[int, float]  # hour -> avg_engagement_rate
    daily_performance: Dict[str, float]  # day -> avg_engagement_rate
    
    # Confidence
    confidence: float
    sample_size: int
    
    # Timestamp
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class ViralityPrediction(BaseModel):
    """Virality prediction for content."""
    content_id: str
    
    # Prediction
    virality_score: float  # 0-100
    predicted_views: int
    predicted_engagement_rate: float
    
    # Confidence
    confidence: float
    confidence_interval: tuple[float, float]
    
    # Contributing factors
    factors: Dict[str, float] = Field(default_factory=dict)
    
    # Recommendations
    boost_recommended: bool
    optimal_post_time: Optional[datetime] = None
    platform_recommendation: Optional[Platform] = None
    
    # Timestamp
    predicted_at: datetime = Field(default_factory=datetime.utcnow)


class LearningReport(BaseModel):
    """Daily learning report with insights and recommendations."""
    report_date: date
    report_id: str
    
    # Summary
    summary: str
    key_insights: List[str] = Field(default_factory=list)
    
    # Discovered patterns
    new_patterns: List[PatternDiscovery] = Field(default_factory=list)
    retention_clusters: List[RetentionCluster] = Field(default_factory=list)
    
    # Performance analysis
    best_performers: List[Dict[str, Any]] = Field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendations
    content_recommendations: List[str] = Field(default_factory=list)
    timing_recommendations: List[str] = Field(default_factory=list)
    style_recommendations: List[str] = Field(default_factory=list)
    
    # Engine updates
    suggested_rule_updates: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_threshold_updates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Brand reinforcement
    brand_alignment_score: float
    brand_drift_detected: bool
    brand_corrections: List[str] = Field(default_factory=list)
    
    # Cost analysis
    total_cost: float
    cost_per_view: float
    roi: float
    
    # Timestamp
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MetricsWriteRequest(BaseModel):
    """Request to write metrics."""
    metric_type: MetricType
    content_id: str
    data: Dict[str, Any]
    
    # Metadata
    platform: Optional[Platform] = None
    channel_type: Optional[ChannelType] = None
    
    # Options
    overwrite_if_exists: bool = False


class MetricsReadRequest(BaseModel):
    """Request to read metrics."""
    content_ids: Optional[List[str]] = None
    metric_types: Optional[List[MetricType]] = None
    
    # Filters
    platform: Optional[Platform] = None
    channel_type: Optional[ChannelType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    
    # Options
    include_aggregates: bool = False
    limit: int = 100
