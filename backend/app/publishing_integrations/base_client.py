"""
Base Publishing Client interface.

All platform-specific clients must inherit from this base class
and implement the required methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePublishingClient(ABC):
    """
    Abstract base class for all social platform publishing clients.
    
    Each platform (Instagram, TikTok, YouTube) implements this interface
    with platform-specific logic and API calls.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the client with optional configuration.
        
        Args:
            config: Platform-specific configuration (API keys, tokens, etc.)
        """
        self.config = config or {}
        self._authenticated = False
    
    @property
    def platform_name(self) -> str:
        """Return the platform name (e.g., 'instagram', 'tiktok', 'youtube')."""
        raise NotImplementedError("Subclasses must define platform_name")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is currently authenticated."""
        return self._authenticated
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the platform API.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            PublishingAuthError: If authentication fails
        """
        raise NotImplementedError("Subclasses must implement authenticate()")
    
    @abstractmethod
    async def upload_video(
        self, 
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Upload a video file to the platform.
        
        Args:
            file_path: Path to the video file
            **kwargs: Platform-specific upload parameters
            
        Returns:
            Dict with upload result including video_id
            
        Raises:
            PublishingUploadError: If upload fails
        """
        raise NotImplementedError("Subclasses must implement upload_video()")
    
    @abstractmethod
    async def publish_post(
        self,
        video_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish a post with the uploaded video.
        
        Args:
            video_id: Platform-specific video ID from upload
            **kwargs: Platform-specific post parameters (caption, etc.)
            
        Returns:
            Dict with post result including post_id and post_url
            
        Raises:
            PublishingPostError: If publishing fails
        """
        raise NotImplementedError("Subclasses must implement publish_post()")
    
    @abstractmethod
    def validate_post_params(self, **kwargs) -> Dict[str, Any]:
        """
        Validate post parameters before publishing.
        
        Args:
            **kwargs: Platform-specific post parameters
            
        Returns:
            Dict with validation result: {valid: bool, errors: List[str]}
        """
        raise NotImplementedError("Subclasses must implement validate_post_params()")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return platform capabilities and limitations.
        
        Returns:
            Dict with platform capabilities (max_duration, max_caption_length, etc.)
        """
        return {
            "platform": self.platform_name,
            "authenticated": self.is_authenticated,
            "features": []
        }
