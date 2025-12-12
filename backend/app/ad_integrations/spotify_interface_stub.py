"""
Spotify Ads Platform Interface - STUB

Interface for Spotify Ad Studio API integration.

CURRENT STATUS: STUB - No real API calls
Phase 4: Integrate with real Spotify Ad Studio API
"""

from typing import Dict, Any, Optional
from datetime import datetime


class SpotifyAdsInterfaceStub:
    """
    Spotify Ads API interface (STUB mode).
    
    Phase 3: Returns mock responses
    Phase 4: Integrates with real Spotify Ad Studio API
    """
    
    def __init__(self):
        """Initialize Spotify interface in STUB mode."""
        self._stub_mode = True
        self._access_token: Optional[str] = None
    
    async def create_audio_ad(
        self,
        account_id: str,
        ad_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an audio ad on Spotify.
        
        Phase 3: Returns mock ad ID
        Phase 4: Creates real ad via Spotify API
        
        Args:
            account_id: Spotify ad account ID
            ad_config: Ad configuration (audio URL, targeting)
            
        Returns:
            Ad creation result
        """
        return {
            "ad_id": f"spotify_ad_stub_{datetime.utcnow().timestamp()}",
            "status": "ACTIVE",
            "platform": "spotify",
            "audio_url": ad_config.get("audio_url"),
            "target_audience": ad_config.get("targeting", {}),
            "mode": "stub",
        }
    
    async def upload_audio(
        self,
        account_id: str,
        audio_url: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload audio creative to Spotify.
        
        Phase 3: Returns mock upload result
        Phase 4: Uploads real audio to Spotify CDN
        
        Args:
            account_id: Spotify ad account ID
            audio_url: URL of audio to upload
            metadata: Audio metadata (title, artist, duration)
            
        Returns:
            Audio upload result
        """
        return {
            "audio_id": f"spotify_audio_stub_{datetime.utcnow().timestamp()}",
            "audio_url": audio_url,
            "duration_seconds": metadata.get("duration", 30),
            "status": "APPROVED",
            "mode": "stub",
        }
    
    async def get_ad_performance(
        self,
        ad_id: str
    ) -> Dict[str, Any]:
        """
        Get ad performance metrics.
        
        Phase 3: Returns mock metrics
        Phase 4: Fetches real metrics from Spotify API
        
        Args:
            ad_id: Ad ID
            
        Returns:
            Ad performance metrics
        """
        return {
            "ad_id": ad_id,
            "impressions": 100000,
            "listens": 8500,
            "completion_rate": 85.0,
            "spend": 250.00,
            "mode": "stub",
        }
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Get Spotify interface status."""
        return {
            "platform": "spotify",
            "connected": False,
            "stub_mode": self._stub_mode,
            "features_available": [
                "audio_ad_creation",
                "audio_upload",
                "performance_metrics",
            ],
            "status": "stub_only",
        }


# Global instance
spotify_interface = SpotifyAdsInterfaceStub()


def get_spotify_interface() -> SpotifyAdsInterfaceStub:
    """Get global Spotify interface instance."""
    return spotify_interface
