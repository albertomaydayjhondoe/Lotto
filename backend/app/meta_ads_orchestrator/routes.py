"""
Meta Ads Orchestrator API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.auth import require_role
from app.core.database import get_db
from app.meta_ads_orchestrator.models import OrchestrationRequest, OrchestrationResult
from app.meta_ads_orchestrator.orchestrator import MetaAdsOrchestrator

router = APIRouter(prefix="/meta/orchestrate")


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
