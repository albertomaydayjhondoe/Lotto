"""
Meta Ads API Client

Client for interacting with Meta Marketing API (Facebook Ads).
Supports STUB mode (returns fake data) and LIVE mode (real API calls).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pathlib import Path

from .exceptions import MetaAPIError, MetaAuthError, MetaRateLimitError
from .types import (
    CampaignResponse,
    AdSetResponse,
    AdResponse,
    VideoUploadResponse,
    InsightsResponse,
)

logger = logging.getLogger(__name__)


class MetaAdsClient:
    """
    Client for Meta Marketing API (Facebook Ads).
    
    Supports two modes:
    - STUB: Returns fake data for testing/development
    - LIVE: Makes real API calls to Meta (requires valid access token)
    
    Args:
        access_token: Meta API access token
        ad_account_id: Meta Ad Account ID (format: act_1234567890)
        mode: Operation mode ("STUB" or "LIVE")
        api_version: Meta API version (default: "v18.0")
    """
    
    def __init__(
        self,
        access_token: str | None = None,
        ad_account_id: str | None = None,
        mode: Literal["stub", "live"] = "stub",
        api_version: str = "v18.0",
    ):
        # In STUB mode, credentials are optional
        if mode == "live" and (not access_token or not ad_account_id):
            logger.warning("LIVE mode requires access_token and ad_account_id, falling back to stub mode")
            mode = "stub"
        
        self.access_token = access_token or "STUB_TOKEN"
        self.ad_account_id = ad_account_id or "act_STUB_ACCOUNT"
        self.mode = mode
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        
        logger.info(
            f"Initialized MetaAdsClient in {mode} mode for account {self.ad_account_id}"
        )
    
    def _validate_token(self) -> bool:
        """
        Validate the access token.
        
        Returns:
            True if token is valid
            
        Raises:
            MetaAuthError: If token is invalid
        """
        if self.mode == "stub":
            logger.info("[STUB] Token validation - returning True")
            return True
        
        # TODO: LIVE mode - Implement token validation
        # Endpoint: GET /debug_token?input_token={token}&access_token={app_token}
        # Check response.data.is_valid and response.data.scopes
        raise NotImplementedError("Token validation not implemented in LIVE mode")
    
    def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = "PAUSED",
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        special_ad_categories: list[str] | None = None,
    ) -> CampaignResponse:
        """
        Create a new campaign in Meta Ads.
        
        Args:
            name: Campaign name
            objective: Campaign objective (e.g., "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT")
            status: Initial status ("ACTIVE" or "PAUSED")
            daily_budget: Daily budget in cents (e.g., 10000 = $100)
            lifetime_budget: Lifetime budget in cents
            special_ad_categories: Special ad categories if applicable
            
        Returns:
            CampaignResponse with campaign data
            
        Raises:
            MetaAPIError: If campaign creation fails
        """
        # Validate parameters
        if not name or not name.strip():
            raise MetaAPIError("Campaign name cannot be empty")
        
        if daily_budget is not None and daily_budget < 0:
            raise MetaAPIError("daily_budget must be positive")
        
        if lifetime_budget is not None and lifetime_budget < 0:
            raise MetaAPIError("lifetime_budget must be positive")
        
        if self.mode == "stub":
            logger.info(f"[STUB] Creating campaign: {name}")
            
            from uuid import uuid4
            campaign_id = f"META_CAMPAIGN_{uuid4().hex[:16]}"
            
            return CampaignResponse(
                id=campaign_id,
                name=name,
                account_id=self.ad_account_id,
                status=status,
                objective=objective,
                daily_budget=str(daily_budget) if daily_budget else None,
                lifetime_budget=str(lifetime_budget) if lifetime_budget else None,
                bid_strategy="LOWEST_COST_WITHOUT_CAP",
                created_time=datetime.now(timezone.utc).isoformat(),
                updated_time=datetime.now(timezone.utc).isoformat(),
                effective_status=status,
            )
        
        # TODO: LIVE mode - Implement campaign creation
        # Endpoint: POST /{ad_account_id}/campaigns
        # Required params: name, objective, status, special_ad_categories
        # Optional params: daily_budget, lifetime_budget, bid_strategy, start_time, stop_time
        # Response: {"id": "campaign_id"}
        # Then fetch full campaign data: GET /{campaign_id}?fields=id,name,status,objective,created_time,updated_time,daily_budget,lifetime_budget,bid_strategy,effective_status
        raise NotImplementedError("Campaign creation not implemented in LIVE mode")
    
    def create_adset(
        self,
        name: str,
        campaign_id: str,
        optimization_goal: str,
        billing_event: str,
        bid_amount: int | None = None,
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        targeting: dict[str, Any] | None = None,
        status: str = "PAUSED",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> AdSetResponse:
        """
        Create a new ad set in Meta Ads.
        
        Args:
            name: AdSet name
            campaign_id: Parent campaign ID
            optimization_goal: Optimization goal (e.g., "LINK_CLICKS", "IMPRESSIONS")
            billing_event: Billing event (e.g., "IMPRESSIONS", "LINK_CLICKS")
            bid_amount: Bid amount in cents
            daily_budget: Daily budget in cents
            lifetime_budget: Lifetime budget in cents
            targeting: Targeting specification (age, gender, location, interests)
            status: Initial status ("ACTIVE" or "PAUSED")
            start_time: Start datetime for the adset
            end_time: End datetime for the adset
            
        Returns:
            AdSetResponse with adset data
            
        Raises:
            MetaAPIError: If adset creation fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Creating adset: {name}")
            
            from uuid import uuid4
            adset_id = f"META_ADSET_{uuid4().hex[:16]}"
            
            return AdSetResponse(
                id=adset_id,
                name=name,
                campaign_id=campaign_id,
                account_id=self.ad_account_id,
                status=status,
                daily_budget=str(daily_budget) if daily_budget else None,
                lifetime_budget=str(lifetime_budget) if lifetime_budget else None,
                bid_amount=str(bid_amount) if bid_amount else None,
                billing_event=billing_event,
                optimization_goal=optimization_goal,
                targeting=targeting or {},
                start_time=start_time.isoformat() if start_time else None,
                end_time=end_time.isoformat() if end_time else None,
                created_time=datetime.now(timezone.utc).isoformat(),
                updated_time=datetime.now(timezone.utc).isoformat(),
                effective_status=status,
            )
        
        # TODO: LIVE mode - Implement adset creation
        # Endpoint: POST /{ad_account_id}/adsets
        # Required params: name, campaign_id, optimization_goal, billing_event, status
        # Required params: daily_budget OR lifetime_budget (at least one)
        # Required params: targeting (at minimum: {"geo_locations": {"countries": ["US"]}})
        # Optional params: bid_amount, start_time, end_time
        # Response: {"id": "adset_id"}
        # Then fetch full adset data: GET /{adset_id}?fields=id,name,campaign_id,status,optimization_goal,billing_event,daily_budget,lifetime_budget,bid_amount,targeting,created_time,updated_time,effective_status
        raise NotImplementedError("AdSet creation not implemented in LIVE mode")
    
    def create_ad(
        self,
        name: str,
        adset_id: str,
        creative_id: str,
        status: str = "PAUSED",
    ) -> AdResponse:
        """
        Create a new ad in Meta Ads.
        
        Args:
            name: Ad name
            adset_id: Parent adset ID
            creative_id: Creative ID to use for this ad
            status: Initial status ("ACTIVE" or "PAUSED")
            
        Returns:
            AdResponse with ad data
            
        Raises:
            MetaAPIError: If ad creation fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Creating ad: {name}")
            
            from uuid import uuid4
            ad_id = f"META_AD_{uuid4().hex[:16]}"
            
            return AdResponse(
                id=ad_id,
                name=name,
                adset_id=adset_id,
                campaign_id=f"META_CAMPAIGN_from_{adset_id}",
                account_id=self.ad_account_id,
                creative={"id": creative_id},
                status=status,
                effective_status=status,
                created_time=datetime.now(timezone.utc).isoformat(),
                updated_time=datetime.now(timezone.utc).isoformat(),
            )
        
        # TODO: LIVE mode - Implement ad creation
        # Endpoint: POST /{ad_account_id}/ads
        # Required params: name, adset_id, creative (format: {"creative_id": "123456"}), status
        # Optional params: tracking_specs, conversion_specs
        # Response: {"id": "ad_id"}
        # Then fetch full ad data: GET /{ad_id}?fields=id,name,adset_id,campaign_id,status,creative,effective_status,created_time,updated_time
        raise NotImplementedError("Ad creation not implemented in LIVE mode")
    
    def upload_creative_from_clip(
        self,
        clip_id: str,
        title: str,
        description: str | None = None,
        thumbnail_url: str | None = None,
        landing_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload a video creative from a clip.
        
        This is a two-step process in LIVE mode:
        1. Upload video to Meta
        2. Create ad creative using the video
        
        Args:
            clip_id: ID of the clip in the system
            title: Video title
            description: Video description
            thumbnail_url: Thumbnail image URL
            landing_url: Landing page URL for the ad
            
        Returns:
            Dict with creative data including id, video_id, name, status
            
        Raises:
            MetaAPIError: If upload or creative creation fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Uploading creative from clip: {clip_id}")
            
            from uuid import uuid4
            video_id = f"META_VIDEO_{uuid4().hex[:16]}"
            creative_id = f"META_CREATIVE_{uuid4().hex[:16]}"
            
            return {
                "id": creative_id,
                "name": f"Creative: {title}",
                "video_id": video_id,
                "object_story_spec": {
                    "page_id": "stub_page",
                    "video_data": {
                        "video_id": video_id,
                        "title": title,
                        "message": description or "",
                        "call_to_action": {
                            "type": "LEARN_MORE",
                            "value": {"link": landing_url or "https://example.com"}
                        }
                    }
                },
                "thumbnail_url": thumbnail_url or f"https://example.com/thumb_{video_id}.jpg",
                "status": "ACTIVE",
            }
        
        # TODO: LIVE mode - Implement video upload and creative creation
        
        # Step 1: Upload video
        # Endpoint: POST /{ad_account_id}/advideos
        # Use resumable upload for large files:
        # 1. Initialize: POST with file_size parameter
        # 2. Upload chunks: POST with video_file_chunk parameter
        # 3. Finalize: Response contains video_id
        # Fields to include in response: id, title, source, status
        
        # Step 2: Create ad creative with video
        # Endpoint: POST /{ad_account_id}/adcreatives
        # Required params:
        # - name: creative name
        # - object_story_spec: {
        #     "page_id": "{page_id}",
        #     "video_data": {
        #       "video_id": "{video_id}",
        #       "title": "{title}",
        #       "message": "{description}",
        #       "call_to_action": {"type": "LEARN_MORE", "value": {"link": "{url}"}}
        #     }
        #   }
        # Response: {"id": "creative_id"}
        
        raise NotImplementedError("Creative upload not implemented in LIVE mode")
    
    def get_insights(
        self,
        level: Literal["account", "campaign", "adset", "ad"],
        object_id: str | None = None,
        date_preset: str = "last_7d",
        fields: list[str] | None = None,
    ) -> list[InsightsResponse]:
        """
        Get insights (performance metrics) from Meta Ads.
        
        Args:
            level: Level of insights ("account", "campaign", "adset", "ad")
            object_id: ID of the object to get insights for (campaign_id, adset_id, ad_id)
                      Not needed for account level
            date_preset: Date range preset (e.g., "last_7d", "last_30d", "lifetime")
            fields: List of fields to retrieve (defaults to common metrics)
            
        Returns:
            List of InsightsResponse with metrics data
            
        Raises:
            MetaAPIError: If insights request fails
        """
        if fields is None:
            fields = [
                "impressions",
                "clicks",
                "spend",
                "reach",
                "frequency",
                "cpm",
                "cpc",
                "ctr",
                "actions",
            ]
        
        if self.mode == "stub":
            logger.info(f"[STUB] Getting {level} insights for {object_id or 'account'}")
            
            # Generate stub insights data
            return [
                InsightsResponse(
                    date_start="2024-01-01",
                    date_stop="2024-01-07",
                    account_id=self.ad_account_id if level == "account" else None,
                    campaign_id=object_id if level == "campaign" else None,
                    adset_id=object_id if level == "adset" else None,
                    ad_id=object_id if level == "ad" else None,
                    impressions="15234",
                    clicks="342",
                    spend="125.50",
                    reach="12045",
                    frequency="1.26",
                    cpm="8.24",
                    cpc="0.37",
                    ctr="2.25",
                    actions=[
                        {"action_type": "link_click", "value": "342"},
                        {"action_type": "page_engagement", "value": "456"},
                    ],
                )
            ]
        
        # TODO: LIVE mode - Implement insights retrieval
        # Endpoint depends on level:
        # - account: GET /{ad_account_id}/insights
        # - campaign: GET /{campaign_id}/insights
        # - adset: GET /{adset_id}/insights
        # - ad: GET /{ad_id}/insights
        
        # Required params: date_preset OR time_range
        # Optional params: fields, level, filtering, breakdowns
        
        # Example params:
        # {
        #   "date_preset": "last_7d",
        #   "fields": ["impressions", "clicks", "spend", "reach", "cpm", "cpc", "ctr"],
        #   "level": "campaign"  # only for account-level insights
        # }
        
        # Response: {
        #   "data": [
        #     {
        #       "date_start": "2024-01-01",
        #       "date_stop": "2024-01-07",
        #       "impressions": "15234",
        #       "clicks": "342",
        #       ...
        #     }
        #   ],
        #   "paging": {...}
        # }
        
        # Handle pagination if needed (next/previous cursors)
        
        raise NotImplementedError("Insights retrieval not implemented in LIVE mode")
    
    def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        """
        Update campaign status (ACTIVE, PAUSED, DELETED).
        
        Args:
            campaign_id: Campaign ID
            status: New status
            
        Returns:
            True if successful
            
        Raises:
            MetaAPIError: If update fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Updating campaign {campaign_id} status to {status}")
            return True
        
        # TODO: LIVE mode - Implement campaign status update
        # Endpoint: POST /{campaign_id}
        # Params: {"status": "ACTIVE|PAUSED|DELETED"}
        # Response: {"success": true}
        raise NotImplementedError("Campaign status update not implemented in LIVE mode")
    
    def update_adset_status(self, adset_id: str, status: str) -> bool:
        """
        Update adset status (ACTIVE, PAUSED, DELETED).
        
        Args:
            adset_id: AdSet ID
            status: New status
            
        Returns:
            True if successful
            
        Raises:
            MetaAPIError: If update fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Updating adset {adset_id} status to {status}")
            return True
        
        # TODO: LIVE mode - Implement adset status update
        # Endpoint: POST /{adset_id}
        # Params: {"status": "ACTIVE|PAUSED|DELETED"}
        # Response: {"success": true}
        raise NotImplementedError("AdSet status update not implemented in LIVE mode")
    
    def update_ad_status(self, ad_id: str, status: str) -> bool:
        """
        Update ad status (ACTIVE, PAUSED, DELETED).
        
        Args:
            ad_id: Ad ID
            status: New status
            
        Returns:
            True if successful
            
        Raises:
            MetaAPIError: If update fails
        """
        if self.mode == "stub":
            logger.info(f"[STUB] Updating ad {ad_id} status to {status}")
            return True
        
        # TODO: LIVE mode - Implement ad status update
        # Endpoint: POST /{ad_id}
        # Params: {"status": "ACTIVE|PAUSED|DELETED"}
        # Response: {"success": true}
        raise NotImplementedError("Ad status update not implemented in LIVE mode")
