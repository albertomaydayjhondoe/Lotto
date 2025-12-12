"""
Dashboard AI Integration Router.

Provides dashboard-optimized endpoints for AI Global Worker data.
Part of PASO 8.0 implementation.

Endpoints:
- GET /dashboard/ai-integration/last - Get last AI reasoning with dashboard formatting
- GET /dashboard/ai-integration/run - Trigger AI reasoning and return formatted result
- GET /dashboard/ai-integration/history - Get AI reasoning history (stub)
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.core.database import get_db
from app.auth.permissions import require_role
from app.ai_global_worker.runner import get_last_reasoning
from app.ai_global_worker.collector import collect_system_snapshot
from app.ai_global_worker.reasoning import run_full_reasoning
from app.dashboard_ai_integration.formatter import generate_full_dashboard_response


router = APIRouter(prefix="/ai-integration", tags=["dashboard_ai_integration"])


@router.get(
    "/last",
    response_model=Dict[str, Any],
    summary="Get last AI reasoning (dashboard format)",
    description="Returns the most recent AI reasoning with dashboard-optimized formatting"
)
async def get_last_ai_reasoning(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get last AI reasoning output formatted for dashboard.
    
    Returns:
        {
            "reasoning_id": str,
            "timestamp": str (ISO),
            "execution_time_ms": int,
            "health_card": {
                "score": 0-100,
                "status": "critical" | "warning" | "healthy",
                "top_issue": str,
                "color": "red" | "yellow" | "green"
            },
            "recommendations_cards": [
                {
                    "category": str,
                    "priority": str,
                    "title": str,
                    "description": str,
                    "impact": str,
                    "effort": str,
                    "badge_color": str
                }
            ],
            "actions_summary": {
                "total_steps": int,
                "estimated_duration": str,
                "risk_level": str,
                "automated": bool,
                "objective": str,
                "risk_badge_color": str
            },
            "raw": {
                "summary": {...},
                "snapshot": {...}
            }
        }
    
    Protected: admin, manager
    """
    last_reasoning = get_last_reasoning()
    
    if not last_reasoning:
        raise HTTPException(
            status_code=404,
            detail="No AI reasoning available yet. AI Worker may not have run."
        )
    
    return generate_full_dashboard_response(last_reasoning)


@router.get(
    "/run",
    response_model=Dict[str, Any],
    summary="Trigger AI reasoning (dashboard format)",
    description="Manually trigger AI reasoning and return formatted result"
)
async def run_ai_reasoning(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Manually trigger AI reasoning and return dashboard-formatted result.
    
    This endpoint:
    1. Collects fresh system snapshot
    2. Runs full AI reasoning cycle
    3. Formats output for dashboard consumption
    4. Returns formatted result
    
    Returns same format as GET /last endpoint.
    
    Protected: admin, manager
    """
    try:
        start_time = time.time()
        
        # Collect snapshot
        snapshot = await collect_system_snapshot(db)
        
        # Run reasoning
        reasoning_output = await run_full_reasoning(snapshot)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Update execution time in output
        reasoning_output.execution_time_ms = execution_time_ms
        
        # Return formatted response
        return generate_full_dashboard_response(reasoning_output)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI reasoning failed: {str(e)}"
        )


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Get AI reasoning history (stub)",
    description="Get historical AI reasoning runs. Currently returns empty list (stub implementation)."
)
async def get_ai_history(
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get AI reasoning history.
    
    STUB IMPLEMENTATION (PASO 8.0):
    Currently returns an empty list. Full implementation will store
    reasoning outputs in database and return paginated history.
    
    Future implementation will support:
    - Pagination (limit, offset)
    - Filtering by date range
    - Filtering by health score
    - Trend analysis
    
    Protected: admin, manager
    """
    # TODO: Implement database storage and retrieval
    # For now, return empty list as specified in requirements
    return []
