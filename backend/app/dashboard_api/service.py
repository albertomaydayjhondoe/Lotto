"""
Dashboard API Service Layer

All business logic and database queries for dashboard statistics.
Uses optimized SQLAlchemy async queries with aggregations.
"""

from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    VideoAsset,
    Clip,
    ClipVariant,
    Publication,
    Job,
    Campaign,
    PublishLogModel,
    JobStatus,
    ClipStatus,
    CampaignStatus
)
from .schemas import (
    OverviewStats,
    QueueStats,
    OrchestratorStats,
    PlatformStats,
    PlatformBreakdown,
    CampaignStats
)


async def get_overview_stats(db: AsyncSession) -> OverviewStats:
    """
    Get global system statistics overview.
    
    Single query per entity type, no loops.
    
    Args:
        db: Database session
        
    Returns:
        OverviewStats with all counts
    """
    # Count videos
    videos_result = await db.execute(select(func.count(VideoAsset.id)))
    total_videos = videos_result.scalar() or 0
    
    # Count clips
    clips_result = await db.execute(select(func.count(Clip.id)))
    total_clips = clips_result.scalar() or 0
    
    # Count jobs total and by status
    jobs_query = select(
        func.count(Job.id).label("total"),
        func.sum(case((Job.status == JobStatus.PENDING, 1), else_=0)).label("pending"),
        func.sum(case((Job.status == JobStatus.PROCESSING, 1), else_=0)).label("processing"),
        func.sum(case((Job.status == JobStatus.FAILED, 1), else_=0)).label("failed")
    )
    jobs_result = await db.execute(jobs_query)
    jobs_row = jobs_result.one()
    
    total_jobs = jobs_row.total or 0
    pending_jobs = jobs_row.pending or 0
    processing_jobs = jobs_row.processing or 0
    failed_jobs = jobs_row.failed or 0
    
    # Count campaigns
    campaigns_result = await db.execute(select(func.count(Campaign.id)))
    total_campaigns = campaigns_result.scalar() or 0
    
    # Count publish logs by status
    logs_query = select(
        func.sum(case((PublishLogModel.status == "success", 1), else_=0)).label("success"),
        func.sum(case((PublishLogModel.status == "failed", 1), else_=0)).label("failed"),
        func.sum(case((PublishLogModel.status == "pending", 1), else_=0)).label("scheduled")
    )
    logs_result = await db.execute(logs_query)
    logs_row = logs_result.one()
    
    success_logs = logs_row.success or 0
    failed_logs = logs_row.failed or 0
    scheduled_publications = logs_row.scheduled or 0
    
    return OverviewStats(
        total_videos=total_videos,
        total_clips=total_clips,
        total_jobs=total_jobs,
        total_campaigns=total_campaigns,
        pending_jobs=pending_jobs,
        processing_jobs=processing_jobs,
        failed_jobs=failed_jobs,
        success_logs=success_logs,
        failed_logs=failed_logs,
        scheduled_publications=scheduled_publications
    )


async def get_queue_stats(db: AsyncSession) -> QueueStats:
    """
    Get publication queue statistics.
    
    Calculates aggregates including processing times and aging.
    
    Args:
        db: Database session
        
    Returns:
        QueueStats with queue metrics
    """
    # Count by status
    status_query = select(
        func.sum(case((PublishLogModel.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((PublishLogModel.status == "processing", 1), else_=0)).label("processing"),
        func.sum(case((PublishLogModel.status == "success", 1), else_=0)).label("success"),
        func.sum(case((PublishLogModel.status == "failed", 1), else_=0)).label("failed")
    )
    status_result = await db.execute(status_query)
    status_row = status_result.one()
    
    pending = status_row.pending or 0
    processing = status_row.processing or 0
    success = status_row.success or 0
    failed = status_row.failed or 0
    
    # Calculate average processing time for successful publications
    # Processing time = published_at - requested_at (in milliseconds)
    # Note: Extract epoch from (later_time - earlier_time) to get positive difference
    avg_time_query = select(
        func.avg(
            (func.extract('epoch', PublishLogModel.published_at) - func.extract('epoch', PublishLogModel.requested_at)) * 1000
        )
    ).where(
        and_(
            PublishLogModel.status == "success",
            PublishLogModel.published_at.isnot(None),
            PublishLogModel.requested_at.isnot(None)
        )
    )
    avg_time_result = await db.execute(avg_time_query)
    avg_processing_time_ms = avg_time_result.scalar()
    
    # Calculate age of oldest pending item (in seconds)
    oldest_pending_query = select(
        func.min(PublishLogModel.requested_at)
    ).where(PublishLogModel.status == "pending")
    oldest_pending_result = await db.execute(oldest_pending_query)
    oldest_pending = oldest_pending_result.scalar()
    
    oldest_pending_age_seconds = None
    if oldest_pending:
        age_delta = datetime.utcnow() - oldest_pending
        oldest_pending_age_seconds = age_delta.total_seconds()
    
    return QueueStats(
        pending=pending,
        processing=processing,
        success=success,
        failed=failed,
        avg_processing_time_ms=avg_processing_time_ms,
        oldest_pending_age_seconds=oldest_pending_age_seconds
    )


async def get_orchestrator_stats(db: AsyncSession) -> OrchestratorStats:
    """
    Get orchestrator activity metrics.
    
    Note: Since we don't have an orchestrator_logs table yet,
    this uses publish_logs as proxy for orchestrator actions.
    
    Args:
        db: Database session
        
    Returns:
        OrchestratorStats with orchestrator metrics
    """
    # Get last publish log as proxy for last orchestrator run
    last_run_query = select(func.max(PublishLogModel.created_at))
    last_run_result = await db.execute(last_run_query)
    last_run_at = last_run_result.scalar()
    
    # Count actions in last 24 hours (new publish logs)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    actions_24h_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.created_at >= twenty_four_hours_ago
    )
    actions_24h_result = await db.execute(actions_24h_query)
    actions_last_24h = actions_24h_result.scalar() or 0
    
    # Actions last run: count of logs created in last hour (simulated)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    actions_last_run_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.created_at >= one_hour_ago
    )
    actions_last_run_result = await db.execute(actions_last_run_query)
    actions_last_run = actions_last_run_result.scalar() or 0
    
    # Calculate queue saturation: (pending + processing) / (total logs + 1)
    # Saturation ranges from 0.0 (empty) to 1.0 (fully saturated)
    saturation_query = select(
        func.sum(case((PublishLogModel.status.in_(["pending", "processing"]), 1), else_=0)).label("active"),
        func.count(PublishLogModel.id).label("total")
    )
    saturation_result = await db.execute(saturation_query)
    saturation_row = saturation_result.one()
    
    active_count = saturation_row.active or 0
    total_count = saturation_row.total or 0
    
    # Avoid division by zero, cap at 1.0
    if total_count > 0:
        queue_saturation = min(active_count / total_count, 1.0)
    else:
        queue_saturation = 0.0
    
    # Active workers: count of unique social_account_id with processing status
    active_workers_query = select(
        func.count(func.distinct(PublishLogModel.social_account_id))
    ).where(PublishLogModel.status == "processing")
    active_workers_result = await db.execute(active_workers_query)
    active_workers = active_workers_result.scalar() or 0
    
    return OrchestratorStats(
        last_run_at=last_run_at,
        actions_last_run=actions_last_run,
        actions_last_24h=actions_last_24h,
        queue_saturation=queue_saturation,
        active_workers=active_workers
    )


async def get_platform_stats(db: AsyncSession) -> PlatformStats:
    """
    Get aggregated statistics by platform.
    
    Uses PublishLogModel and Publication tables for platform-specific metrics.
    
    Args:
        db: Database session
        
    Returns:
        PlatformStats with breakdown for each platform
    """
    platforms = ["instagram", "tiktok", "youtube", "other"]
    platform_data: Dict[str, PlatformBreakdown] = {}
    
    for platform in platforms:
        # Count clips ready for this platform (based on publish logs pending/scheduled)
        clips_ready_query = select(func.count(func.distinct(PublishLogModel.clip_id))).where(
            and_(
                PublishLogModel.platform == platform,
                PublishLogModel.status.in_(["pending", "scheduled"])
            )
        )
        clips_ready_result = await db.execute(clips_ready_query)
        clips_ready = clips_ready_result.scalar() or 0
        
        # Count clips published for this platform (based on successful publish logs)
        clips_published_query = select(func.count(func.distinct(PublishLogModel.clip_id))).where(
            and_(
                PublishLogModel.platform == platform,
                PublishLogModel.status == "success"
            )
        )
        clips_published_result = await db.execute(clips_published_query)
        clips_published = clips_published_result.scalar() or 0
        
        # Average visual score for clips associated with this platform's logs
        # Join clips through publish logs
        avg_score_query = select(func.avg(Clip.visual_score)).join(
            PublishLogModel, PublishLogModel.clip_id == Clip.id
        ).where(
            and_(
                PublishLogModel.platform == platform,
                Clip.visual_score.isnot(None)
            )
        )
        avg_score_result = await db.execute(avg_score_query)
        avg_score = avg_score_result.scalar()
        avg_score = float(avg_score) if avg_score is not None else 0.0
        
        # Jobs completed and failed for this platform
        # Use cast to handle JSON field access properly
        from sqlalchemy import cast, String
        jobs_query = select(
            func.sum(case((Job.status == JobStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(case((Job.status == JobStatus.FAILED, 1), else_=0)).label("failed")
        ).where(cast(Job.params["platform"], String) == platform)
        
        jobs_result = await db.execute(jobs_query)
        jobs_row = jobs_result.one()
        
        jobs_completed = jobs_row.completed or 0
        jobs_failed = jobs_row.failed or 0
        
        platform_data[platform] = PlatformBreakdown(
            clips_ready=clips_ready,
            clips_published=clips_published,
            avg_score=avg_score,
            jobs_completed=jobs_completed,
            jobs_failed=jobs_failed
        )
    
    return PlatformStats(
        instagram=platform_data["instagram"],
        tiktok=platform_data["tiktok"],
        youtube=platform_data["youtube"],
        other=platform_data["other"]
    )


async def get_campaign_stats(db: AsyncSession) -> CampaignStats:
    """
    Get campaign status aggregations.
    
    Args:
        db: Database session
        
    Returns:
        CampaignStats with campaign counts by status
    """
    # Count campaigns by status
    status_query = select(
        func.sum(case((Campaign.status == CampaignStatus.DRAFT, 1), else_=0)).label("draft"),
        func.sum(case((Campaign.status == CampaignStatus.ACTIVE, 1), else_=0)).label("active"),
        func.sum(case((Campaign.status == CampaignStatus.PAUSED, 1), else_=0)).label("paused"),
        func.sum(case((Campaign.status == CampaignStatus.COMPLETED, 1), else_=0)).label("completed")
    )
    status_result = await db.execute(status_query)
    status_row = status_result.one()
    
    draft = status_row.draft or 0
    active = status_row.active or 0
    paused = status_row.paused or 0
    completed = status_row.completed or 0
    
    # Total budget spent (simulated as 0.0 for now, structure ready)
    # In future: could sum from campaign.budget_spent field or related transactions
    total_budget_spent = 0.0
    
    return CampaignStats(
        draft=draft,
        active=active,
        paused=paused,
        completed=completed,
        total_budget_spent=total_budget_spent
    )
