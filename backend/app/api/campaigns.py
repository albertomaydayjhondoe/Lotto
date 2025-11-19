"""
Campaigns endpoint handler.
POST /campaigns - Create a campaign
GET /campaigns - List campaigns
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.models.schemas import Campaign as CampaignSchema, CampaignCreate
from app.models.database import Campaign, Clip, CampaignStatus
from app.core.database import get_db

router = APIRouter()


@router.post("/campaigns", response_model=CampaignSchema, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or preview a campaign.
    
    Args:
        campaign_data: Campaign creation data
        db: Database session
        
    Returns:
        Created Campaign object
    """
    # Check clip exists
    result = await db.execute(
        select(Clip).where(Clip.id == campaign_data.clip_id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="clip not found"
        )
    
    # Create campaign
    campaign = Campaign(
        id=uuid4(),
        name=campaign_data.name,
        clip_id=campaign_data.clip_id,
        budget_cents=campaign_data.budget_cents,
        targeting=campaign_data.targeting.model_dump() if campaign_data.targeting else None,
        status=CampaignStatus.DRAFT
    )
    
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    
    return CampaignSchema.model_validate(campaign)


@router.get("/campaigns", response_model=List[CampaignSchema])
async def list_campaigns(
    db: AsyncSession = Depends(get_db)
):
    """
    List all campaigns.
    
    Args:
        db: Database session
        
    Returns:
        List of Campaign objects
    """
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    
    return [CampaignSchema.model_validate(campaign) for campaign in campaigns]
