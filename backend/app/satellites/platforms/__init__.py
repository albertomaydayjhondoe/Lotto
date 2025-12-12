"""
Platform Clients Package
Export all platform clients.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

from app.satellites.platforms.base_client import BasePlatformClient
from app.satellites.platforms.tiktok_client import TikTokClient
from app.satellites.platforms.instagram_client import InstagramClient
from app.satellites.platforms.youtube_client import YouTubeClient

__all__ = [
    "BasePlatformClient",
    "TikTokClient",
    "InstagramClient",
    "YouTubeClient",
]
