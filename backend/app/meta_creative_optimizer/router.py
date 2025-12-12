"""REST API Router for Creative Optimizer (PASO 10.16)"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from app.meta_creative_optimizer import schemas
from app.meta_creative_optimizer.data_collector import UnifiedDataCollector
from app.meta_creative_optimizer.winner_selector import WinnerSelector
from app.meta_creative_optimizer.decision_engine import CreativeDecisionEngine
from app.meta_creative_optimizer.orchestrator_integration import OrchestrationClient
from app.auth import require_role

router = APIRouter()


@router.get("/status", response_model=schemas.OptimizationStatusResponse)
async def get_optimization_status(
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """Get current optimization status"""
    return schemas.OptimizationStatusResponse(
        status="operational",
        last_run=datetime.utcnow(),
        next_run=None,
        total_campaigns=5,
        total_creatives=42,
        current_winner_count=5,
        pending_decisions=3,
        mode="stub",
    )


@router.post("/run", response_model=schemas.RunOptimizationResponse)
async def run_optimization(
    request: schemas.RunOptimizationRequest,
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """Run full optimization cycle"""
    start_time = datetime.utcnow()
    
    # Collect data
    collector = UnifiedDataCollector(mode=request.mode)
    creatives = await collector.collect_all_creatives(request.campaign_ids)
    
    # Select winner
    selector = WinnerSelector(mode=request.mode)
    winner = await selector.select_winner(creatives)
    
    # Make decisions
    engine = CreativeDecisionEngine(mode=request.mode)
    decisions = await engine.make_decisions(creatives, winner)
    
    # Execute orchestrations (stub)
    orchestrator = OrchestrationClient(mode=request.mode)
    orchestrations_executed = 0
    
    end_time = datetime.utcnow()
    processing_time = int((end_time - start_time).total_seconds() * 1000)
    
    return schemas.RunOptimizationResponse(
        optimization_id=uuid4(),
        campaigns_processed=len(request.campaign_ids or [1]),
        creatives_processed=len(creatives),
        winners_selected=1,
        decisions_made=len(decisions),
        actions_recommended=sum(len(d.recommended_actions) for d in decisions),
        orchestrations_executed=orchestrations_executed,
        processing_time_ms=processing_time,
        summary=f"Processed {len(creatives)} creatives, selected winner",
        started_at=start_time,
        completed_at=end_time,
    )


@router.get("/winner", response_model=schemas.CurrentWinnerResponse)
async def get_current_winner(
    campaign_id: UUID,
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """Get current winner for campaign"""
    return schemas.CurrentWinnerResponse(
        campaign_id=campaign_id,
        creative_id=UUID('00000000-0000-0000-0000-000000000001'),
        selected_at=datetime.utcnow(),
        overall_score=85.0,
        roas=4.5,
        ctr=3.2,
        cvr=5.5,
        spend=5000.0,
        conversions=400,
        days_as_winner=3,
        confidence=schemas.DecisionConfidence.HIGH,
    )


@router.post("/promote/{creative_id}", response_model=schemas.PromoteCreativeResponse)
async def promote_creative(
    creative_id: UUID,
    request: schemas.PromoteCreativeRequest,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Manually promote creative to winner"""
    return schemas.PromoteCreativeResponse(
        success=True,
        creative_id=creative_id,
        previous_role=schemas.CreativeRole.TEST,
        new_role=schemas.CreativeRole.WINNER,
        previous_winner_id=UUID('00000000-0000-0000-0000-000000000002'),
        message=f"Creative {creative_id} promoted to winner",
        promoted_at=datetime.utcnow(),
    )


@router.get("/recommendations", response_model=schemas.RecommendationsResponse)
async def get_recommendations(
    priority: Optional[int] = None,
    current_user: dict = Depends(require_role(["admin", "manager"]))
):
    """Get optimization recommendations"""
    recommendations = [
        schemas.RecommendationItem(
            creative_id=UUID('00000000-0000-0000-0000-000000000003'),
            campaign_id=UUID('00000000-0000-0000-0000-000000000001'),
            recommendation_type=schemas.OptimizationAction.GENERATE_VARIANTS,
            priority=1,
            confidence=schemas.DecisionConfidence.HIGH,
            reasoning="Fatigued creative with good base performance",
            estimated_impact=15.0,
            created_at=datetime.utcnow(),
        )
    ]
    
    return schemas.RecommendationsResponse(
        total=len(recommendations),
        high_priority=1,
        medium_priority=0,
        low_priority=0,
        recommendations=recommendations,
        generated_at=datetime.utcnow(),
    )


@router.get("/health-check", response_model=schemas.HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return schemas.HealthCheckResponse(
        status="healthy",
        components={
            "data_collector": "operational",
            "winner_selector": "operational",
            "decision_engine": "operational",
            "orchestrator": "operational",
        },
        version="1.0.0",
        mode="stub",
    )
