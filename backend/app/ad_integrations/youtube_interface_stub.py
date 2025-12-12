"""
YouTube Ads Platform Interface - STUB

Interface for YouTube Ads API integration.

CURRENT STATUS: STUB - No real API calls
Phase 4: Integrate with real Google Ads API (YouTube)
"""

from typing import Dict, Any, Optional
from datetime import datetime


class YouTubeAdsInterfaceStub:
    """
    YouTube Ads API interface (STUB mode).
    
    Phase 3: Returns mock responses
    Phase 4: Integrates with real Google Ads API
    """
    
    def __init__(self):
        """Initialize YouTube interface in STUB mode."""
        self._stub_mode = True
        self._api_key: Optional[str] = None
    
    async def create_video_campaign(
        self,
        customer_id: str,
        campaign_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a video ad campaign on YouTube.
        
        Phase 3: Returns mock campaign ID
        Phase 4: Creates real campaign via Google Ads API
        
        Args:
            customer_id: Google Ads customer ID
            campaign_config: Campaign configuration
            
        Returns:
            Campaign creation result
        """
        return {
            "campaign_id": f"youtube_campaign_stub_{datetime.utcnow().timestamp()}",
            "status": "ENABLED",
            "platform": "youtube",
            "campaign_type": "VIDEO",
            "budget": campaign_config.get("budget", 500),
            "mode": "stub",
        }
    
    async def upload_video_ad(
        self,
        customer_id: str,
        video_url: str,
        ad_format: str = "SKIPPABLE_IN_STREAM"
    ) -> Dict[str, Any]:
        """
        Upload video ad to YouTube.
        
        Phase 3: Returns mock video ad ID
        Phase 4: Uploads real video ad to YouTube
        
        Args:
            customer_id: Google Ads customer ID
            video_url: URL of video to upload
            ad_format: Ad format (SKIPPABLE_IN_STREAM, NON_SKIPPABLE, BUMPER)
            
        Returns:
            Video ad upload result
        """
        return {
            "video_ad_id": f"youtube_ad_stub_{datetime.utcnow().timestamp()}",
            "video_url": video_url,
            "ad_format": ad_format,
            "status": "APPROVED",
            "mode": "stub",
        }
    
    async def get_campaign_metrics(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get campaign performance metrics.
        
        Phase 3: Returns mock metrics
        Phase 4: Fetches real metrics from Google Ads API
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign metrics
        """
        return {
            "campaign_id": campaign_id,
            "views": 150000,
            "impressions": 200000,
            "clicks": 7500,
            "spend": 450.00,
            "view_rate": 75.0,
            "mode": "stub",
        }
    
    async def get_video_analytics(
        self,
        video_id: str
    ) -> Dict[str, Any]:
        """
        Get video-specific analytics.
        
        Phase 3: Returns mock analytics
        Phase 4: Fetches real analytics from YouTube Data API
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video analytics
        """
        return {
            "video_id": video_id,
            "views": 50000,
            "likes": 3200,
            "comments": 450,
            "shares": 890,
            "watch_time_hours": 2100,
            "mode": "stub",
        }
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Get YouTube interface status."""
        return {
            "platform": "youtube",
            "connected": False,
            "stub_mode": self._stub_mode,
            "features_available": [
                "video_campaign_creation",
                "video_ad_upload",
                "campaign_metrics",
                "video_analytics",
            ],
            "status": "stub_only",
        }


# Global instance
youtube_interface = YouTubeAdsInterfaceStub()


def get_youtube_interface() -> YouTubeAdsInterfaceStub:
    """Get global YouTube interface instance."""
    return youtube_interface
