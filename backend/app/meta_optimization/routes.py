"""
Optimization API Routes

REST API endpoints for monitoring and controlling the optimization loop.

Endpoints:
- GET  /meta/optimization/queue - List pending actions
- POST /meta/optimization/execute/{action_id} - Execute specific action
- POST /meta/optimization/run - Trigger manual optimization run
- GET  /meta/optimization/stats - Get optimization statistics
- POST /meta/optimization/approve/{action_id} - Approve action for execution
- DELETE /meta/optimization/cancel/{action_id} - Cancel pending action
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.permissions import require_role
from app.models.database import OptimizationActionModel, OptimizationActionStatus
from app.meta_optimization.service import OptimizationService

logger = logging.getLogger("meta_optimization.routes")

router = APIRouter(prefix="/meta/optimization", tags=["meta-optimization"])


# Request/Response Models

class ActionResponse(BaseModel):
    """Response model for optimization action."""
    action_id: str
    campaign_id: Optional[UUID]
    ad_id: Optional[UUID]
    action_type: str
    target_level: str
    target_id: str
    amount_pct: Optional[float]
    amount_usd: Optional[float]
    reason: str
    confidence: float
    roas_value: Optional[float]
    status: str
    created_by: str
    created_at: datetime
    executed_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExecuteActionRequest(BaseModel):
    """Request to execute an action."""
    dry_run: bool = Field(False, description="Simulate execution without actually doing it")


class ExecuteActionResponse(BaseModel):
    """Response from action execution."""
    action_id: str
    status: str
    details: dict
    meta_response: Optional[dict] = None


class ManualRunRequest(BaseModel):
    """Request for manual optimization run."""
    campaign_ids: Optional[List[str]] = Field(None, description="Specific campaigns to evaluate (empty = all)")
    lookback_days: int = Field(7, ge=1, le=30, description="Days of data to analyze")


class ManualRunResponse(BaseModel):
    """Response from manual run."""
    started: bool
    processed_campaigns: int
    actions_suggested: int
    execution_time_seconds: float


class QueueStatsResponse(BaseModel):
    """Statistics about the action queue."""
    total_suggested: int
    total_pending: int
    total_executing: int
    total_executed_today: int
    total_failed_today: int
    avg_confidence: float


class ApproveActionRequest(BaseModel):
    """Request to approve an action."""
    notes: Optional[str] = Field(None, description="Optional notes about approval")


# Endpoints

@router.get("/queue", response_model=List[ActionResponse])
async def list_queue(
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    status: Optional[str] = Query(None, description="Filter by status (suggested, pending, etc.)"),
    action_type: Optional[str] = Query(None, description="Filter by action type (scale_up, scale_down, etc.)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["manager", "admin"])),
):
    """
    List pending and suggested optimization actions.
    
    Requires: manager or admin role
    """
    try:
        stmt = select(OptimizationActionModel)
        
        # Apply filters
        filters = []
        if campaign_id:
            filters.append(OptimizationActionModel.campaign_id == campaign_id)
        if status:
            filters.append(OptimizationActionModel.status == status)
        else:
            # Default: show suggested and pending
            filters.append(OptimizationActionModel.status.in_([
                OptimizationActionStatus.SUGGESTED,
                OptimizationActionStatus.PENDING,
            ]))
        if action_type:
            filters.append(OptimizationActionModel.action_type == action_type)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        stmt = stmt.order_by(OptimizationActionModel.confidence.desc()).limit(limit)
        
        result = await db.execute(stmt)
        actions = result.scalars().all()
        
        return [ActionResponse.from_orm(action) for action in actions]
    
    except Exception as e:
        logger.exception(f"Error listing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=QueueStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["manager", "admin"])),
):
    """
    Get statistics about the optimization queue.
    
    Requires: manager or admin role
    """
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count by status
        stmt_suggested = select(func.count()).select_from(OptimizationActionModel).where(
            OptimizationActionModel.status == OptimizationActionStatus.SUGGESTED
        )
        stmt_pending = select(func.count()).select_from(OptimizationActionModel).where(
            OptimizationActionModel.status == OptimizationActionStatus.PENDING
        )
        stmt_executing = select(func.count()).select_from(OptimizationActionModel).where(
            OptimizationActionModel.status == OptimizationActionStatus.EXECUTING
        )
        stmt_executed_today = select(func.count()).select_from(OptimizationActionModel).where(
            and_(
                OptimizationActionModel.status == OptimizationActionStatus.EXECUTED,
                OptimizationActionModel.executed_at >= today,
            )
        )
        stmt_failed_today = select(func.count()).select_from(OptimizationActionModel).where(
            and_(
                OptimizationActionModel.status == OptimizationActionStatus.FAILED,
                OptimizationActionModel.created_at >= today,
            )
        )
        
        # Average confidence of pending actions
        stmt_avg_conf = select(func.avg(OptimizationActionModel.confidence)).where(
            OptimizationActionModel.status.in_([
                OptimizationActionStatus.SUGGESTED,
                OptimizationActionStatus.PENDING,
            ])
        )
        
        total_suggested = (await db.execute(stmt_suggested)).scalar() or 0
        total_pending = (await db.execute(stmt_pending)).scalar() or 0
        total_executing = (await db.execute(stmt_executing)).scalar() or 0
        total_executed_today = (await db.execute(stmt_executed_today)).scalar() or 0
        total_failed_today = (await db.execute(stmt_failed_today)).scalar() or 0
        avg_confidence = (await db.execute(stmt_avg_conf)).scalar() or 0.0
        
        return QueueStatsResponse(
            total_suggested=total_suggested,
            total_pending=total_pending,
            total_executing=total_executing,
            total_executed_today=total_executed_today,
            total_failed_today=total_failed_today,
            avg_confidence=round(avg_confidence, 3),
        )
    
    except Exception as e:
        logger.exception(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{action_id}", response_model=ExecuteActionResponse)
async def execute_action(
    action_id: str = Path(..., description="Action ID to execute"),
    request: ExecuteActionRequest = ExecuteActionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["manager", "admin"])),
):
    """
    Execute a specific optimization action.
    
    Requires: manager or admin role
    """
    try:
        svc = OptimizationService(db)
        
        # Get user email from token
        run_by = getattr(current_user, "email", "manual")
        
        result = await svc.execute_action(
            action_id=action_id,
            run_by=run_by,
            dry_run=request.dry_run,
        )
        
        return ExecuteActionResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error executing action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{action_id}", response_model=ActionResponse)
async def approve_action(
    action_id: str = Path(..., description="Action ID to approve"),
    request: ApproveActionRequest = ApproveActionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["manager", "admin"])),
):
    """
    Approve an action for execution (moves from SUGGESTED to PENDING).
    
    Requires: manager or admin role
    """
    try:
        stmt = select(OptimizationActionModel).where(
            OptimizationActionModel.action_id == action_id
        )
        result = await db.execute(stmt)
        action = result.scalar_one_or_none()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        if action.status != OptimizationActionStatus.SUGGESTED:
            raise HTTPException(
                status_code=400,
                detail=f"Action must be in SUGGESTED status, current: {action.status}"
            )
        
        # Approve action
        action.status = OptimizationActionStatus.PENDING
        action.approved_by = getattr(current_user, "email", "manual")
        action.approved_at = datetime.utcnow()
        if request.notes:
            action.notes = (action.notes or "") + f"\n[Approved] {request.notes}"
        
        await db.commit()
        await db.refresh(action)
        
        logger.info(f"Action {action_id} approved by {action.approved_by}")
        
        return ActionResponse.from_orm(action)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error approving action {action_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{action_id}")
async def cancel_action(
    action_id: str = Path(..., description="Action ID to cancel"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["manager", "admin"])),
):
    """
    Cancel a pending action.
    
    Requires: manager or admin role
    """
    try:
        stmt = select(OptimizationActionModel).where(
            OptimizationActionModel.action_id == action_id
        )
        result = await db.execute(stmt)
        action = result.scalar_one_or_none()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        if action.status not in [OptimizationActionStatus.SUGGESTED, OptimizationActionStatus.PENDING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel action with status {action.status}"
            )
        
        action.status = OptimizationActionStatus.CANCELLED
        action.notes = (action.notes or "") + f"\n[Cancelled by {getattr(current_user, 'email', 'user')}]"
        
        await db.commit()
        
        logger.info(f"Action {action_id} cancelled")
        
        return {"action_id": action_id, "status": "cancelled"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error cancelling action {action_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=ManualRunResponse)
async def manual_run(
    request: ManualRunRequest = ManualRunRequest(),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["admin"])),
):
    """
    Trigger a manual optimization run immediately.
    
    This runs the optimization loop synchronously and returns results.
    
    Requires: admin role
    """
    try:
        start_time = datetime.utcnow()
        svc = OptimizationService(db)
        
        # Get campaigns to evaluate
        if request.campaign_ids:
            stmt = select(MetaCampaignModel).where(
                MetaCampaignModel.campaign_id.in_(request.campaign_ids)
            )
        else:
            # Get all active campaigns
            stmt = select(MetaCampaignModel).where(
                MetaCampaignModel.status == "ACTIVE"
            ).limit(50)
        
        result = await db.execute(stmt)
        campaigns = result.scalars().all()
        
        total_actions = 0
        
        for campaign in campaigns:
            try:
                actions = await svc.evaluate_campaign(
                    campaign_id=campaign.campaign_id,
                    lookback_days=request.lookback_days,
                )
                
                for action in actions:
                    await svc.enqueue_action(action, created_by="manual_run")
                    total_actions += 1
            
            except Exception as e:
                logger.error(f"Error evaluating campaign {campaign.campaign_id}: {e}")
                continue
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"Manual run completed: {len(campaigns)} campaigns, {total_actions} actions",
            extra={"campaigns": len(campaigns), "actions": total_actions}
        )
        
        return ManualRunResponse(
            started=True,
            processed_campaigns=len(campaigns),
            actions_suggested=total_actions,
            execution_time_seconds=round(execution_time, 2),
        )
    
    except Exception as e:
        logger.exception(f"Error in manual run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import for manual_run endpoint
from app.models.database import MetaCampaignModel
