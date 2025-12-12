"""Publishing simulators for testing without real API integration."""

import asyncio
import random
from uuid import uuid4

from app.publishing_engine.models import PublishRequest, PublishResult


async def simulate_instagram_publish(request: PublishRequest) -> PublishResult:
    """
    Simulate Instagram publication.
    
    - 10% failure rate
    - Generates fake post ID and URL
    - Simulates network delay
    
    Args:
        request: PublishRequest with clip and account details
    
    Returns:
        PublishResult with success status and post details
    """
    # Simulate network delay
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # 10% chance of failure
    if random.random() < 0.1:
        return PublishResult(
            success=False,
            external_post_id=None,
            external_url=None,
            error_message="Instagram API rate limit exceeded (simulated)",
            platform=request.platform,
            clip_id=request.clip_id,
            social_account_id=request.social_account_id
        )
    
    # Success case
    post_id = f"ig_{uuid4().hex[:12]}"
    return PublishResult(
        success=True,
        external_post_id=post_id,
        external_url=f"https://www.instagram.com/p/{post_id}/",
        error_message=None,
        platform=request.platform,
        clip_id=request.clip_id,
        social_account_id=request.social_account_id
    )


async def simulate_tiktok_publish(request: PublishRequest) -> PublishResult:
    """
    Simulate TikTok publication.
    
    - 10% failure rate
    - Generates fake video ID and URL
    - Simulates network delay
    
    Args:
        request: PublishRequest with clip and account details
    
    Returns:
        PublishResult with success status and video details
    """
    # Simulate network delay
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # 10% chance of failure
    if random.random() < 0.1:
        return PublishResult(
            success=False,
            external_post_id=None,
            external_url=None,
            error_message="TikTok content moderation check failed (simulated)",
            platform=request.platform,
            clip_id=request.clip_id,
            social_account_id=request.social_account_id
        )
    
    # Success case
    video_id = f"tt_{uuid4().hex[:16]}"
    return PublishResult(
        success=True,
        external_post_id=video_id,
        external_url=f"https://www.tiktok.com/@user/video/{video_id}",
        error_message=None,
        platform=request.platform,
        clip_id=request.clip_id,
        social_account_id=request.social_account_id
    )


async def simulate_youtube_publish(request: PublishRequest) -> PublishResult:
    """
    Simulate YouTube publication (as Short).
    
    - 10% failure rate
    - Generates fake video ID and URL
    - Simulates network delay
    
    Args:
        request: PublishRequest with clip and account details
    
    Returns:
        PublishResult with success status and video details
    """
    # Simulate network delay
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # 10% chance of failure
    if random.random() < 0.1:
        return PublishResult(
            success=False,
            external_post_id=None,
            external_url=None,
            error_message="YouTube quota exceeded (simulated)",
            platform=request.platform,
            clip_id=request.clip_id,
            social_account_id=request.social_account_id
        )
    
    # Success case
    video_id = f"yt_{uuid4().hex[:11]}"
    return PublishResult(
        success=True,
        external_post_id=video_id,
        external_url=f"https://www.youtube.com/shorts/{video_id}",
        error_message=None,
        platform=request.platform,
        clip_id=request.clip_id,
        social_account_id=request.social_account_id
    )


# Platform simulators registry
PLATFORM_SIMULATORS = {
    "instagram": simulate_instagram_publish,
    "tiktok": simulate_tiktok_publish,
    "youtube": simulate_youtube_publish,
}


async def get_simulator(platform: str):
    """
    Get the appropriate simulator for a platform.
    
    Args:
        platform: Platform name (instagram, tiktok, youtube)
    
    Returns:
        Simulator function
    
    Raises:
        ValueError: If platform is not supported
    """
    simulator = PLATFORM_SIMULATORS.get(platform.lower())
    if not simulator:
        raise ValueError(f"Unsupported platform: {platform}")
    return simulator
