"""
Visual Analytics Layer (PASO 8.3)

Provides aggregated analytics and metrics for dashboard visualization.
"""

from app.visual_analytics.router import router
from app.visual_analytics.collector import VisualAnalyticsCollector
from app.visual_analytics.schemas import (
    AnalyticsOverview,
    TimelineData,
    HeatmapData,
    PlatformStats,
    ClipsDistribution,
    CampaignBreakdown,
    AnalyticsSummary,
)

__all__ = [
    "router",
    "VisualAnalyticsCollector",
    "AnalyticsOverview",
    "TimelineData",
    "HeatmapData",
    "PlatformStats",
    "ClipsDistribution",
    "CampaignBreakdown",
    "AnalyticsSummary",
]
