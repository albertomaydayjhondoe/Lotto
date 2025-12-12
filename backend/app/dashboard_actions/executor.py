"""
Dashboard Actions Executor

Executes dashboard actions by delegating to appropriate services.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.database import (
    Clip,
    ClipVariant,
    PublishLogModel,
    Campaign,
    VideoAsset
)
from app.publishing_engine.service import publish_clip
from app.publishing_engine.models import PublishRequest
from app.publishing_scheduler.scheduler import schedule_publication
from app.publishing_scheduler.models import ScheduleRequest
from app.orchestrator.runner import run_orchestrator_once
from app.ledger import log_event


async def execute_action(
    action_type: str,
    payload: Dict[str, Any],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Execute a dashboard action.
    
    Args:
        action_type: Type of action to execute
        payload: Action-specific parameters
        db: Database session
        
    Returns:
        Dict with execution result
        
    Raises:
        ValueError: If action type is unknown or payload is invalid
    """
    action_map = {
        "publish": _action_force_publish,
        "retry": _action_retry_failed,
        "run_orchestrator": _action_run_orchestrator,
        "run_scheduler": _action_run_scheduler,
        "rebalance_queue": _action_rebalance_queue,
        "promote": _action_promote_clip,
        "publish_best_clip": _action_publish_best_clip,
        "reschedule": _action_reschedule,
        "clear_failed": _action_clear_failed,
        "optimize_schedule": _action_optimize_schedule
    }
    
    action_func = action_map.get(action_type)
    if not action_func:
        raise ValueError(f"Unknown action type: {action_type}")
    
    try:
        result = await action_func(payload, db)
        
        # Log action execution
        await log_event(
            db=db,
            event_type="dashboard.action_executed",
            entity_type="dashboard",
            entity_id="dashboard_actions",
            metadata={
                "action_type": action_type,
                "payload": payload,
                "result": result
            }
        )
        
        return {
            "success": True,
            "message": result.get("message", "Action executed successfully"),
            "data": result,
            "executed_at": datetime.utcnow()
        }
        
    except Exception as e:
        # Log error
        await log_event(
            db=db,
            event_type="dashboard.action_failed",
            entity_type="dashboard",
            entity_id="dashboard_actions",
            metadata={
                "action_type": action_type,
                "payload": payload,
                "error": str(e)
            },
            is_error=True
        )
        
        raise


async def _action_force_publish(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Force publish a clip immediately."""
    clip_id = UUID(payload["clip_id"]) if isinstance(payload.get("clip_id"), str) else payload.get("clip_id")
    platform = payload.get("platform")
    account_id = payload.get("account_id")
    
    if not clip_id:
        raise ValueError("clip_id is required")
    
    # If no platform specified, find best variant
    if not platform:
        query = (
            select(ClipVariant)
            .join(Clip, ClipVariant.clip_id == Clip.id)
            .where(
                and_(
                    Clip.id == clip_id,
                    ClipVariant.status == "ready"
                )
            )
            .order_by(ClipVariant.visual_score.desc())
            .limit(1)
        )
        result = await db.execute(query)
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise ValueError(f"No ready variants found for clip {clip_id}")
        
        platform = variant.platform
    
    # Publish
    publish_request = PublishRequest(
        clip_id=clip_id,
        platform=platform,
        social_account_id=UUID(account_id) if account_id else None
    )
    
    result = await publish_clip(db, publish_request)
    
    return {
        "message": f"Clip published to {platform}",
        "clip_id": str(clip_id),
        "platform": platform,
        "publish_log_id": str(result.publish_log_id) if result.publish_log_id else None,
        "status": "success" if result.success else "failed"
    }


async def _action_retry_failed(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Retry all failed publications."""
    # Find failed publications
    query = (
        select(PublishLogModel)
        .where(PublishLogModel.status == "failed")
        .limit(50)  # Limit to prevent overload
    )
    result = await db.execute(query)
    failed_logs = result.scalars().all()
    
    retry_count = 0
    for log in failed_logs:
        # Reset status to pending
        log.status = "pending"
        log.requested_at = datetime.utcnow()
        retry_count += 1
    
    await db.commit()
    
    return {
        "message": f"Retrying {retry_count} failed publications",
        "retry_count": retry_count
    }


async def _action_run_orchestrator(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Run orchestrator tick manually."""
    result = await run_orchestrator_once()
    
    return {
        "message": "Orchestrator tick completed",
        "actions_executed": result.get("actions_executed", 0),
        "decisions_made": result.get("decisions_made", 0)
    }


async def _action_run_scheduler(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Run scheduler tick manually."""
    dry_run = payload.get("dry_run", False)
    
    # Get pending clips to schedule
    query = (
        select(ClipVariant)
        .where(
            and_(
                ClipVariant.status == "ready",
                ClipVariant.visual_score.isnot(None)
            )
        )
        .order_by(ClipVariant.visual_score.desc())
        .limit(20)
    )
    result = await db.execute(query)
    variants = result.scalars().all()
    
    scheduled_count = 0
    for variant in variants:
        if not dry_run:
            # Schedule publication
            schedule_request = ScheduleRequest(
                clip_id=variant.clip_id,
                platform=variant.platform,
                scheduled_for=datetime.utcnow() + timedelta(hours=2),
                social_account_id=None  # Will be assigned by scheduler
            )
            
            try:
                await schedule_publication(db, schedule_request)
                scheduled_count += 1
            except Exception:
                pass  # Continue with next variant
        else:
            scheduled_count += 1
    
    return {
        "message": f"Scheduler tick completed ({'dry run' if dry_run else 'live'})",
        "scheduled_count": scheduled_count,
        "dry_run": dry_run
    }


async def _action_rebalance_queue(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Rebalance publishing queue by optimizing scheduled times."""
    # Get pending publications
    query = (
        select(PublishLogModel)
        .where(PublishLogModel.status == "pending")
        .order_by(PublishLogModel.scheduled_for)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    rebalanced_count = 0
    for i, log in enumerate(logs):
        # Spread publications evenly with 30-minute intervals
        new_time = datetime.utcnow() + timedelta(minutes=30 * (i + 1))
        log.scheduled_for = new_time
        rebalanced_count += 1
    
    await db.commit()
    
    return {
        "message": f"Queue rebalanced: {rebalanced_count} items rescheduled",
        "rebalanced_count": rebalanced_count
    }


async def _action_promote_clip(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Promote best clip from video to a campaign."""
    video_id = UUID(payload.get("video_id")) if isinstance(payload.get("video_id"), str) else payload.get("video_id")
    campaign_id = payload.get("campaign_id")
    
    if not video_id:
        raise ValueError("video_id is required")
    
    # Find best clip from video
    query = (
        select(Clip)
        .where(Clip.video_id == video_id)
        .order_by(Clip.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise ValueError(f"No clips found for video {video_id}")
    
    # If campaign_id provided, link clip to campaign
    if campaign_id:
        campaign_uuid = UUID(campaign_id) if isinstance(campaign_id, str) else campaign_id
        clip.campaign_id = campaign_uuid
        await db.commit()
    
    return {
        "message": f"Clip promoted to campaign",
        "clip_id": str(clip.id),
        "campaign_id": str(campaign_id) if campaign_id else None
    }


async def _action_publish_best_clip(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Publish best available clip from a video."""
    video_id = UUID(payload.get("video_id")) if isinstance(payload.get("video_id"), str) else payload.get("video_id")
    platform = payload.get("platform")
    
    if not video_id:
        raise ValueError("video_id is required")
    
    # Find best clip variant
    query = (
        select(ClipVariant, Clip)
        .join(Clip, ClipVariant.clip_id == Clip.id)
        .where(
            and_(
                Clip.video_id == video_id,
                ClipVariant.status == "ready"
            )
        )
        .order_by(ClipVariant.visual_score.desc())
        .limit(1)
    )
    
    if platform:
        query = query.where(ClipVariant.platform == platform)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise ValueError(f"No ready clips found for video {video_id}")
    
    variant, clip = row
    
    # Publish
    publish_request = PublishRequest(
        clip_id=clip.id,
        platform=variant.platform
    )
    
    publish_result = await publish_clip(db, publish_request)
    
    return {
        "message": f"Best clip published to {variant.platform}",
        "clip_id": str(clip.id),
        "variant_id": str(variant.id),
        "platform": variant.platform,
        "score": float(variant.visual_score) if variant.visual_score else 0.0
    }


async def _action_reschedule(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Reschedule a publication to a new time."""
    log_id = UUID(payload.get("log_id")) if isinstance(payload.get("log_id"), str) else payload.get("log_id")
    new_time_str = payload.get("new_time")
    
    if not log_id or not new_time_str:
        raise ValueError("log_id and new_time are required")
    
    # Parse new time
    if isinstance(new_time_str, str):
        new_time = datetime.fromisoformat(new_time_str.replace("Z", "+00:00"))
    else:
        new_time = new_time_str
    
    # Update publication
    query = select(PublishLogModel).where(PublishLogModel.id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        raise ValueError(f"Publish log {log_id} not found")
    
    old_time = log.scheduled_for
    log.scheduled_for = new_time
    await db.commit()
    
    return {
        "message": f"Publication rescheduled",
        "log_id": str(log_id),
        "old_time": old_time.isoformat() if old_time else None,
        "new_time": new_time.isoformat()
    }


async def _action_clear_failed(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Clear old failed publications."""
    older_than_days = payload.get("older_than_days", 7)
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
    
    # Delete old failed logs
    query = (
        select(PublishLogModel)
        .where(
            and_(
                PublishLogModel.status == "failed",
                PublishLogModel.requested_at < cutoff_date
            )
        )
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    deleted_count = len(logs)
    for log in logs:
        await db.delete(log)
    
    await db.commit()
    
    return {
        "message": f"Cleared {deleted_count} old failed publications",
        "deleted_count": deleted_count,
        "older_than_days": older_than_days
    }


async def _action_optimize_schedule(payload: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Optimize schedule for specified platforms."""
    platforms = payload.get("platforms", [])
    
    if not platforms:
        platforms = ["instagram", "tiktok", "youtube", "facebook"]
    
    optimized_count = 0
    for platform in platforms:
        # Find pending publications for platform
        query = (
            select(PublishLogModel)
            .where(
                and_(
                    PublishLogModel.platform == platform,
                    PublishLogModel.status == "pending"
                )
            )
            .order_by(PublishLogModel.scheduled_for)
            .limit(10)
        )
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Optimize timing (spread evenly in optimal windows)
        for i, log in enumerate(logs):
            # Example: schedule during peak hours (10 AM - 8 PM)
            optimal_hour = 10 + (i * 2) % 10  # 10, 12, 14, 16, 18, etc.
            new_time = datetime.utcnow().replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
            
            if new_time < datetime.utcnow():
                new_time += timedelta(days=1)
            
            log.scheduled_for = new_time
            optimized_count += 1
    
    await db.commit()
    
    return {
        "message": f"Optimized schedule for {len(platforms)} platforms",
        "platforms": platforms,
        "optimized_count": optimized_count
    }
