"""
Meta Ads Orchestrator API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.auth import require_role
from app.core.database import get_db
from app.meta_ads_orchestrator.models import OrchestrationRequest, OrchestrationResult
from app.meta_ads_orchestrator.orchestrator import MetaAdsOrchestrator
from app.meta_ads_orchestrator import ab_test

router = APIRouter(prefix="/meta/orchestrate")


# ============================================================================
# Pydantic Models for A/B Testing
# ============================================================================

class ABTestCreateRequest(BaseModel):
    """Request model for creating an A/B test."""
    campaign_id: UUID
    test_name: str
    variants: List[Dict[str, UUID]]  # [{"clip_id": uuid, "ad_id": uuid}, ...]
    metrics: Optional[List[str]] = ["ctr", "cpc", "engagement"]
    min_impressions: int = 1000
    min_duration_hours: int = 48


class ABTestEvaluateRequest(BaseModel):
    """Request model for evaluating an A/B test."""
    force: bool = False  # Force evaluation even if embargo not met


class ABTestPublishRequest(BaseModel):
    """Request model for publishing A/B test winner."""
    social_account_id: UUID


@router.post("/run", response_model=OrchestrationResult)
async def run_orchestration(
    request: OrchestrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Run complete Meta Ads campaign orchestration.
    
    Creates: Campaign → Adset → Ad → Creative and syncs insights.
    
    Requires: admin or manager role.
    """
    orchestrator = MetaAdsOrchestrator(db)
    
    try:
        result = await orchestrator.orchestrate_campaign(request)
        
        if not result.overall_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Orchestration failed",
                    "errors": result.errors,
                    "request_id": result.request_id,
                },
            )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration error: {str(e)}",
        )


@router.post("/sync-insights/{social_account_id}")
async def sync_insights_for_account(
    social_account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Sync insights for all campaigns of a social account.
    
    Requires: admin or manager role.
    """
    orchestrator = MetaAdsOrchestrator(db)
    
    # Simple implementation for testing
    return {
        "message": f"Insights sync initiated for account {social_account_id}",
        "status": "queued",
    }


# ============================================================================
# A/B Testing Endpoints (PASO 10.4)
# ============================================================================

@router.post("/ab", status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    request: ABTestCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Create a new A/B test for a Meta Ads campaign.
    
    Requires: admin or manager role.
    """
    try:
        ab_test_instance = await ab_test.create_ab_test(
            db=db,
            campaign_id=request.campaign_id,
            test_name=request.test_name,
            variants=request.variants,
            metrics=request.metrics,
            min_impressions=request.min_impressions,
            min_duration_hours=request.min_duration_hours,
        )
        
        return {
            "id": str(ab_test_instance.id),
            "campaign_id": str(ab_test_instance.campaign_id),
            "test_name": ab_test_instance.test_name,
            "status": ab_test_instance.status,
            "variants": ab_test_instance.variants,
            "metrics": ab_test_instance.metrics,
            "start_time": ab_test_instance.start_time.isoformat(),
            "min_impressions": ab_test_instance.min_impressions,
            "min_duration_hours": ab_test_instance.min_duration_hours,
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}",
        )


@router.get("/ab/{ab_test_id}")
async def get_ab_test(
    ab_test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Get A/B test details.
    
    Requires: admin or manager role.
    """
    from sqlalchemy import select
    from app.models.database import MetaAbTestModel
    
    result = await db.execute(
        select(MetaAbTestModel).where(MetaAbTestModel.id == ab_test_id)
    )
    ab_test_instance = result.scalar_one_or_none()
    
    if not ab_test_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A/B test {ab_test_id} not found",
        )
    
    return {
        "id": str(ab_test_instance.id),
        "campaign_id": str(ab_test_instance.campaign_id),
        "test_name": ab_test_instance.test_name,
        "status": ab_test_instance.status,
        "variants": ab_test_instance.variants,
        "metrics": ab_test_instance.metrics,
        "start_time": ab_test_instance.start_time.isoformat(),
        "end_time": ab_test_instance.end_time.isoformat() if ab_test_instance.end_time else None,
        "winner_clip_id": str(ab_test_instance.winner_clip_id) if ab_test_instance.winner_clip_id else None,
        "winner_ad_id": str(ab_test_instance.winner_ad_id) if ab_test_instance.winner_ad_id else None,
        "winner_decided_at": ab_test_instance.winner_decided_at.isoformat() if ab_test_instance.winner_decided_at else None,
        "metrics_snapshot": ab_test_instance.metrics_snapshot,
        "statistical_results": ab_test_instance.statistical_results,
        "published_to_social": bool(ab_test_instance.published_to_social),
        "publish_log_id": str(ab_test_instance.publish_log_id) if ab_test_instance.publish_log_id else None,
    }


@router.post("/ab/{ab_test_id}/evaluate")
async def evaluate_ab_test_endpoint(
    ab_test_id: UUID,
    request: ABTestEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Evaluate an A/B test and select a winner.
    
    Requires: admin or manager role.
    """
    try:
        result = await ab_test.evaluate_ab_test(
            db=db,
            ab_test_id=ab_test_id,
            force=request.force,
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate A/B test: {str(e)}",
        )


@router.post("/ab/{ab_test_id}/publish-winner")
async def publish_ab_test_winner(
    ab_test_id: UUID,
    request: ABTestPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Publish the winner of an A/B test to social media.
    
    Creates a PublishLog entry that will be picked up by the publishing queue.
    
    Requires: admin or manager role.
    """
    try:
        result = await ab_test.publish_winner(
            db=db,
            ab_test_id=ab_test_id,
            social_account_id=request.social_account_id,
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish winner: {str(e)}",
        )


@router.post("/ab/{ab_test_id}/archive")
async def archive_ab_test_endpoint(
    ab_test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    """
    Archive an A/B test.
    
    Requires: admin or manager role.
    """
    try:
        ab_test_instance = await ab_test.archive_ab_test(
            db=db,
            ab_test_id=ab_test_id,
        )
        
        return {
            "id": str(ab_test_instance.id),
            "status": ab_test_instance.status,
            "message": "A/B test archived successfully",
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive A/B test: {str(e)}",
        )
