"""
REST API endpoints for Meta Targeting Optimizer.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.auth import require_role
from app.meta_targeting_optimizer.optimizer import MetaTargetingOptimizer
from app.meta_targeting_optimizer.models import (
    MetaTargetingRecommendationModel,
    MetaTargetingHistoryModel,
    MetaTargetingSegmentScoreModel,
)
from app.meta_targeting_optimizer.schemas import (
    RunOptimizationRequest,
    RunOptimizationResponse,
    OptimizationStatus,
    ApplyTargetingRequest,
    ApplyTargetingResponse,
    TargetingRecommendation,
    TargetingHistoryEntry,
    SegmentPerformanceSummary,
    SegmentType,
)

router = APIRouter(prefix="/meta/targeting", tags=["meta_targeting_optimizer"])


@router.post("/run", response_model=RunOptimizationResponse)
async def run_targeting_optimization(
    request: RunOptimizationRequest,
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["admin", "manager"]))
):
    """
    Run targeting optimization for campaign(s).
    
    **RBAC:** admin, manager
    
    Generates targeting recommendations using Bayesian scoring,
    geo allocation, and audience building.
    """
    try:
        optimizer = MetaTargetingOptimizer(db=db, mode=request.mode)
        
        result = await optimizer.run_optimization(
            campaign_id=request.campaign_id,
            force_refresh=request.force_refresh
        )
        
        return RunOptimizationResponse(
            run_id=result["run_id"],
            status=OptimizationStatus.COMPLETED,
            campaign_ids=result["campaign_ids"],
            recommendations_count=result["recommendations_count"],
            duration_ms=result["duration_ms"],
            message=f"Generated {result['recommendations_count']} recommendations in {result['duration_ms']}ms"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get("/recommendations/{campaign_id}", response_model=TargetingRecommendation)
async def get_targeting_recommendation(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["admin", "manager"]))
):
    """
    Get latest targeting recommendation for a campaign.
    
    **RBAC:** admin, manager
    """
    optimizer = MetaTargetingOptimizer(db=db)
    recommendation = await optimizer.get_recommendation(campaign_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recommendation found for campaign {campaign_id}"
        )
    
    return recommendation


@router.post("/apply/{recommendation_id}", response_model=ApplyTargetingResponse)
async def apply_targeting_recommendation(
    recommendation_id: int,
    request: ApplyTargetingRequest,
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["admin", "manager"]))
):
    """
    Apply targeting recommendation to adset.
    
    **RBAC:** admin, manager
    
    In STUB mode: simulates application.
    In LIVE mode: calls Meta API to update targeting.
    """
    try:
        optimizer = MetaTargetingOptimizer(db=db, mode=request.mode)
        
        result = await optimizer.apply_recommendation(
            recommendation_id=recommendation_id,
            dry_run=request.dry_run
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return ApplyTargetingResponse(
            recommendation_id=str(recommendation_id),
            adset_id=result["adset_id"],
            success=True,
            applied_changes=result["applied_changes"],
            message=result["message"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply recommendation: {str(e)}"
        )


@router.get("/segments", response_model=List[SegmentPerformanceSummary])
async def get_segment_performance(
    segment_type: Optional[SegmentType] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["admin", "manager"]))
):
    """
    Get segment performance scores.
    
    **RBAC:** admin, manager
    
    Returns top-performing segments by type (interest, behavior, etc).
    """
    query = select(MetaTargetingSegmentScoreModel).order_by(
        desc(MetaTargetingSegmentScoreModel.composite_score)
    )
    
    if segment_type:
        query = query.where(MetaTargetingSegmentScoreModel.segment_type == segment_type.value)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    segments = result.scalars().all()
    
    summaries = []
    for seg in segments:
        summaries.append(SegmentPerformanceSummary(
            segment_id=seg.segment_id,
            segment_name=seg.segment_name,
            segment_type=SegmentType(seg.segment_type),
            total_impressions=seg.impressions,
            total_clicks=seg.clicks,
            total_conversions=seg.conversions,
            total_spend=seg.spend,
            total_revenue=seg.revenue,
            avg_ctr=seg.ctr,
            avg_cvr=seg.cvr,
            avg_roas=seg.roas,
            campaigns_count=seg.campaigns_used_count,
            last_used=seg.last_used_at,
            is_fatigued=seg.is_fatigued,
            fatigue_reason=seg.fatigue_reason,
        ))
    
    return summaries


@router.get("/history", response_model=List[TargetingHistoryEntry])
async def get_targeting_history(
    campaign_id: Optional[str] = None,
    adset_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user = Depends(require_role(["admin", "manager"]))
):
    """
    Get targeting change history.
    
    **RBAC:** admin, manager
    
    Returns audit log of all targeting changes applied.
    """
    query = select(MetaTargetingHistoryModel).order_by(
        desc(MetaTargetingHistoryModel.applied_at)
    )
    
    if campaign_id:
        query = query.where(MetaTargetingHistoryModel.campaign_id == campaign_id)
    
    if adset_id:
        query = query.where(MetaTargetingHistoryModel.adset_id == adset_id)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    entries = []
    for h in history:
        entries.append(TargetingHistoryEntry(
            id=h.id,
            run_id=h.run_id,
            campaign_id=h.campaign_id,
            adset_id=h.adset_id,
            applied_at=h.applied_at,
            old_targeting=h.old_targeting,
            new_targeting=h.new_targeting,
            before_ctr=h.before_ctr,
            before_cvr=h.before_cvr,
            before_roas=h.before_roas,
            after_ctr=h.after_ctr,
            after_cvr=h.after_cvr,
            after_roas=h.after_roas,
            success=h.success,
            error_message=h.error_message,
        ))
    
    return entries


@router.get("/health")
async def targeting_optimizer_health():
    """
    Health check for targeting optimizer.
    
    **Public endpoint** - no authentication required.
    """
    return {
        "status": "healthy",
        "service": "meta_targeting_optimizer",
        "version": "1.0.0",
        "mode": "stub",
    }
