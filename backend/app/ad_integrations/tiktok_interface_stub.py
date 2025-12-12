"""
TikTok Ads Platform Interface - STUB

Interface for TikTok Ads API integration.

CURRENT STATUS: STUB - No real API calls
Phase 4: Integrate with real TikTok Marketing API
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class TikTokAdsInterfaceStub:
    """
    TikTok Ads API interface (STUB mode).
    
    Phase 3: Returns mock responses
    Phase 4: Integrates with real TikTok Marketing API
    """
    
    def __init__(self):
        """Initialize TikTok interface in STUB mode."""
        self._stub_mode = True
        self._access_token: Optional[str] = None
    
    async def create_campaign(
        self,
        advertiser_id: str,
        campaign_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new ad campaign on TikTok.
        
        Phase 3: Returns mock campaign ID
        Phase 4: Creates real campaign via TikTok API
        
        Args:
            advertiser_id: TikTok advertiser ID
            campaign_config: Campaign configuration
            
        Returns:
            Campaign creation result
        """
        return {
            "campaign_id": f"tiktok_campaign_stub_{datetime.utcnow().timestamp()}",
            "status": "ENABLE",
            "platform": "tiktok",
            "objective": campaign_config.get("objective", "REACH"),
            "budget": campaign_config.get("budget", 100),
            "mode": "stub",
        }
    
    async def create_ad_group(
        self,
        campaign_id: str,
        targeting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an ad group within a campaign.
        
        Phase 3: Returns mock ad group
        Phase 4: Creates real ad group via TikTok API
        
        Args:
            campaign_id: Parent campaign ID
            targeting: Targeting parameters (age, gender, interests)
            
        Returns:
            Ad group creation result
        """
        return {
            "ad_group_id": f"tiktok_adgroup_stub_{datetime.utcnow().timestamp()}",
            "campaign_id": campaign_id,
            "targeting": targeting,
            "status": "ENABLE",
            "mode": "stub",
        }
    
    async def upload_video(
        self,
        advertiser_id: str,
        video_url: str
    ) -> Dict[str, Any]:
        """
        Upload video creative to TikTok.
        
        Phase 3: Returns mock video ID
        Phase 4: Uploads real video to TikTok CDN
        
        Args:
            advertiser_id: TikTok advertiser ID
            video_url: URL of video to upload
            
        Returns:
            Video upload result
        """
        return {
            "video_id": f"tiktok_video_stub_{datetime.utcnow().timestamp()}",
            "advertiser_id": advertiser_id,
            "video_url": video_url,
            "status": "APPROVED",
            "mode": "stub",
        }
    
    async def get_campaign_stats(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get campaign performance statistics.
        
        Phase 3: Returns mock stats
        Phase 4: Fetches real stats from TikTok API
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign statistics
        """
        return {
            "campaign_id": campaign_id,
            "impressions": 75000,
            "clicks": 4500,
            "conversions": 180,
            "spend": 200.00,
            "ctr": 6.0,
            "mode": "stub",
        }
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Get TikTok interface status."""
        return {
            "platform": "tiktok",
            "connected": False,
            "stub_mode": self._stub_mode,
            "features_available": [
                "campaign_creation",
                "ad_group_management",
                "video_upload",
                "stats_retrieval",
            ],
            "status": "stub_only",
        }


# Global instance
tiktok_interface = TikTokAdsInterfaceStub()


def get_tiktok_interface() -> TikTokAdsInterfaceStub:
    """Get global TikTok interface instance."""
    return tiktok_interface
