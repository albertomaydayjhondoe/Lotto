"""
Publishing Integrations module.

This module provides real API client structures for social media platforms
(Instagram, TikTok, YouTube) without requiring actual credentials.

Current status: STUB implementations ready for API key integration.
"""
from app.publishing_integrations.base_client import BasePublishingClient
from app.publishing_integrations.instagram_client import InstagramPublishingClient
from app.publishing_integrations.tiktok_client import TikTokPublishingClient
from app.publishing_integrations.youtube_client import YouTubePublishingClient
from app.publishing_integrations.exceptions import (
    PublishingAuthError,
    PublishingUploadError,
    PublishingPostError
)
from app.publishing_integrations.router import router


# Provider registry
AVAILABLE_PROVIDERS = {
    "instagram": InstagramPublishingClient,
    "tiktok": TikTokPublishingClient,
    "youtube": YouTubePublishingClient
}


def get_provider_client(platform: str, config: dict = None) -> BasePublishingClient:
    """
    Factory function to get a provider client instance.
    
    Args:
        platform: Platform name (instagram, tiktok, youtube)
        config: Optional configuration dict with API credentials
        
    Returns:
        Platform-specific client instance
        
    Raises:
        ValueError: If platform not supported
        
    Example:
        >>> client = get_provider_client("instagram", {"access_token": "..."})
        >>> await client.authenticate()
        >>> result = await client.upload_video("/path/to/video.mp4")
    """
    if platform not in AVAILABLE_PROVIDERS:
        raise ValueError(
            f"Platform '{platform}' not supported. "
            f"Available: {', '.join(AVAILABLE_PROVIDERS.keys())}"
        )
    
    client_class = AVAILABLE_PROVIDERS[platform]
    return client_class(config=config)


__all__ = [
    # Base
    "BasePublishingClient",
    
    # Clients
    "InstagramPublishingClient",
    "TikTokPublishingClient",
    "YouTubePublishingClient",
    
    # Exceptions
    "PublishingAuthError",
    "PublishingUploadError",
    "PublishingPostError",
    
    # Factory
    "get_provider_client",
    "AVAILABLE_PROVIDERS",
    
    # Router
    "router",
]
