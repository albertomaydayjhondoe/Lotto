"""
Meta Ads Orchestrator - Simplified for PASO 10.3
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_ads_client import MetaAdsClient, get_meta_client_for_account
from app.meta_ads_client.mappers import (
    map_campaign_response_to_model_dict,
    map_adset_response_to_model_dict,
    map_ad_response_to_model_dict,
    map_insights_response_to_model_dict,
)
from app.models.database import (
    Clip,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaCreativeModel,
    MetaAdInsightsModel,
)

from .models import (
    OrchestrationRequest,
    OrchestrationResult,
    CampaignCreationResult,
    InsightsSyncResult,
)

logger = logging.getLogger(__name__)


class MetaAdsOrchestrator:
    """High-level orchestrator for Meta Ads campaigns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.action_queue = []
        self.max_retries = 3
        self.retry_delay_seconds = 2
    
    async def orchestrate_campaign(self, request: OrchestrationRequest) -> OrchestrationResult:
        """Orchestrate complete Meta Ads campaign creation."""
        request_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        errors = []
        
        logger.info(f"[{request_id}] Starting orchestration")
        
        result = OrchestrationResult(
            request_id=request_id,
            social_account_id=request.social_account_id,
            clip_id=request.clip_id,
            started_at=started_at,
        )
        
        try:
            await self._validate_clip(request.clip_id)
            client = await get_meta_client_for_account(self.db, request.social_account_id)
            campaign_result = await self._create_campaign_structure(client, request)
            result.campaign_creation = campaign_result
            
            if not campaign_result.success:
                errors.append(f"Campaign creation failed: {campaign_result.error}")
                result.overall_success = False
            
            if campaign_result.success:
                try:
                    insights_result = await self._sync_campaign_insights(
                        client,
                        campaign_result.campaign_db_id,
                        campaign_result.adset_db_id,
                        campaign_result.ad_db_id,
                        campaign_result.ad_meta_id,
                    )
                    result.insights_sync = insights_result
                except Exception as e:
                    logger.warning(f"Insights sync skipped: {e}")
        
        except Exception as e:
            logger.error(f"[{request_id}] Orchestration failed: {e}")
            errors.append(str(e))
            result.overall_success = False
        
        completed_at = datetime.now(timezone.utc)
        result.completed_at = completed_at
        result.duration_seconds = (completed_at - started_at).total_seconds()
        result.errors = errors
        
        return result
    
    async def _validate_clip(self, clip_id: UUID) -> Clip:
        """Validate that clip exists."""
        result = await self.db.execute(select(Clip).where(Clip.id == clip_id))
        clip = result.scalar_one_or_none()
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")
        return clip
    
    async def _create_campaign_structure(self, client: MetaAdsClient, request: OrchestrationRequest) -> CampaignCreationResult:
        """Create complete campaign structure."""
        try:
            status = "ACTIVE" if request.auto_publish else "PAUSED"
            
            # Create campaign
            campaign_response = client.create_campaign(
                name=request.campaign_name,
                objective=request.campaign_objective,
                status=status,
                daily_budget=request.daily_budget_cents,
            )
            
            campaign_dict = map_campaign_response_to_model_dict(
                campaign_response,
                social_account_id=str(request.social_account_id),
            )
            campaign_model = MetaCampaignModel(**campaign_dict)
            self.db.add(campaign_model)
            await self.db.flush()
            
            # Create adset
            start_time = datetime.now(timezone.utc)
            end_time = start_time + timedelta(days=30)
            
            adset_response = client.create_adset(
                name=f"{request.campaign_name} - Adset",
                campaign_id=campaign_response["id"],
                daily_budget=request.daily_budget_cents,
                optimization_goal=request.optimization_goal,
                targeting=request.targeting,
                start_time=start_time,
                end_time=end_time,
                status=status,
            )
            
            adset_dict = map_adset_response_to_model_dict(
                adset_response,
                campaign_db_id=campaign_model.id,
                social_account_id=str(request.social_account_id),
            )
            adset_model = MetaAdsetModel(**adset_dict)
            self.db.add(adset_model)
            await self.db.flush()
            
            # Upload creative
            creative_response = client.upload_creative_from_clip(
                clip_id=str(request.clip_id),
                title=request.creative_title,
                description=request.creative_description,
                landing_url=request.landing_url,
            )
            
            creative_model = MetaCreativeModel(
                social_account_id=request.social_account_id,
                creative_id=creative_response["id"],
                name=creative_response["name"],
                status=creative_response["status"],
                video_id=creative_response.get("video_id"),
                thumbnail_url=creative_response.get("thumbnail_url"),
                call_to_action=creative_response.get("call_to_action"),
                object_story_spec=creative_response.get("object_story_spec"),
            )
            self.db.add(creative_model)
            await self.db.flush()
            
            # Create ad
            ad_response = client.create_ad(
                name=f"{request.campaign_name} - Ad",
                adset_id=adset_response["id"],
                creative_id=creative_response["id"],
                status=status,
            )
            
            ad_dict = map_ad_response_to_model_dict(
                ad_response,
                adset_db_id=adset_model.id,
                social_account_id=str(request.social_account_id),
                creative_id=creative_response["id"],
            )
            ad_model = MetaAdModel(**ad_dict)
            self.db.add(ad_model)
            await self.db.flush()
            
            await self.db.commit()
            
            return CampaignCreationResult(
                campaign_db_id=campaign_model.id,
                campaign_meta_id=campaign_model.campaign_id,
                adset_db_id=adset_model.id,
                adset_meta_id=adset_model.adset_id,
                ad_db_id=ad_model.id,
                ad_meta_id=ad_model.ad_id,
                creative_db_id=creative_model.id,
                creative_meta_id=creative_model.creative_id,
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Campaign creation failed: {e}")
            await self.db.rollback()
            return CampaignCreationResult(
                campaign_db_id=0,
                campaign_meta_id="",
                adset_db_id=0,
                adset_meta_id="",
                ad_db_id=0,
                ad_meta_id="",
                creative_db_id=0,
                creative_meta_id="",
                success=False,
                error=str(e),
            )
    
    async def _sync_campaign_insights(self, client, campaign_db_id, adset_db_id, ad_db_id, ad_meta_id) -> InsightsSyncResult:
        """Sync insights for created campaign."""
        try:
            insights_list = client.get_insights(
                level="ad",
                object_id=ad_meta_id,
                date_preset="last_7d",
            )
            
            synced_count = 0
            date_range_start = None
            date_range_end = None
            
            for insight_response in insights_list:
                insight_dict = map_insights_response_to_model_dict(
                    insight_response,
                    campaign_db_id=campaign_db_id,
                    adset_db_id=adset_db_id,
                    ad_db_id=ad_db_id,
                )
                
                insight_model = MetaAdInsightsModel(**insight_dict)
                self.db.add(insight_model)
                synced_count += 1
                
                if date_range_start is None or insight_response["date_start"] < date_range_start:
                    date_range_start = insight_response["date_start"]
                if date_range_end is None or insight_response["date_stop"] > date_range_end:
                    date_range_end = insight_response["date_stop"]
            
            await self.db.commit()
            
            return InsightsSyncResult(
                insights_synced=synced_count,
                date_range_start=date_range_start or "N/A",
                date_range_end=date_range_end or "N/A",
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Insights sync failed: {e}")
            await self.db.rollback()
            return InsightsSyncResult(
                insights_synced=0,
                date_range_start="N/A",
                date_range_end="N/A",
                success=False,
                error=str(e),
            )
    
    def add_action_to_queue(self, action):
        self.action_queue.append(action)
    
    async def process_action_queue(self):
        total = len(self.action_queue)
        processed = 0
        failed = 0
        while self.action_queue:
            action = self.action_queue.pop(0)
            try:
                processed += 1
            except:
                failed += 1
        return {"total": total, "processed": processed, "failed": failed}
