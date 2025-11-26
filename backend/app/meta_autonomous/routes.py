"""
API Routes for Meta Autonomous System
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.core.database import get_db
from app.auth import require_role
from .auto_worker import MetaAutoWorker
from .policy_engine import PolicyEngine
from .safety import SafetyEngine
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta/autonomous", tags=["meta-autonomous"])

# Global worker instance (will be initialized in main.py)
_worker: Optional[MetaAutoWorker] = None


def set_worker(worker: MetaAutoWorker) -> None:
    """Set the global worker instance."""
    global _worker
    _worker = worker


# ============================================================================
# Request/Response Models
# ============================================================================

class ManualTickResponse(BaseModel):
    """Response from manual tick execution."""
    success: bool
    tick_started_at: str
    tick_completed_at: str
    campaigns_evaluated: int
    actions_generated: int
    actions_policy_blocked: int
    actions_safety_blocked: int
    actions_queued: int
    actions_executed: int
    actions_failed: int
    errors: list[str]


class WorkerStatusResponse(BaseModel):
    """Current status of the autonomous worker."""
    enabled: bool
    mode: str  # suggest | auto
    is_running: bool
    interval_seconds: int
    max_daily_spend_usd: float
    max_actions_per_tick: int
    hard_stop_roas: float
    embargo_hours: int


class PolicyResponse(BaseModel):
    """Current policy configuration."""
    max_daily_change_pct: float
    max_auto_change_pct: float
    hard_stop_roas: float
    hard_stop_confidence: float
    min_impressions: int
    min_spend_usd: float
    min_age_hours: int
    creative_embargo_hours: int
    min_spain_percentage: float
    max_single_country_pct: float
    require_human_approval_creatives: bool


class ToggleModeRequest(BaseModel):
    """Request to change worker mode."""
    mode: str = Field(..., pattern="^(suggest|auto)$", description="New mode: suggest or auto")


class ToggleModeResponse(BaseModel):
    """Response from mode toggle."""
    success: bool
    old_mode: str
    new_mode: str
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/run-once", response_model=ManualTickResponse)
async def manual_tick(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin"))
) -> ManualTickResponse:
    """
    Manually trigger one autonomous optimization cycle.
    
    Admin only. Useful for testing and debugging.
    
    Returns:
        Statistics from the tick execution
    """
    if not _worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autonomous worker not initialized"
        )
    
    logger.info("Manual tick requested by admin")
    
    try:
        stats = await _worker.tick()
        
        return ManualTickResponse(
            success=True,
            tick_started_at=stats["tick_started_at"],
            tick_completed_at=stats["tick_completed_at"],
            campaigns_evaluated=stats["campaigns_evaluated"],
            actions_generated=stats["actions_generated"],
            actions_policy_blocked=stats["actions_policy_blocked"],
            actions_safety_blocked=stats["actions_safety_blocked"],
            actions_queued=stats["actions_queued"],
            actions_executed=stats["actions_executed"],
            actions_failed=stats["actions_failed"],
            errors=stats["errors"],
        )
        
    except Exception as e:
        logger.error(f"Manual tick failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual tick failed: {str(e)}"
        )


@router.get("/status", response_model=WorkerStatusResponse)
async def get_status(
    _user=Depends(require_role("manager"))
) -> WorkerStatusResponse:
    """
    Get current status of the autonomous worker.
    
    Returns:
        Worker configuration and runtime status
    """
    is_running = _worker.is_running if _worker else False
    
    return WorkerStatusResponse(
        enabled=settings.META_AUTO_ENABLED,
        mode=settings.META_AUTO_MODE,
        is_running=is_running,
        interval_seconds=settings.META_AUTO_INTERVAL_SECONDS,
        max_daily_spend_usd=settings.MAX_DAILY_SPEND_USD,
        max_actions_per_tick=settings.MAX_ACTIONS_PER_TICK,
        hard_stop_roas=settings.HARD_STOP_ROAS,
        embargo_hours=settings.MIN_AGE_HOURS,
    )


@router.get("/policies", response_model=PolicyResponse)
async def get_policies(
    _user=Depends(require_role("manager"))
) -> PolicyResponse:
    """
    Get current policy engine configuration.
    
    Returns:
        All policy thresholds and rules
    """
    return PolicyResponse(
        max_daily_change_pct=settings.MAX_DAILY_CHANGE_PCT,
        max_auto_change_pct=settings.MAX_AUTO_CHANGE_PCT,
        hard_stop_roas=settings.HARD_STOP_ROAS,
        hard_stop_confidence=settings.HARD_STOP_CONFIDENCE,
        min_impressions=settings.MIN_IMPRESSIONS,
        min_spend_usd=settings.MIN_SPEND_USD,
        min_age_hours=settings.MIN_AGE_HOURS,
        creative_embargo_hours=settings.CREATIVE_EMBARGO_HOURS,
        min_spain_percentage=settings.MIN_SPAIN_PERCENTAGE,
        max_single_country_pct=settings.MAX_SINGLE_COUNTRY_PCT,
        require_human_approval_creatives=settings.REQUIRE_HUMAN_APPROVAL_CREATIVES,
    )


@router.post("/toggle-mode", response_model=ToggleModeResponse)
async def toggle_mode(
    request: ToggleModeRequest,
    _user=Depends(require_role("admin"))
) -> ToggleModeResponse:
    """
    Toggle between suggest and auto modes.
    
    Admin only. Changes take effect immediately.
    
    **suggest mode**: Generate recommendations for human approval
    **auto mode**: Execute safe actions automatically
    
    Args:
        request: New mode (suggest or auto)
        
    Returns:
        Confirmation with old and new modes
    """
    old_mode = settings.META_AUTO_MODE
    new_mode = request.mode
    
    if old_mode == new_mode:
        return ToggleModeResponse(
            success=True,
            old_mode=old_mode,
            new_mode=new_mode,
            message=f"Already in {new_mode} mode"
        )
    
    # Update settings
    settings.META_AUTO_MODE = new_mode
    
    logger.warning(f"Mode changed: {old_mode} → {new_mode}")
    
    return ToggleModeResponse(
        success=True,
        old_mode=old_mode,
        new_mode=new_mode,
        message=f"Mode changed from {old_mode} to {new_mode}. Changes take effect on next tick."
    )


@router.post("/start")
async def start_worker(
    _user=Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Start the autonomous worker loop.
    
    Admin only.
    """
    if not _worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autonomous worker not initialized"
        )
    
    if _worker.is_running:
        return {
            "success": False,
            "message": "Worker already running"
        }
    
    _worker.start()
    
    logger.info("Worker started via API")
    
    return {
        "success": True,
        "message": f"Worker started in {settings.META_AUTO_MODE} mode"
    }


@router.post("/stop")
async def stop_worker(
    _user=Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Stop the autonomous worker loop.
    
    Admin only.
    """
    if not _worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autonomous worker not initialized"
        )
    
    if not _worker.is_running:
        return {
            "success": False,
            "message": "Worker not running"
        }
    
    _worker.stop()
    
    logger.info("Worker stopped via API")
    
    return {
        "success": True,
        "message": "Worker stop requested (will complete current tick)"
    }
