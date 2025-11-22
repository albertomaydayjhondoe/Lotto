"""
System Data Collector for AI Global Worker.

Collects comprehensive system state from all modules:
- Queue statistics
- Scheduler status
- Orchestrator metrics
- Publishing history
- Content (clips, jobs, campaigns)
- Alerts
- Best clips per platform
- Rule engine weights
- Ledger events
- Worker load
- Telemetry
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Dict, Any

from app.models.database import (
    Job, JobStatus,
    Clip, ClipStatus,
    Campaign, CampaignStatus,
    PublishLogModel,
    AlertEventModel,
    VideoAsset
)
from app.ai_global_worker.schemas import SystemSnapshot
from app.ledger import get_recent_events
from app.orchestrator.runner import is_orchestrator_running


async def collect_system_snapshot(db: AsyncSession) -> SystemSnapshot:
    """
    Collect comprehensive system snapshot.
    
    Gathers data from all system components to provide complete
    observability for AI reasoning.
    
    Args:
        db: Database session
        
    Returns:
        SystemSnapshot with all collected metrics
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    # Initialize snapshot data
    snapshot_data = {
        "timestamp": now,
        "queue_pending": 0,
        "queue_processing": 0,
        "queue_failed": 0,
        "queue_success": 0,
        "scheduler_pending": 0,
        "scheduler_due_soon": 0,
        "orchestrator_running": False,
        "orchestrator_last_run": None,
        "orchestrator_actions_last_24h": 0,
        "publish_success_rate": 0.0,
        "publish_total_24h": 0,
        "publish_failed_24h": 0,
        "clips_ready": 0,
        "clips_pending_analysis": 0,
        "jobs_pending": 0,
        "jobs_failed": 0,
        "campaigns_active": 0,
        "campaigns_draft": 0,
        "alerts_critical": 0,
        "alerts_warning": 0,
        "platform_stats": {},
        "best_clips": {},
        "rule_weights": {},
        "recent_events": [],
        "additional_metrics": {}
    }
    
    # Collect queue metrics from PublishLogModel
    try:
        queue_stats = await db.execute(
            select(
                PublishLogModel.status,
                func.count(PublishLogModel.id).label("count")
            )
            .group_by(PublishLogModel.status)
        )
        
        for status, count in queue_stats.all():
            if status == "pending":
                snapshot_data["queue_pending"] = count
            elif status == "processing":
                snapshot_data["queue_processing"] = count
            elif status == "failed":
                snapshot_data["queue_failed"] = count
            elif status == "success":
                snapshot_data["queue_success"] = count
    except Exception as e:
        snapshot_data["additional_metrics"]["queue_error"] = str(e)
    
    # Collect scheduler metrics
    try:
        scheduled_count = await db.execute(
            select(func.count(PublishLogModel.id))
            .where(PublishLogModel.status == "scheduled")
        )
        snapshot_data["scheduler_pending"] = scheduled_count.scalar() or 0
        
        # Count scheduled items due in next hour
        next_hour = now + timedelta(hours=1)
        due_soon_count = await db.execute(
            select(func.count(PublishLogModel.id))
            .where(
                and_(
                    PublishLogModel.status == "scheduled",
                    PublishLogModel.scheduled_for <= next_hour
                )
            )
        )
        snapshot_data["scheduler_due_soon"] = due_soon_count.scalar() or 0
    except Exception as e:
        snapshot_data["additional_metrics"]["scheduler_error"] = str(e)
    
    # Collect orchestrator status
    try:
        snapshot_data["orchestrator_running"] = is_orchestrator_running()
        # Note: orchestrator_last_run and actions would need tracking in a separate table
        # For now, using placeholder
        snapshot_data["orchestrator_actions_last_24h"] = 0
    except Exception as e:
        snapshot_data["additional_metrics"]["orchestrator_error"] = str(e)
    
    # Collect publishing metrics (last 24h)
    try:
        publish_stats_24h = await db.execute(
            select(
                PublishLogModel.status,
                func.count(PublishLogModel.id).label("count")
            )
            .where(PublishLogModel.requested_at >= last_24h)
            .group_by(PublishLogModel.status)
        )
        
        total_24h = 0
        failed_24h = 0
        success_24h = 0
        
        for status, count in publish_stats_24h.all():
            total_24h += count
            if status == "failed":
                failed_24h = count
            elif status == "success":
                success_24h = count
        
        snapshot_data["publish_total_24h"] = total_24h
        snapshot_data["publish_failed_24h"] = failed_24h
        
        if total_24h > 0:
            snapshot_data["publish_success_rate"] = success_24h / total_24h
    except Exception as e:
        snapshot_data["additional_metrics"]["publishing_error"] = str(e)
    
    # Collect clip metrics
    try:
        clips_by_status = await db.execute(
            select(
                Clip.status,
                func.count(Clip.id).label("count")
            )
            .group_by(Clip.status)
        )
        
        for status, count in clips_by_status.all():
            if status == ClipStatus.READY:
                snapshot_data["clips_ready"] = count
            elif status in [ClipStatus.PENDING, ClipStatus.PROCESSING]:
                snapshot_data["clips_pending_analysis"] += count
    except Exception as e:
        snapshot_data["additional_metrics"]["clips_error"] = str(e)
    
    # Collect job metrics
    try:
        jobs_by_status = await db.execute(
            select(
                Job.status,
                func.count(Job.id).label("count")
            )
            .group_by(Job.status)
        )
        
        for status, count in jobs_by_status.all():
            if status == JobStatus.PENDING:
                snapshot_data["jobs_pending"] = count
            elif status == JobStatus.FAILED:
                snapshot_data["jobs_failed"] = count
    except Exception as e:
        snapshot_data["additional_metrics"]["jobs_error"] = str(e)
    
    # Collect campaign metrics
    try:
        campaigns_by_status = await db.execute(
            select(
                Campaign.status,
                func.count(Campaign.id).label("count")
            )
            .group_by(Campaign.status)
        )
        
        for status, count in campaigns_by_status.all():
            if status == CampaignStatus.ACTIVE:
                snapshot_data["campaigns_active"] = count
            elif status == CampaignStatus.DRAFT:
                snapshot_data["campaigns_draft"] = count
    except Exception as e:
        snapshot_data["additional_metrics"]["campaigns_error"] = str(e)
    
    # Collect alert metrics
    try:
        alerts_by_severity = await db.execute(
            select(
                AlertEventModel.severity,
                func.count(AlertEventModel.id).label("count")
            )
            .where(AlertEventModel.acknowledged == False)
            .group_by(AlertEventModel.severity)
        )
        
        for severity, count in alerts_by_severity.all():
            if severity == "critical":
                snapshot_data["alerts_critical"] = count
            elif severity == "warning":
                snapshot_data["alerts_warning"] = count
    except Exception as e:
        snapshot_data["additional_metrics"]["alerts_error"] = str(e)
    
    # Collect platform-specific stats
    try:
        platform_clips = await db.execute(
            select(
                Clip.target_platform,
                Clip.status,
                func.count(Clip.id).label("count"),
                func.avg(Clip.visual_score).label("avg_visual_score")
            )
            .where(Clip.target_platform.isnot(None))
            .group_by(Clip.target_platform, Clip.status)
        )
        
        platform_data = {}
        for platform, status, count, avg_score in platform_clips.all():
            if platform not in platform_data:
                platform_data[platform] = {
                    "total_clips": 0,
                    "ready_clips": 0,
                    "avg_visual_score": 0.0
                }
            
            platform_data[platform]["total_clips"] += count
            if status == ClipStatus.READY:
                platform_data[platform]["ready_clips"] = count
            if avg_score:
                platform_data[platform]["avg_visual_score"] = float(avg_score)
        
        snapshot_data["platform_stats"] = platform_data
    except Exception as e:
        snapshot_data["additional_metrics"]["platform_error"] = str(e)
    
    # Collect recent ledger events
    try:
        recent_events = await get_recent_events(db, limit=50)
        snapshot_data["recent_events"] = [
            {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "event_type": event.event_type,
                "severity": event.severity.value if event.severity else "INFO"
            }
            for event in recent_events
        ]
    except Exception as e:
        snapshot_data["additional_metrics"]["ledger_error"] = str(e)
    
    # Additional metrics
    try:
        total_videos = await db.execute(select(func.count(VideoAsset.id)))
        snapshot_data["additional_metrics"]["total_videos"] = total_videos.scalar() or 0
        
        total_clips = await db.execute(select(func.count(Clip.id)))
        snapshot_data["additional_metrics"]["total_clips"] = total_clips.scalar() or 0
    except Exception as e:
        snapshot_data["additional_metrics"]["metrics_error"] = str(e)
    
    return SystemSnapshot(**snapshot_data)
