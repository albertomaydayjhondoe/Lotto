"""
Visual Analytics API Router.

Provides endpoints for aggregated analytics and metrics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.permissions import require_permission
from app.visual_analytics.collector import VisualAnalyticsCollector
from app.visual_analytics.schemas import *


router = APIRouter(prefix="/visual/analytics")


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_analytics_overview(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete analytics overview.
    
    Provides:
    - Total counts (clips, jobs, publications, campaigns)
    - Rates (per day/week/month)
    - Averages (job duration, clip score, success rate)
    - Trends and correlations
    - Top performers
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_overview(days_back)


@router.get(
    "/timeline",
    response_model=TimelineData,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_timeline(
    days_back: int = Query(7, ge=1, le=90, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get timeline data for jobs, publications, clips, and orchestrator events.
    
    Returns time-series data optimized for line charts.
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_timeline(days_back)


@router.get(
    "/heatmap",
    response_model=HeatmapData,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_activity_heatmap(
    metric: str = Query("clips", regex="^(clips|jobs|publications)$"),
    days_back: int = Query(30, ge=1, le=90, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity heatmap by hour and day of week.
    
    Shows activity patterns across different times and days.
    
    Args:
        metric: Which metric to visualize (clips, jobs, publications)
        days_back: Days to look back
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_heatmap(metric, days_back)


@router.get(
    "/platforms",
    response_model=PlatformStats,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_platform_stats(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform performance breakdown.
    
    Provides metrics for each platform:
    - Clips count
    - Publications count
    - Average score
    - Success rate
    - Total views
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_platform_stats(days_back)


@router.get(
    "/clips",
    response_model=ClipsDistribution,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_clips_distribution(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get clips distributions and rankings.
    
    Provides:
    - Duration distribution (histogram)
    - Score distribution (histogram)
    - Top clips by score
    - Average metrics
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_clips_distribution(days_back)


@router.get(
    "/campaigns",
    response_model=CampaignBreakdown,
    dependencies=[Depends(require_permission("analytics:read"))]
)
async def get_campaign_breakdown(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get campaign performance breakdown.
    
    Provides:
    - Campaign metrics (clips, publications, scores)
    - Total and active campaigns
    - Average clips per campaign
    
    Requires: analytics:read permission
    """
    collector = VisualAnalyticsCollector(db)
    return await collector.get_campaign_breakdown(days_back)
