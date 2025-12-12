"""
Orchestrator Monitor - System State Monitoring
Provides real-time snapshot of entire system state
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    Job, JobStatus,
    PublishLogModel,
    Clip,
    Campaign, CampaignStatus,
)
from app.ledger.models import LedgerEvent, EventSeverity
from app.core.config import settings


async def monitor_system_state(db: AsyncSession) -> Dict[str, Any]:
    """
    Monitor complete system state and return comprehensive snapshot
    
    Returns dict with:
    - jobs: counts by status
    - publish_logs: counts by status
    - scheduler_windows: current state of scheduling
    - campaigns: active campaigns info
    - clips: recent clips performance
    - ledger: recent errors/events
    - system: overall health metrics
    """
    now = datetime.utcnow()
    
    # 1. Jobs monitoring
    jobs_data = await _monitor_jobs(db)
    
    # 2. Publish logs monitoring
    publish_logs_data = await _monitor_publish_logs(db)
    
    # 3. Scheduler windows monitoring
    scheduler_data = await _monitor_scheduler_windows(db, now)
    
    # 4. Campaigns monitoring
    campaigns_data = await _monitor_campaigns(db)
    
    # 5. Clips performance monitoring
    clips_data = await _monitor_clips(db, now)
    
    # 6. Ledger monitoring (errors, events)
    ledger_data = await _monitor_ledger(db, now)
    
    # 7. System health
    system_health = _calculate_system_health(
        jobs_data, publish_logs_data, scheduler_data, ledger_data
    )
    
    snapshot = {
        "timestamp": now.isoformat(),
        "jobs": jobs_data,
        "publish_logs": publish_logs_data,
        "scheduler": scheduler_data,
        "campaigns": campaigns_data,
        "clips": clips_data,
        "ledger": ledger_data,
        "system": system_health
    }
    
    return snapshot


async def _monitor_jobs(db: AsyncSession) -> Dict[str, Any]:
    """Monitor jobs queue state"""
    
    # Count by status
    pending_query = select(func.count(Job.id)).where(Job.status == JobStatus.PENDING)
    processing_query = select(func.count(Job.id)).where(Job.status == JobStatus.PROCESSING)
    retry_query = select(func.count(Job.id)).where(Job.status == JobStatus.RETRY)
    failed_query = select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
    completed_query = select(func.count(Job.id)).where(Job.status == JobStatus.COMPLETED)
    
    pending_count = (await db.execute(pending_query)).scalar() or 0
    processing_count = (await db.execute(processing_query)).scalar() or 0
    retry_count = (await db.execute(retry_query)).scalar() or 0
    failed_count = (await db.execute(failed_query)).scalar() or 0
    completed_count = (await db.execute(completed_query)).scalar() or 0
    
    # Get oldest pending job age
    oldest_pending_query = select(Job.created_at).where(
        Job.status == JobStatus.PENDING
    ).order_by(Job.created_at).limit(1)
    oldest_pending_result = await db.execute(oldest_pending_query)
    oldest_pending = oldest_pending_result.scalar_one_or_none()
    
    oldest_age_minutes = None
    if oldest_pending:
        oldest_age_minutes = (datetime.utcnow() - oldest_pending).total_seconds() / 60
    
    return {
        "pending": pending_count,
        "processing": processing_count,
        "retry": retry_count,
        "failed": failed_count,
        "completed": completed_count,
        "total": pending_count + processing_count + retry_count + failed_count + completed_count,
        "oldest_pending_age_minutes": oldest_age_minutes,
        "queue_saturated": pending_count > 50  # Heuristic threshold
    }


async def _monitor_publish_logs(db: AsyncSession) -> Dict[str, Any]:
    """Monitor publishing queue state"""
    
    # Count by status
    pending_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "pending"
    )
    scheduled_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "scheduled"
    )
    failed_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "failed"
    )
    retry_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "retry"
    )
    published_query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "published"
    )
    
    pending_count = (await db.execute(pending_query)).scalar() or 0
    scheduled_count = (await db.execute(scheduled_query)).scalar() or 0
    failed_count = (await db.execute(failed_query)).scalar() or 0
    retry_count = (await db.execute(retry_query)).scalar() or 0
    published_count = (await db.execute(published_query)).scalar() or 0
    
    # Get failed logs in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_failed_query = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.status == "failed",
            PublishLogModel.updated_at >= one_hour_ago
        )
    )
    recent_failed_count = (await db.execute(recent_failed_query)).scalar() or 0
    
    return {
        "pending": pending_count,
        "scheduled": scheduled_count,
        "failed": failed_count,
        "retry": retry_count,
        "published": published_count,
        "total": pending_count + scheduled_count + failed_count + retry_count + published_count,
        "recent_failures_1h": recent_failed_count,
        "has_failures": failed_count > 0 or recent_failed_count > 0
    }


async def _monitor_scheduler_windows(db: AsyncSession, now: datetime) -> Dict[str, Any]:
    """Monitor scheduler windows state"""
    
    current_hour = now.hour
    
    # Check which platforms are in active window
    instagram_window = settings.PLATFORM_WINDOWS.get("instagram", {"start_hour": 18, "end_hour": 23})
    tiktok_window = settings.PLATFORM_WINDOWS.get("tiktok", {"start_hour": 16, "end_hour": 24})
    youtube_window = settings.PLATFORM_WINDOWS.get("youtube", {"start_hour": 17, "end_hour": 22})
    
    def is_in_window(hour: int, window: dict) -> bool:
        start = window["start_hour"]
        end = window["end_hour"]
        if start <= end:
            return start <= hour < end
        else:  # Crosses midnight
            return hour >= start or hour < end
    
    instagram_active = is_in_window(current_hour, instagram_window)
    tiktok_active = is_in_window(current_hour, tiktok_window)
    youtube_active = is_in_window(current_hour, youtube_window)
    
    # Count scheduled logs due in next hour
    next_hour = now + timedelta(hours=1)
    due_soon_query = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.status == "scheduled",
            PublishLogModel.scheduled_for >= now,
            PublishLogModel.scheduled_for <= next_hour
        )
    )
    due_soon_count = (await db.execute(due_soon_query)).scalar() or 0
    
    return {
        "current_hour": current_hour,
        "windows": {
            "instagram": {"active": instagram_active, "start": instagram_window["start_hour"], "end": instagram_window["end_hour"]},
            "tiktok": {"active": tiktok_active, "start": tiktok_window["start_hour"], "end": tiktok_window["end_hour"]},
            "youtube": {"active": youtube_active, "start": youtube_window["start_hour"], "end": youtube_window["end_hour"]}
        },
        "any_window_active": instagram_active or tiktok_active or youtube_active,
        "scheduled_due_soon_1h": due_soon_count
    }


async def _monitor_campaigns(db: AsyncSession) -> Dict[str, Any]:
    """Monitor active campaigns"""
    
    # Count active campaigns
    active_query = select(func.count(Campaign.id)).where(
        Campaign.status == CampaignStatus.ACTIVE
    )
    active_count = (await db.execute(active_query)).scalar() or 0
    
    # Get active campaigns details
    campaigns_query = select(Campaign).where(
        Campaign.status == CampaignStatus.ACTIVE
    ).limit(10)
    campaigns_result = await db.execute(campaigns_query)
    campaigns = campaigns_result.scalars().all()
    
    campaigns_list = []
    for campaign in campaigns:
        campaigns_list.append({
            "id": str(campaign.id),
            "name": campaign.name,
            "budget_cents": campaign.budget_cents,
            "clip_id": str(campaign.clip_id) if campaign.clip_id else None
        })
    
    return {
        "active_count": active_count,
        "has_active_campaigns": active_count > 0,
        "campaigns": campaigns_list
    }


async def _monitor_clips(db: AsyncSession, now: datetime) -> Dict[str, Any]:
    """Monitor clips performance"""
    
    # Get clips created in last 24h
    yesterday = now - timedelta(hours=24)
    recent_clips_query = select(Clip).where(
        Clip.created_at >= yesterday
    ).order_by(Clip.visual_score.desc()).limit(20)
    recent_clips_result = await db.execute(recent_clips_query)
    recent_clips = recent_clips_result.scalars().all()
    
    # Calculate average visual score
    avg_score_query = select(func.avg(Clip.visual_score)).where(
        Clip.visual_score.isnot(None)
    )
    avg_score_result = await db.execute(avg_score_query)
    avg_visual_score = avg_score_result.scalar() or 0.0
    
    # Find high-score clips (>80)
    high_score_query = select(func.count(Clip.id)).where(
        and_(
            Clip.visual_score > 80,
            Clip.created_at >= yesterday
        )
    )
    high_score_count = (await db.execute(high_score_query)).scalar() or 0
    
    clips_list = []
    for clip in recent_clips:
        clips_list.append({
            "id": str(clip.id),
            "visual_score": clip.visual_score,
            "created_at": clip.created_at.isoformat() if clip.created_at else None,
            "status": clip.status.value if clip.status else None
        })
    
    return {
        "recent_24h_count": len(recent_clips),
        "avg_visual_score": float(avg_visual_score),
        "high_score_count_24h": high_score_count,
        "has_high_score_clips": high_score_count > 0,
        "recent_clips": clips_list[:5]  # Top 5 only
    }


async def _monitor_ledger(db: AsyncSession, now: datetime) -> Dict[str, Any]:
    """Monitor ledger for recent errors and events"""
    
    # Get errors in last hour
    one_hour_ago = now - timedelta(hours=1)
    error_query = select(func.count(LedgerEvent.id)).where(
        and_(
            LedgerEvent.severity == EventSeverity.ERROR,
            LedgerEvent.timestamp >= one_hour_ago
        )
    )
    error_count = (await db.execute(error_query)).scalar() or 0
    
    # Get recent error events
    recent_errors_query = select(LedgerEvent).where(
        and_(
            LedgerEvent.severity == EventSeverity.ERROR,
            LedgerEvent.timestamp >= one_hour_ago
        )
    ).order_by(LedgerEvent.timestamp.desc()).limit(10)
    recent_errors_result = await db.execute(recent_errors_query)
    recent_errors = recent_errors_result.scalars().all()
    
    errors_list = []
    for error in recent_errors:
        errors_list.append({
            "event_type": error.event_type,
            "entity_type": error.entity_type,
            "created_at": error.timestamp.isoformat() if error.timestamp else None
        })
    
    # Count events in last hour
    events_query = select(func.count(LedgerEvent.id)).where(
        LedgerEvent.timestamp >= one_hour_ago
    )
    events_count = (await db.execute(events_query)).scalar() or 0
    
    return {
        "errors_1h": error_count,
        "has_errors": error_count > 0,
        "recent_errors": errors_list,
        "total_events_1h": events_count
    }


def _calculate_system_health(
    jobs_data: Dict,
    publish_logs_data: Dict,
    scheduler_data: Dict,
    ledger_data: Dict
) -> Dict[str, Any]:
    """Calculate overall system health metrics"""
    
    # Health score (0-100)
    health_score = 100.0
    
    # Deduct for queue saturation
    if jobs_data["queue_saturated"]:
        health_score -= 20
    
    # Deduct for pending jobs backlog
    if jobs_data["oldest_pending_age_minutes"] and jobs_data["oldest_pending_age_minutes"] > 30:
        health_score -= 15
    
    # Deduct for publishing failures
    if publish_logs_data["has_failures"]:
        health_score -= 10
    
    # Deduct for recent errors
    if ledger_data["has_errors"]:
        health_score -= ledger_data["errors_1h"] * 5  # 5 points per error
    
    health_score = max(0, health_score)
    
    # Health status
    if health_score >= 80:
        health_status = "healthy"
    elif health_score >= 50:
        health_status = "degraded"
    else:
        health_status = "critical"
    
    # Recommendations
    recommendations = []
    if jobs_data["queue_saturated"]:
        recommendations.append("Scale job workers")
    if publish_logs_data["has_failures"]:
        recommendations.append("Investigate publishing failures")
    if ledger_data["has_errors"]:
        recommendations.append("Review error logs")
    if not scheduler_data["any_window_active"]:
        recommendations.append("Outside all publishing windows")
    
    return {
        "health_score": health_score,
        "health_status": health_status,
        "recommendations": recommendations,
        "requires_attention": health_score < 80
    }
