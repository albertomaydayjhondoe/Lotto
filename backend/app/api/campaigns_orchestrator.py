"""API endpoints for campaigns orchestrator."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import VideoAsset
from app.campaigns_engine import orchestrate_campaigns_for_video, get_best_clip_decision
from app.campaigns_engine.schemas import (
    OrchestrateCampaignRequest,
    OrchestrateCampaignResponse,
    BestClipDecision,
)
from app.auth.permissions import require_role


router = APIRouter(prefix="/campaigns")


@router.post("/orchestrate", response_model=OrchestrateCampaignResponse)
async def orchestrate_campaigns(
    request: OrchestrateCampaignRequest,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Orchestrate campaigns for a video asset.
    
    Selects best clips for each platform using Rule Engine 2.0 and creates
    internal draft campaigns ready for Meta Ads integration.
    
    Args:
        request: OrchestrateCampaignRequest with video_asset_id and platforms
        db: Database session
    
    Returns:
        OrchestrateCampaignResponse with decisions and campaign IDs
    
    Raises:
        HTTPException 404: Video asset not found
        HTTPException 400: No READY clips found
    """
    # Validate video asset exists
    stmt = select(VideoAsset).where(VideoAsset.id == request.video_asset_id)
    result = await db.execute(stmt)
    video_asset = result.scalar_one_or_none()
    
    if not video_asset:
        raise HTTPException(
            status_code=404,
            detail=f"Video asset {request.video_asset_id} not found"
        )
    
    # Orchestrate campaigns
    try:
        response = await orchestrate_campaigns_for_video(
            db=db,
            video_asset_id=request.video_asset_id,
            platforms=request.platforms
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/best_clip", response_model=BestClipDecision)
async def get_best_clip(
    video_asset_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get the best clip decision for a video asset and platform.
    
    This is a READ-ONLY endpoint that returns existing decisions from the database.
    It does NOT recalculate or trigger new evaluations.
    
    To create new decisions, use POST /campaigns/orchestrate.
    
    Args:
        video_asset_id: UUID of the video asset
        platform: Platform name (tiktok, instagram, youtube)
        db: Database session
    
    Returns:
        BestClipDecision with clip_id, score, and decided_at
    
    Raises:
        HTTPException 404: No decision found for this video_asset_id + platform
    """
    decision = await get_best_clip_decision(
        db=db,
        video_asset_id=video_asset_id,
        platform=platform
    )
    
    if not decision:
        raise HTTPException(
            status_code=404,
            detail=f"No best clip decision found for video_asset_id={video_asset_id} platform={platform}"
        )
    
    return decision
