"""
Dashboard API Router

Internal API endpoints for administrative panel backend.
All endpoints are read-only statistics and aggregations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from .schemas import (
    OverviewStats,
    QueueStats,
    OrchestratorStats,
    PlatformStats,
    CampaignStats
)
from .service import (
    get_overview_stats,
    get_queue_stats,
    get_orchestrator_stats,
    get_platform_stats,
    get_campaign_stats
)


router = APIRouter()


@router.get(
    "/stats/overview",
    response_model=OverviewStats,
    summary="Get global system statistics",
    description="""
    Returns high-level overview of the entire system:
    - Total counts for videos, clips, jobs, campaigns
    - Job status breakdown (pending, processing, failed)
    - Publication logs summary (success, failed, scheduled)
    """
)
async def overview_stats_endpoint(db: AsyncSession = Depends(get_db)) -> OverviewStats:
    """Get global system statistics overview."""
    return await get_overview_stats(db)


@router.get(
    "/stats/queue",
    response_model=QueueStats,
    summary="Get publication queue statistics",
    description="""
    Returns aggregated metrics for the publication queue:
    - Queue item counts by status (pending, processing, success, failed)
    - Average processing time in milliseconds
    - Age of oldest pending item in seconds
    """
)
async def queue_stats_endpoint(db: AsyncSession = Depends(get_db)) -> QueueStats:
    """Get publication queue statistics."""
    return await get_queue_stats(db)


@router.get(
    "/stats/orchestrator",
    response_model=OrchestratorStats,
    summary="Get orchestrator activity metrics",
    description="""
    Returns orchestrator performance and activity data:
    - Last execution timestamp
    - Actions taken in last run and last 24 hours
    - Queue saturation ratio (0.0 to 1.0)
    - Number of active workers
    """
)
async def orchestrator_stats_endpoint(db: AsyncSession = Depends(get_db)) -> OrchestratorStats:
    """Get orchestrator activity metrics."""
    return await get_orchestrator_stats(db)


@router.get(
    "/stats/platforms",
    response_model=PlatformStats,
    summary="Get platform-specific statistics",
    description="""
    Returns aggregated data broken down by platform:
    - Instagram, TikTok, YouTube, and Other platforms
    - Clips ready vs published counts
    - Average quality scores
    - Job success and failure counts per platform
    """
)
async def platform_stats_endpoint(db: AsyncSession = Depends(get_db)) -> PlatformStats:
    """Get platform-specific statistics."""
    return await get_platform_stats(db)


@router.get(
    "/stats/campaigns",
    response_model=CampaignStats,
    summary="Get campaign status summary",
    description="""
    Returns campaign statistics aggregated by status:
    - Draft, active, paused, and completed campaign counts
    - Total budget spent across all campaigns
    """
)
async def campaign_stats_endpoint(db: AsyncSession = Depends(get_db)) -> CampaignStats:
    """Get campaign status summary."""
    return await get_campaign_stats(db)
