"""
Telemetry Collector

Collects real-time metrics from the system.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.database import (
    PublishLogModel,
    ClipVariant,
    Job,
    JobStatus
)
from app.ledger import get_recent_events
from .models import (
    TelemetryPayload,
    QueueStats,
    SchedulerStats,
    OrchestratorStats,
    PlatformStats,
    WorkerStats
)


async def gather_metrics(db: AsyncSession) -> TelemetryPayload:
    """
    Gather all telemetry metrics from the system.
    
    Uses optimized queries with aggregations to minimize database load.
    
    Args:
        db: Database session
        
    Returns:
        TelemetryPayload with current system metrics
    """
    # Gather all metrics concurrently for performance
    queue_stats = await _collect_queue_stats(db)
    scheduler_stats = await _collect_scheduler_stats(db)
    orchestrator_stats = await _collect_orchestrator_stats(db)
    platform_stats = await _collect_platform_stats(db)
    worker_stats = await _collect_worker_stats(db)
    
    return TelemetryPayload(
        queue=queue_stats,
        scheduler=scheduler_stats,
        orchestrator=orchestrator_stats,
        platforms=platform_stats,
        workers=worker_stats,
        timestamp=datetime.utcnow()
    )


async def _collect_queue_stats(db: AsyncSession) -> QueueStats:
    """
    Collect queue statistics with single optimized query.
    
    Args:
        db: Database session
        
    Returns:
        QueueStats object
    """
    # Single query with aggregations grouped by status
    from sqlalchemy import case
    
    query = select(
        func.sum(case((PublishLogModel.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((PublishLogModel.status == "processing", 1), else_=0)).label("processing"),
        func.sum(case((PublishLogModel.status == "success", 1), else_=0)).label("success"),
        func.sum(case((PublishLogModel.status == "failed", 1), else_=0)).label("failed"),
        func.count(PublishLogModel.id).label("total")
    )
    
    result = await db.execute(query)
    row = result.one()
    
    return QueueStats(
        pending=row.pending or 0,
        processing=row.processing or 0,
        success=row.success or 0,
        failed=row.failed or 0,
        total=row.total or 0
    )


async def _collect_scheduler_stats(db: AsyncSession) -> SchedulerStats:
    """
    Collect scheduler statistics.
    
    Args:
        db: Database session
        
    Returns:
        SchedulerStats object
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    next_hour = now + timedelta(hours=1)
    
    # Scheduled today
    query_today = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.scheduled_for >= today_start,
            PublishLogModel.scheduled_for < today_end,
            PublishLogModel.status == "pending"
        )
    )
    result_today = await db.execute(query_today)
    scheduled_today = result_today.scalar() or 0
    
    # Scheduled in next hour
    query_next_hour = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.scheduled_for >= now,
            PublishLogModel.scheduled_for < next_hour,
            PublishLogModel.status == "pending"
        )
    )
    result_next_hour = await db.execute(query_next_hour)
    scheduled_next_hour = result_next_hour.scalar() or 0
    
    # Overdue (scheduled in past but still pending)
    query_overdue = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.scheduled_for < now,
            PublishLogModel.status == "pending"
        )
    )
    result_overdue = await db.execute(query_overdue)
    overdue = result_overdue.scalar() or 0
    
    # Average delay for overdue items
    avg_delay_seconds = None
    if overdue > 0:
        query_delay = select(
            func.avg(
                func.extract('epoch', now - PublishLogModel.scheduled_for)
            )
        ).where(
            and_(
                PublishLogModel.scheduled_for < now,
                PublishLogModel.status == "pending"
            )
        )
        result_delay = await db.execute(query_delay)
        avg_delay = result_delay.scalar()
        if avg_delay:
            avg_delay_seconds = float(avg_delay)
    
    return SchedulerStats(
        scheduled_today=scheduled_today,
        scheduled_next_hour=scheduled_next_hour,
        overdue=overdue,
        avg_delay_seconds=avg_delay_seconds
    )


async def _collect_orchestrator_stats(db: AsyncSession) -> OrchestratorStats:
    """
    Collect orchestrator statistics from ledger events.
    
    Args:
        db: Database session
        
    Returns:
        OrchestratorStats object
    """
    # Get recent orchestrator events from ledger
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    # Count orchestrator actions in last minute
    recent_events = await get_recent_events(
        db=db,
        event_type="orchestrator.action_executed",
        limit=100
    )
    
    # Filter to last minute
    actions_last_minute = sum(
        1 for event in recent_events
        if event.timestamp >= one_minute_ago
    )
    
    # Count pending jobs as proxy for pending decisions
    query_pending = select(func.count(Job.id)).where(
        Job.status == JobStatus.PENDING
    )
    result_pending = await db.execute(query_pending)
    decisions_pending = result_pending.scalar() or 0
    
    # Calculate saturation rate (pending / total jobs)
    query_total = select(func.count(Job.id))
    result_total = await db.execute(query_total)
    total_jobs = result_total.scalar() or 0
    
    saturation_rate = None
    if total_jobs > 0:
        saturation_rate = decisions_pending / total_jobs
    
    # Get last orchestrator run from ledger
    last_run_seconds_ago = None
    if recent_events:
        last_event = recent_events[0]
        delta = datetime.utcnow() - last_event.timestamp
        last_run_seconds_ago = int(delta.total_seconds())
    
    return OrchestratorStats(
        actions_last_minute=actions_last_minute,
        decisions_pending=decisions_pending,
        saturation_rate=saturation_rate,
        last_run_seconds_ago=last_run_seconds_ago
    )


async def _collect_platform_stats(db: AsyncSession) -> PlatformStats:
    """
    Collect platform statistics (clips ready per platform).
    
    Args:
        db: Database session
        
    Returns:
        PlatformStats object
    """
    from sqlalchemy import case
    
    # Single query with aggregations per platform
    query = select(
        func.sum(case((ClipVariant.platform == "instagram", 1), else_=0)).label("instagram"),
        func.sum(case((ClipVariant.platform == "tiktok", 1), else_=0)).label("tiktok"),
        func.sum(case((ClipVariant.platform == "youtube", 1), else_=0)).label("youtube"),
        func.sum(case((ClipVariant.platform == "facebook", 1), else_=0)).label("facebook")
    ).where(ClipVariant.status == "ready")
    
    result = await db.execute(query)
    row = result.one()
    
    return PlatformStats(
        instagram=row.instagram or 0,
        tiktok=row.tiktok or 0,
        youtube=row.youtube or 0,
        facebook=row.facebook or 0
    )


async def _collect_worker_stats(db: AsyncSession) -> WorkerStats:
    """
    Collect worker statistics.
    
    Args:
        db: Database session
        
    Returns:
        WorkerStats object
    """
    # Count processing items as proxy for active workers
    query_processing = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "processing"
    )
    result_processing = await db.execute(query_processing)
    tasks_processing = result_processing.scalar() or 0
    
    # Estimate active workers (assume 1 worker per processing task)
    active_workers = tasks_processing
    
    # Calculate average processing time from completed tasks
    query_avg_time = select(
        func.avg(
            func.extract('epoch', PublishLogModel.published_at - PublishLogModel.requested_at) * 1000
        )
    ).where(
        and_(
            PublishLogModel.status == "success",
            PublishLogModel.published_at.isnot(None),
            PublishLogModel.requested_at.isnot(None)
        )
    )
    result_avg_time = await db.execute(query_avg_time)
    avg_time = result_avg_time.scalar()
    
    avg_processing_time_ms = float(avg_time) if avg_time else None
    
    return WorkerStats(
        active_workers=active_workers,
        tasks_processing=tasks_processing,
        avg_processing_time_ms=avg_processing_time_ms
    )
