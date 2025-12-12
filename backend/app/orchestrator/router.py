"""
Orchestrator API Router
Exposes orchestrator control and monitoring endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.orchestrator.monitor import monitor_system_state
from app.orchestrator.runner import (
    start_orchestrator,
    stop_orchestrator,
    is_orchestrator_running,
    run_orchestrator_once
)
from app.auth.permissions import require_role


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/snapshot")
async def get_system_snapshot(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    GET /orchestrator/snapshot
    Get current system state snapshot
    """
    snapshot = await monitor_system_state(db)
    
    return {
        "status": "ok",
        "snapshot": snapshot
    }


@router.post("/run-once")
async def run_once(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    POST /orchestrator/run-once
    Run a single orchestrator cycle manually
    Returns: snapshot, decisions, and execution results
    """
    result = await run_orchestrator_once()
    
    return {
        "status": "ok",
        "result": result
    }


@router.post("/enable")
async def enable_orchestrator(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    POST /orchestrator/enable
    Start the orchestrator autonomous loop
    """
    result = await start_orchestrator()
    
    return {
        "status": "ok",
        "orchestrator": result
    }


@router.post("/disable")
async def disable_orchestrator(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    POST /orchestrator/disable
    Stop the orchestrator autonomous loop
    """
    result = await stop_orchestrator()
    
    return {
        "status": "ok",
        "orchestrator": result
    }


@router.get("/status")
async def get_orchestrator_status(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    GET /orchestrator/status
    Check if orchestrator is running
    """
    is_running = is_orchestrator_running()
    
    return {
        "status": "ok",
        "running": is_running
    }
