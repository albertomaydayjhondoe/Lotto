"""
Meta Ads Platform Interface - STUB

Interface for Meta (Facebook/Instagram) Ads API integration.

CURRENT STATUS: STUB - No real API calls
Phase 4: Integrate with real Meta Marketing API
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class MetaAdsInterfaceStub:
    """
    Meta Ads API interface (STUB mode).
    
    Phase 3: Returns mock responses
    Phase 4: Integrates with real Meta Marketing API
    """
    
    def __init__(self):
        """Initialize Meta interface in STUB mode."""
        self._stub_mode = True
        self._access_token: Optional[str] = None
    
    async def create_campaign(
        self,
        account_id: str,
        campaign_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new ad campaign on Meta.
        
        Phase 3: Returns mock campaign ID
        Phase 4: Creates real campaign via Meta API
        
        Args:
            account_id: Meta ad account ID
            campaign_config: Campaign configuration
            
        Returns:
            Campaign creation result
        """
        # STUB: Return mock campaign
        return {
            "campaign_id": f"meta_campaign_stub_{datetime.utcnow().timestamp()}",
            "status": "ACTIVE",
            "platform": "meta",
            "objective": campaign_config.get("objective", "REACH"),
            "budget": campaign_config.get("budget", 100),
            "mode": "stub",
        }
    
    async def create_ad_set(
        self,
        campaign_id: str,
        targeting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an ad set within a campaign.
        
        Phase 3: Returns mock ad set
        Phase 4: Creates real ad set via Meta API
        
        Args:
            campaign_id: Parent campaign ID
            targeting: Targeting parameters
            
        Returns:
            Ad set creation result
        """
        return {
            "ad_set_id": f"meta_adset_stub_{datetime.utcnow().timestamp()}",
            "campaign_id": campaign_id,
            "targeting": targeting,
            "status": "ACTIVE",
            "mode": "stub",
        }
    
    async def create_ad_creative(
        self,
        account_id: str,
        creative_assets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create ad creative with music/video assets.
        
        Phase 3: Returns mock creative
        Phase 4: Uploads real assets to Meta
        
        Args:
            account_id: Meta ad account ID
            creative_assets: Assets (video, audio, images)
            
        Returns:
            Creative creation result
        """
        return {
            "creative_id": f"meta_creative_stub_{datetime.utcnow().timestamp()}",
            "video_url": creative_assets.get("video_url"),
            "audio_url": creative_assets.get("audio_url"),
            "status": "ACTIVE",
            "mode": "stub",
        }
    
    async def get_campaign_insights(
        self,
        campaign_id: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Get campaign performance metrics.
        
        Phase 3: Returns mock metrics
        Phase 4: Fetches real insights from Meta API
        
        Args:
            campaign_id: Campaign ID
            metrics: List of metrics to retrieve
            
        Returns:
            Campaign insights
        """
        return {
            "campaign_id": campaign_id,
            "impressions": 50000,
            "reach": 35000,
            "clicks": 2500,
            "spend": 150.00,
            "ctr": 5.0,
            "mode": "stub",
        }
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Get Meta interface status."""
        return {
            "platform": "meta",
            "connected": False,
            "stub_mode": self._stub_mode,
            "features_available": [
                "campaign_creation",
                "ad_set_management",
                "creative_upload",
                "insights_retrieval",
            ],
            "status": "stub_only",
        }


# Global instance
meta_interface = MetaAdsInterfaceStub()


def get_meta_interface() -> MetaAdsInterfaceStub:
    """Get global Meta interface instance."""
    return meta_interface
