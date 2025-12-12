"""Campaign creation and orchestration services."""

import json
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Campaign, CampaignStatus
from app.campaigns_engine.schemas import BestClipDecision
from app.ledger import log_event


async def create_internal_campaigns_for_decisions(
    db: AsyncSession,
    decisions: list[BestClipDecision],
) -> list[str]:
    """
    Create internal draft campaigns for best clip decisions.
    
    Creates one campaign per decision with:
    - status = "draft"
    - name = auto-generated
    - budget_cents = 0 (symbolic)
    - optimization_meta = JSON with orchestrator info
    
    Logs to SocialSyncLedger for each campaign created.
    
    Args:
        db: Database session
        decisions: List of BestClipDecision objects
    
    Returns:
        List of campaign IDs as strings
    """
    campaign_ids = []
    
    for decision in decisions:
        # Create campaign record
        campaign_id = uuid4()
        campaign = Campaign(
            id=campaign_id,
            clip_id=decision.clip_id,
            status=CampaignStatus.DRAFT,
            name=f"{decision.platform.upper()} auto-campaign for {decision.video_asset_id}",
            budget_cents=0,  # Symbolic - to be set later
            targeting=json.dumps({
                "source": "auto_orchestrator",
                "score": decision.score,
                "platform": decision.platform,
                "video_asset_id": str(decision.video_asset_id),
                "decided_at": decision.decided_at.isoformat()
            })
        )
        
        db.add(campaign)
        campaign_ids.append(str(campaign_id))
        
        # Log to ledger
        await log_event(
            db=db,
            event_type="campaign_created_auto",
            entity_type="campaign",
            entity_id=str(campaign_id),
            metadata={
                "platform": decision.platform,
                "clip_id": str(decision.clip_id),
                "video_asset_id": str(decision.video_asset_id),
                "score": decision.score
            }
        )
    
    await db.commit()
    
    return campaign_ids
