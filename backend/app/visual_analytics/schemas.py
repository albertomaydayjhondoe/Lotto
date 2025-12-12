"""
Pydantic schemas for Visual Analytics Layer.

Chart-optimized data structures for frontend visualization.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TimeseriesPoint(BaseModel):
    """Single data point in a timeseries."""
    timestamp: datetime
    value: float


class Timeseries(BaseModel):
    """Timeseries data for line charts."""
    series_name: str
    data: List[TimeseriesPoint]
    color: Optional[str] = None


class HeatmapCell(BaseModel):
    """Single cell in a heatmap matrix."""
    x: int  # Hour (0-23)
    y: int  # Day of week (0-6)
    value: float


class HeatmapData(BaseModel):
    """Heatmap data structure."""
    title: str
    x_labels: List[str]  # Hour labels
    y_labels: List[str]  # Day labels
    cells: List[HeatmapCell]
    color_scale: str = "viridis"


class Distribution(BaseModel):
    """Distribution data for histograms."""
    bins: List[float]
    counts: List[int]
    label: Optional[str] = None


class PlatformMetric(BaseModel):
    """Metrics for a single platform."""
    platform: str
    clips_count: int
    publications_count: int
    avg_score: float
    success_rate: float
    total_views: int = 0


class PlatformStats(BaseModel):
    """Platform performance breakdown."""
    platforms: List[PlatformMetric]
    total_clips: int
    total_publications: int
    best_platform: Optional[str] = None


class ClipRanking(BaseModel):
    """Single clip in ranking."""
    clip_id: str
    video_id: str
    title: Optional[str] = None
    score: float
    duration_ms: int


class ClipsDistribution(BaseModel):
    """Clips analytics and distributions."""
    by_duration: Distribution
    by_score: Distribution
    top_clips: List[ClipRanking]
    total_clips: int
    avg_score: float
    avg_duration: float


class CampaignMetric(BaseModel):
    """Metrics for a single campaign."""
    campaign_id: str
    name: str
    status: str
    clips_count: int
    publications_count: int
    avg_clip_score: float
    created_at: datetime


class CampaignBreakdown(BaseModel):
    """Campaign performance breakdown."""
    campaigns: List[CampaignMetric]
    total_campaigns: int
    active_campaigns: int
    avg_clips_per_campaign: float


class TrendLine(BaseModel):
    """Trend line data."""
    metric_name: str
    values: List[float]
    timestamps: List[datetime]


class TimelineData(BaseModel):
    """Timeline data for multiple series."""
    jobs_timeline: List[Timeseries]
    publications_timeline: List[Timeseries]
    clips_timeline: List[Timeseries]
    orchestrator_events: List[Timeseries]
    date_range: Dict[str, datetime]


class CorrelationMetric(BaseModel):
    """Correlation between two metrics."""
    metric_x: str
    metric_y: str
    correlation: float
    sample_size: int


class AnalyticsOverview(BaseModel):
    """Complete analytics overview response."""
    # Counts
    total_clips: int
    total_jobs: int
    total_publications: int
    total_campaigns: int
    
    # Rates
    clips_per_day: float
    clips_per_week: float
    clips_per_month: float
    
    # Averages
    avg_job_duration_ms: float
    avg_clip_score: float
    publication_success_rate: float
    
    # Advanced analytics
    trends: List[TrendLine]
    correlations: List[CorrelationMetric]
    top_videos_by_score: List[ClipRanking]
    rule_engine_metrics: Dict[str, Any]
    
    # Metadata
    generated_at: datetime
    date_range: Dict[str, datetime]


class AnalyticsSummary(BaseModel):
    """Lightweight analytics summary."""
    total_clips: int
    total_jobs: int
    total_publications: int
    avg_clip_score: float
    generated_at: datetime
