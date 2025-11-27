"""
FastAPI Router for Meta RT Performance Engine (PASO 10.14)

REST API endpoints for real-time performance monitoring and actions.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import require_role
from app.meta_rt_engine.schemas import (
    RTRunRequest,
    RTRunResponse,
    RTHealthResponse,
    RTLatestResponse,
    RTLogResponse,
    RTLogEntry,
    ActionRequest,
    ActionResponse,
    PerformanceSnapshot,
    PerformanceMetrics,
    SeverityLevel,
)
from app.meta_rt_engine.detector import RealTimeDetector
from app.meta_rt_engine.decision_engine import RealTimeDecisionEngine
from app.meta_rt_engine.actions import RealTimeActionsLayer

router = APIRouter()


@router.get("/health", response_model=RTHealthResponse)
async def get_rt_health(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """
    Get RT Engine health status.
    
    Returns:
        RT Health Response with system status
    """
    # TODO: Get real metrics from DB
    return RTHealthResponse(
        status="healthy",
        last_run=datetime.utcnow(),
        last_run_duration_ms=250,
        active_campaigns=15,
        snapshots_last_hour=12,
        anomalies_last_hour=3,
        actions_last_hour=1,
        components={
            "detector": "ok",
            "decision_engine": "ok",
            "actions": "ok",
        },
        timestamp=datetime.utcnow(),
    )


@router.get("/latest/{campaign_id}", response_model=RTLatestResponse)
async def get_latest_rt_data(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """
    Get latest RT data for a specific campaign.
    
    Args:
        campaign_id: Campaign UUID
    
    Returns:
        Latest snapshot, detection, decision, and actions
    """
    # TODO: Query DB for latest RT data
    return RTLatestResponse(
        campaign_id=campaign_id,
        latest_snapshot=None,
        latest_detection=None,
        latest_decision=None,
        latest_actions=[],
        last_update=datetime.utcnow(),
    )


@router.get("/logs", response_model=RTLogResponse)
async def get_rt_logs(
    campaign_id: Optional[UUID] = Query(None),
    log_type: Optional[str] = Query(None, description="detection, decision, action, error"),
    severity: Optional[SeverityLevel] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """
    Get RT logs with filtering and pagination.
    
    Args:
        campaign_id: Filter by campaign (optional)
        log_type: Filter by log type (optional)
        severity: Filter by severity (optional)
        page: Page number
        page_size: Page size
    
    Returns:
        Paginated RT logs
    """
    # TODO: Query DB with filters
    return RTLogResponse(
        logs=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@router.post("/run", response_model=RTRunResponse)
async def run_rt_engine(
    request: RTRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """
    Manually trigger RT engine run.
    
    Args:
        request: RT Run request with configuration
    
    Returns:
        RT Run response with results
    """
    start_time = datetime.utcnow()
    
    # Initialize components
    detector = RealTimeDetector(mode="stub")
    decision_engine = RealTimeDecisionEngine(mode="stub")
    actions_layer = RealTimeActionsLayer(mode="stub")
    
    # Get campaigns to analyze
    if request.campaign_ids:
        campaign_ids = request.campaign_ids
    else:
        # TODO: Get all active campaigns from DB
        campaign_ids = [uuid.uuid4() for _ in range(5)]
    
    snapshots_created = 0
    anomalies_detected = 0
    critical_anomalies = 0
    decisions_made = 0
    actions_executed = 0
    
    try:
        for campaign_id in campaign_ids:
            # Create snapshot
            snapshot = PerformanceSnapshot(
                campaign_id=campaign_id,
                ad_account_id="act_123456789",
                timestamp=datetime.utcnow(),
                window_minutes=request.window_minutes,
                metrics=PerformanceMetrics(
                    impressions=1000,
                    clicks=30,
                    conversions=5,
                    spend=50.0,
                    ctr=0.03,
                    cvr=0.167,
                    cpm=50.0,
                    cpc=1.67,
                    cpa=10.0,
                    roas=3.0,
                    frequency=2.5,
                    reach=400,
                ),
            )
            snapshots_created += 1
            
            # Detect anomalies
            if request.detection_enabled:
                detection_result = await detector.detect_anomalies(
                    campaign_id=campaign_id,
                    current_snapshot=snapshot,
                )
                
                anomalies_detected += len(detection_result.anomalies)
                critical_anomalies += detection_result.critical_count
                
                # Make decisions
                if request.decisions_enabled and detection_result.anomalies:
                    decision = await decision_engine.make_decision(detection_result)
                    decisions_made += 1
                    
                    # Execute actions
                    if request.actions_enabled and request.auto_apply_actions:
                        action_response = await actions_layer.execute_actions(
                            decision=decision,
                            auto_apply=True,
                        )
                        actions_executed += action_response.successful_actions
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return RTRunResponse(
            run_id=uuid.uuid4(),
            campaigns_analyzed=len(campaign_ids),
            snapshots_created=snapshots_created,
            anomalies_detected=anomalies_detected,
            critical_anomalies=critical_anomalies,
            decisions_made=decisions_made,
            actions_executed=actions_executed,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            summary={
                "detection_enabled": request.detection_enabled,
                "decisions_enabled": request.decisions_enabled,
                "actions_enabled": request.actions_enabled,
                "auto_apply": request.auto_apply_actions,
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RT Engine run failed: {str(e)}",
        )


@router.post("/actions/apply", response_model=ActionResponse)
async def apply_rt_actions(
    request: ActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),  # Admin only for applying actions
):
    """
    Apply real-time actions to a campaign.
    
    Args:
        request: Action request with type and parameters
    
    Returns:
        Action response with execution results
    """
    try:
        actions_layer = RealTimeActionsLayer(mode="stub")
        
        # Create a mock decision for single action execution
        from app.meta_rt_engine.schemas import RealTimeDecision
        
        mock_decision = RealTimeDecision(
            decision_id=uuid.uuid4(),
            campaign_id=request.campaign_id,
            detection_result_id=uuid.uuid4(),
            recommended_actions=[request.action_type],
            rules_triggered=[],
            reasoning="Manual action execution",
            urgency=SeverityLevel.MODERATE,
            should_auto_apply=request.auto_apply,
            estimated_impact={},
            created_at=datetime.utcnow(),
        )
        
        action_response = await actions_layer.execute_actions(
            decision=mock_decision,
            auto_apply=request.auto_apply,
        )
        
        return action_response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Action execution failed: {str(e)}",
        )
