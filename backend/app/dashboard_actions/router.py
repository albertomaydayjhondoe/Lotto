"""
Dashboard Actions Router

FastAPI endpoints for manual dashboard actions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from .models import (
    ForcePublishRequest,
    RescheduleRequest,
    RunSchedulerRequest,
    PromoteClipRequest,
    PublishBestClipRequest,
    ClearFailedRequest,
    ActionResult
)
from .executor import execute_action

router = APIRouter(prefix="/actions", tags=["dashboard_actions"])


@router.post("/force-publish", response_model=ActionResult)
async def force_publish(
    request: ForcePublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Force publish a clip immediately.
    
    Args:
        request: ForcePublishRequest with clip_id, optional platform and account_id
        
    Returns:
        ActionResult with publication details
    """
    try:
        result = await execute_action(
            action_type="publish",
            payload={
                "clip_id": request.clip_id,
                "platform": request.platform,
                "account_id": request.account_id
            },
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-failed", response_model=ActionResult)
async def retry_failed(db: AsyncSession = Depends(get_db)):
    """
    Retry all failed publications.
    
    Returns:
        ActionResult with retry count
    """
    try:
        result = await execute_action(
            action_type="retry",
            payload={},
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-orchestrator", response_model=ActionResult)
async def run_orchestrator(db: AsyncSession = Depends(get_db)):
    """
    Run orchestrator tick manually.
    
    Returns:
        ActionResult with orchestrator execution details
    """
    try:
        result = await execute_action(
            action_type="run_orchestrator",
            payload={},
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-scheduler", response_model=ActionResult)
async def run_scheduler(
    request: RunSchedulerRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run scheduler tick manually.
    
    Args:
        request: RunSchedulerRequest with optional dry_run flag
        
    Returns:
        ActionResult with scheduler execution details
    """
    try:
        result = await execute_action(
            action_type="run_scheduler",
            payload={"dry_run": request.dry_run},
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebalance-queue", response_model=ActionResult)
async def rebalance_queue(db: AsyncSession = Depends(get_db)):
    """
    Rebalance publishing queue by optimizing scheduled times.
    
    Returns:
        ActionResult with rebalance details
    """
    try:
        result = await execute_action(
            action_type="rebalance_queue",
            payload={},
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote-clip", response_model=ActionResult)
async def promote_clip(
    request: PromoteClipRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Promote best clip from video to a campaign.
    
    Args:
        request: PromoteClipRequest with video_id and optional campaign_id
        
    Returns:
        ActionResult with promotion details
    """
    try:
        result = await execute_action(
            action_type="promote",
            payload={
                "video_id": request.video_id,
                "campaign_id": request.campaign_id
            },
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-best-clip", response_model=ActionResult)
async def publish_best_clip(
    request: PublishBestClipRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Publish best available clip from a video.
    
    Args:
        request: PublishBestClipRequest with video_id and optional platform
        
    Returns:
        ActionResult with publication details
    """
    try:
        result = await execute_action(
            action_type="publish_best_clip",
            payload={
                "video_id": request.video_id,
                "platform": request.platform
            },
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reschedule", response_model=ActionResult)
async def reschedule(
    request: RescheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reschedule a publication to a new time.
    
    Args:
        request: RescheduleRequest with log_id and new_time
        
    Returns:
        ActionResult with reschedule details
    """
    try:
        result = await execute_action(
            action_type="reschedule",
            payload={
                "log_id": request.log_id,
                "new_time": request.new_time
            },
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-failed", response_model=ActionResult)
async def clear_failed(
    request: ClearFailedRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear old failed publications.
    
    Args:
        request: ClearFailedRequest with older_than_days
        
    Returns:
        ActionResult with deletion count
    """
    try:
        result = await execute_action(
            action_type="clear_failed",
            payload={"older_than_days": request.older_than_days},
            db=db
        )
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report", response_model=ActionResult)
async def generate_report(db: AsyncSession = Depends(get_db)):
    """
    Generate comprehensive system report.
    
    Returns:
        ActionResult with report data
    """
    try:
        # Import here to avoid circular dependency
        from app.dashboard_ai.analyzer import analyze_system
        from app.dashboard_ai.recommender import generate_recommendations
        
        analysis = await analyze_system(db)
        recommendations = await generate_recommendations(db)
        
        result = {
            "success": True,
            "message": "System report generated",
            "data": {
                "analysis": analysis.dict(),
                "recommendations": [r.dict() for r in recommendations],
                "generated_at": analysis.timestamp.isoformat()
            },
            "executed_at": analysis.timestamp
        }
        
        return ActionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
