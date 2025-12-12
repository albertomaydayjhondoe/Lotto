"""
Orchestrator Executor - Action Execution Engine
Executes actions decided by the decider
"""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.orchestrator.decider import OrchestratorAction
from app.models.database import Clip, PublishLogModel, Campaign, Job, JobStatus, CampaignStatus, ClipStatus

# Add alias for consistency
JobModel = Job
from app.publishing_scheduler.scheduler import schedule_publication
from app.publishing_intelligence.intelligence import auto_schedule_clip
from app.publishing_reconciliation.recon import reconcile_publications
from app.ledger import log_event
from sqlalchemy import select, and_, or_


async def execute_actions(
    actions: List[OrchestratorAction],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Execute list of actions
    Returns execution report
    """
    
    results = []
    success_count = 0
    error_count = 0
    
    for action in actions:
        try:
            result = await _execute_single_action(action, db)
            results.append({
                "action_type": action.action_type,
                "status": "success",
                "result": result,
                "priority": action.priority,
                "reason": action.reason
            })
            success_count += 1
            
            # Log success
            await log_event(
                db=db,
                event_type="orchestrator.action_executed",
                entity_type="orchestrator",
                entity_id="orchestrator",
                metadata={
                    "action_type": action.action_type,
                    "params": action.params,
                    "result": result,
                    "status": "success"
                }
            )
            
        except Exception as e:
            results.append({
                "action_type": action.action_type,
                "status": "error",
                "error": str(e),
                "priority": action.priority,
                "reason": action.reason
            })
            error_count += 1
            
            # Log error
            await log_event(
                db=db,
                event_type="orchestrator.action_failed",
                entity_type="orchestrator",
                entity_id="orchestrator",
                metadata={
                    "action_type": action.action_type,
                    "params": action.params,
                    "error": str(e),
                    "status": "error"
                },
                is_error=True
            )
    
    return {
        "total_actions": len(actions),
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


async def _execute_single_action(
    action: OrchestratorAction,
    db: AsyncSession
) -> Dict[str, Any]:
    """Execute a single action based on type"""
    
    action_type = action.action_type
    params = action.params
    
    if action_type == "schedule_clip":
        return await _execute_schedule_clip(db, params)
    
    elif action_type == "retry_failed_log":
        return await _execute_retry_failed_log(db, params)
    
    elif action_type == "trigger_reconciliation":
        return await _execute_trigger_reconciliation(db, params)
    
    elif action_type == "promote_high_score_clip":
        return await _execute_promote_high_score_clip(db, params)
    
    elif action_type == "downgrade_low_score_clip":
        return await _execute_downgrade_low_score_clip(db, params)
    
    elif action_type == "force_publish":
        return await _execute_force_publish(db, params)
    
    elif action_type == "rebalance_queue":
        return await _execute_rebalance_queue(db, params)
    
    else:
        raise ValueError(f"Unknown action type: {action_type}")


async def _execute_schedule_clip(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule a clip for publishing"""
    
    clip_id = params.get("clip_id")
    platform = params.get("platform", "auto")
    min_visual_score = params.get("min_visual_score", 80)
    use_intelligence = params.get("use_intelligence", True)
    
    # Find clip to schedule
    if clip_id:
        clip = await db.get(Clip, clip_id)
        if not clip:
            return {"status": "error", "message": f"Clip {clip_id} not found"}
    else:
        # Find best clip based on score
        stmt = select(Clip).where(
            and_(
                Clip.visual_score >= min_visual_score,
                Clip.status == ClipStatus.READY
            )
        ).order_by(Clip.visual_score.desc()).limit(1)
        
        result = await db.execute(stmt)
        clip = result.scalar_one_or_none()
        
        if not clip:
            return {"status": "no_clips", "message": "No suitable clips found"}
    
    # Use APIL if requested
    if use_intelligence:
        result = await auto_schedule_clip(
            db=db,
            clip_id=str(clip.id),
            platform=platform if platform != "auto" else "instagram"  # Default platform
        )
        return {"status": "scheduled_via_apil", "clip_id": clip.id, "result": result}
    else:
        # Direct scheduling not implemented in simplified version
        # Would need to create ScheduleRequest and call schedule_publication
        return {"status": "skipped", "reason": "Direct scheduling requires more parameters"}


async def _execute_retry_failed_log(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Retry failed publish logs"""
    
    max_retries = params.get("max_retries", 3)
    force = params.get("force", False)
    
    # Find failed logs
    stmt = select(PublishLogModel).where(
        PublishLogModel.status == "failed"
    ).order_by(PublishLogModel.updated_at.desc()).limit(10)
    
    result = await db.execute(stmt)
    failed_logs = result.scalars().all()
    
    if not failed_logs:
        return {"status": "no_failures", "message": "No failed logs to retry"}
    
    retried_count = 0
    for log in failed_logs:
        if force or (log.retry_count or 0) < max_retries:
            # Reset to scheduled
            log.status = "scheduled"
            log.retry_count = (log.retry_count or 0) + 1
            log.updated_at = datetime.utcnow()
            retried_count += 1
    
    await db.commit()
    
    return {
        "status": "retried",
        "count": retried_count,
        "total_failed": len(failed_logs)
    }


async def _execute_trigger_reconciliation(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger reconciliation process"""
    
    reason = params.get("reason", "manual")
    
    # Run reconciliation
    result = await reconcile_publications(db=db, since_minutes=10)
    
    return {
        "status": "reconciled",
        "reason": reason,
        "result": result
    }


async def _execute_promote_high_score_clip(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Promote high-scoring clips"""
    
    min_visual_score = params.get("min_visual_score", 80)
    platform = params.get("platform", "auto")
    
    # Find high-score clips not yet published
    stmt = select(Clip).where(
        and_(
            Clip.visual_score >= min_visual_score,
            Clip.status == ClipStatus.READY
        )
    ).order_by(Clip.visual_score.desc()).limit(3)
    
    result = await db.execute(stmt)
    clips = result.scalars().all()
    
    if not clips:
        return {"status": "no_clips", "message": "No high-score clips to promote"}
    
    promoted_count = 0
    for clip in clips:
        # Check if already scheduled
        stmt_log = select(PublishLogModel).where(
            and_(
                PublishLogModel.clip_id == clip.id,
                or_(
                    PublishLogModel.status == "scheduled",
                    PublishLogModel.status == "published"
                )
            )
        )
        existing = await db.execute(stmt_log)
        if existing.scalar_one_or_none():
            continue  # Already scheduled/published
        
        # Schedule via APIL
        await auto_schedule_clip(
            db=db,
            clip_id=str(clip.id),
            platform=platform if platform != "auto" else "instagram"
        )
        promoted_count += 1
    
    return {
        "status": "promoted",
        "count": promoted_count,
        "total_candidates": len(clips)
    }


async def _execute_downgrade_low_score_clip(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Downgrade low-scoring clips"""
    
    max_visual_score = params.get("max_visual_score", 30)
    
    # Find low-score clips that are scheduled but not published
    stmt = select(PublishLogModel).join(Clip).where(
        and_(
            Clip.visual_score <= max_visual_score,
            PublishLogModel.status == "scheduled"
        )
    ).limit(5)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    if not logs:
        return {"status": "no_logs", "message": "No low-score clips to downgrade"}
    
    downgraded_count = 0
    for log in logs:
        # Postpone scheduled time by 24 hours
        if log.scheduled_at:
            log.scheduled_at = log.scheduled_at + timedelta(hours=24)
            log.updated_at = datetime.utcnow()
            downgraded_count += 1
    
    await db.commit()
    
    return {
        "status": "downgraded",
        "count": downgraded_count,
        "total_candidates": len(logs)
    }


async def _execute_force_publish(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Force immediate publication of pending logs"""
    
    age_threshold_minutes = params.get("age_threshold_minutes", 60)
    limit = params.get("limit", 5)
    reason = params.get("reason", "force")
    
    # Find old pending publish logs
    threshold_time = datetime.utcnow() - timedelta(minutes=age_threshold_minutes)
    
    stmt = select(PublishLogModel).where(
        and_(
            PublishLogModel.status.in_(["scheduled", "pending"]),
            PublishLogModel.created_at <= threshold_time
        )
    ).order_by(PublishLogModel.created_at.asc()).limit(limit)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    if not logs:
        return {"status": "no_logs", "message": "No old logs to force publish"}
    
    forced_count = 0
    for log in logs:
        # Change to pending and clear scheduled_at
        log.status = "pending"
        log.scheduled_at = None
        log.updated_at = datetime.utcnow()
        forced_count += 1
    
    await db.commit()
    
    return {
        "status": "forced",
        "count": forced_count,
        "reason": reason,
        "total_candidates": len(logs)
    }


async def _execute_rebalance_queue(db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
    """Rebalance job queue by priority"""
    
    emergency = params.get("emergency", False)
    strategy = params.get("strategy", "priority")
    
    # Find pending jobs
    stmt = select(JobModel).where(
        JobModel.status == "pending"
    ).order_by(JobModel.created_at.asc())
    
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    if not jobs:
        return {"status": "no_jobs", "message": "No pending jobs to rebalance"}
    
    # If emergency, fail old jobs
    if emergency:
        threshold = datetime.utcnow() - timedelta(hours=2)
        failed_count = 0
        for job in jobs:
            if job.created_at <= threshold:
                job.status = "failed"
                job.result = {"error": "Emergency rebalance timeout"}
                job.updated_at = datetime.utcnow()
                failed_count += 1
        
        await db.commit()
        return {
            "status": "emergency_rebalanced",
            "failed_count": failed_count,
            "total_jobs": len(jobs)
        }
    
    # Normal rebalance: just log, actual rebalancing happens in worker
    return {
        "status": "rebalance_requested",
        "strategy": strategy,
        "pending_count": len(jobs),
        "message": "Workers will pick up jobs by priority"
    }
