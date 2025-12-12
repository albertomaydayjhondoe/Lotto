"""Campaigns Engine - Clip Selection & Campaign Orchestration.

This module provides intelligent clip selection and automated campaign creation
by integrating with the Rule Engine 2.0 to evaluate clips and create draft campaigns.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns_engine.schemas import (
    BestClipDecision,
    OrchestrateCampaignResponse,
)
from app.campaigns_engine.selector import (
    select_best_clip_for_platform,
    select_best_clips_for_platforms,
    get_best_clip_decision,
)
from app.campaigns_engine.services import create_internal_campaigns_for_decisions


__all__ = [
    "orchestrate_campaigns_for_video",
    "get_best_clip_decision",
    "BestClipDecision",
    "OrchestrateCampaignResponse",
]


async def orchestrate_campaigns_for_video(
    db: AsyncSession,
    video_asset_id: UUID,
    platforms: list[str],
) -> OrchestrateCampaignResponse:
    """
    Complete orchestration workflow: select best clips and create campaigns.
    
    This is the high-level function that:
    1. Selects best clip for each platform using Rule Engine
    2. Creates internal draft campaigns for each decision
    3. Returns comprehensive response
    
    Args:
        db: Database session
        video_asset_id: UUID of the video asset
        platforms: List of platforms (e.g., ["tiktok", "instagram", "youtube"])
    
    Returns:
        OrchestrateCampaignResponse with decisions and campaign IDs
    
    Raises:
        ValueError: If no READY clips found for the video asset
    """
    # Select best clips for all platforms
    decisions = await select_best_clips_for_platforms(
        db=db,
        video_asset_id=video_asset_id,
        platforms=platforms
    )
    
    # Create internal campaigns
    campaign_ids = await create_internal_campaigns_for_decisions(
        db=db,
        decisions=decisions
    )
    
    return OrchestrateCampaignResponse(
        decisions=decisions,
        campaigns_created=campaign_ids
    )
