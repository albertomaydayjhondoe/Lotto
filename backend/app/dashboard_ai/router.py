"""
Dashboard AI Router

FastAPI endpoints for AI analysis, recommendations, and action execution.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from .models import SystemAnalysis, Recommendation, ExecuteActionRequest, ExecuteActionResponse
from .analyzer import analyze_system
from .recommender import generate_recommendations
from app.dashboard_actions.executor import execute_action

router = APIRouter(prefix="/ai", tags=["dashboard_ai"])


@router.get("/analyze", response_model=SystemAnalysis)
async def get_analysis(db: AsyncSession = Depends(get_db)):
    """
    Get complete system analysis with health metrics and detected issues.
    
    Returns:
        SystemAnalysis object with:
        - Health statuses (queue, orchestrator, campaigns)
        - Success rates
        - Best clips per platform
        - Detected issues
        - Additional metrics
        
    Example:
        ```
        GET /dashboard/ai/analyze
        
        {
            "timestamp": "2025-11-22T10:30:00",
            "queue_health": "good",
            "orchestrator_health": "warning",
            "campaigns_status": "good",
            "publish_success_rate": 0.92,
            "pending_scheduled": 15,
            "best_clip_per_platform": {...},
            "issues_detected": [...]
        }
        ```
    """
    try:
        analysis = await analyze_system(db)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze system: {str(e)}"
        )


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """
    Get AI-generated recommendations based on system analysis.
    
    Returns:
        List of Recommendation objects sorted by severity (critical first).
        Each recommendation includes:
        - title: Short description
        - description: Detailed explanation
        - severity: info | warning | critical
        - action: Action type to execute
        - payload: Action-specific data
        
    Example:
        ```
        GET /dashboard/ai/recommendations
        
        [
            {
                "id": "uuid",
                "title": "Publish high-scoring Instagram clip",
                "description": "Clip with score 0.95 ready",
                "severity": "info",
                "action": "publish",
                "payload": {
                    "clip_id": "uuid",
                    "platform": "instagram"
                }
            }
        ]
        ```
    """
    try:
        recommendations = await generate_recommendations(db)
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/execute", response_model=ExecuteActionResponse)
async def execute_ai_action(
    request: ExecuteActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute an AI recommendation or manual action.
    
    Supported actions:
    - publish: Publish a clip
    - retry: Retry failed publications
    - reschedule: Reschedule a publication
    - run_orchestrator: Run orchestrator tick
    - run_scheduler: Run scheduler tick
    - rebalance_queue: Rebalance publishing queue
    - promote: Promote clip to campaign
    - publish_best_clip: Publish best available clip
    - clear_failed: Clear old failed publications
    - optimize_schedule: Optimize scheduling
    
    Args:
        request: ExecuteActionRequest with action type and payload
        
    Returns:
        ExecuteActionResponse with execution result
        
    Example:
        ```
        POST /dashboard/ai/execute
        
        Request:
        {
            "action": "publish",
            "payload": {
                "clip_id": "uuid",
                "platform": "instagram"
            }
        }
        
        Response:
        {
            "success": true,
            "action": "publish",
            "message": "Clip published successfully",
            "result": {...}
        }
        ```
    """
    try:
        result = await execute_action(
            action_type=request.action,
            payload=request.payload,
            db=db
        )
        
        return ExecuteActionResponse(
            success=result.get("success", True),
            action=request.action,
            message=result.get("message", "Action executed successfully"),
            result=result.get("data", {}),
            executed_at=result.get("executed_at")
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {str(e)}"
        )
