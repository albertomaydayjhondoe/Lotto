"""
AI Global Worker API Router.

Exposes endpoints for:
- Querying last AI reasoning output
- Triggering manual reasoning
- Accessing system snapshot
- Getting recommendations, summary, action plans
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.permissions import require_role
from app.ai_global_worker.collector import collect_system_snapshot
from app.ai_global_worker.reasoning import run_full_reasoning
from app.ai_global_worker.runner import get_last_reasoning
from app.ai_global_worker.schemas import (
    AIReasoningOutput,
    SystemSnapshot,
    AISummary,
    AIActionPlan,
    AIRecommendation,
    AIRunResponse
)
from typing import List


router = APIRouter(prefix="/ai/global", tags=["ai_global_worker"])


@router.get(
    "/last_run",
    response_model=AIReasoningOutput,
    summary="Get last AI reasoning output",
    description="Returns the most recent AI reasoning output from the background worker"
)
async def get_last_run(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get the last AI reasoning output.
    
    Returns the most recently generated reasoning from the background
    AI worker. Returns 404 if worker hasn't run yet.
    
    Protected: admin, manager
    """
    last_reasoning = get_last_reasoning()
    
    if not last_reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning available yet. Worker may not have run."
        )
    
    return last_reasoning


@router.post(
    "/run",
    response_model=AIRunResponse,
    summary="Manually trigger AI reasoning",
    description="Triggers immediate AI reasoning cycle and returns result"
)
async def manual_run(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Manually trigger AI reasoning.
    
    Collects fresh system snapshot and generates new reasoning output.
    Useful for on-demand analysis or testing.
    
    Protected: admin, manager
    """
    try:
        start_time = time.time()
        
        # Collect snapshot
        snapshot = await collect_system_snapshot(db)
        
        # Run reasoning
        reasoning_output = await run_full_reasoning(snapshot)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return AIRunResponse(
            success=True,
            reasoning_id=reasoning_output.reasoning_id,
            message=f"AI reasoning completed successfully. Health: {reasoning_output.summary.overall_health}",
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI reasoning failed: {str(e)}"
        )


@router.get(
    "/snapshot",
    response_model=SystemSnapshot,
    summary="Get current system snapshot",
    description="Returns current system state without AI reasoning"
)
async def get_snapshot(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get current system snapshot.
    
    Collects and returns system metrics without running AI reasoning.
    Useful for inspecting raw data.
    
    Protected: admin, manager
    """
    try:
        snapshot = await collect_system_snapshot(db)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect snapshot: {str(e)}"
        )


@router.get(
    "/recommendations",
    response_model=List[AIRecommendation],
    summary="Get AI recommendations only",
    description="Returns only the recommendations from last AI reasoning"
)
async def get_recommendations(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get AI recommendations only.
    
    Returns the prioritized list of recommendations from the last
    AI reasoning cycle.
    
    Protected: admin, manager
    """
    last_reasoning = get_last_reasoning()
    
    if not last_reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning available yet"
        )
    
    return last_reasoning.recommendations


@router.get(
    "/summary",
    response_model=AISummary,
    summary="Get AI summary only",
    description="Returns only the system summary from last AI reasoning"
)
async def get_summary(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get AI summary only.
    
    Returns the system health summary from the last AI reasoning cycle.
    
    Protected: admin, manager
    """
    last_reasoning = get_last_reasoning()
    
    if not last_reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning available yet"
        )
    
    return last_reasoning.summary


@router.get(
    "/action-plan",
    response_model=AIActionPlan,
    summary="Get AI action plan only",
    description="Returns only the action plan from last AI reasoning"
)
async def get_action_plan(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get AI action plan only.
    
    Returns the proposed action plan from the last AI reasoning cycle.
    
    Protected: admin, manager
    """
    last_reasoning = get_last_reasoning()
    
    if not last_reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning available yet"
        )
    
    return last_reasoning.action_plan
