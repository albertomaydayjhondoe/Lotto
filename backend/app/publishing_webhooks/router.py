"""
Publishing Webhooks Router.

FastAPI endpoints for receiving webhook callbacks from social media platforms.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.database import get_db
from app.publishing_webhooks import (
    handle_instagram_webhook,
    handle_tiktok_webhook,
    handle_youtube_webhook
)

router = APIRouter()


@router.post("/webhooks/instagram")
async def instagram_webhook_endpoint(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Instagram webhook endpoint.
    
    Receives callbacks from Instagram API when posts are published.
    
    Example payload:
    ```json
    {
        "external_post_id": "instagram_post_12345",
        "media_url": "https://www.instagram.com/p/ABC123/",
        "status": "published"
    }
    ```
    """
    return await handle_instagram_webhook(db, payload)


@router.post("/webhooks/tiktok")
async def tiktok_webhook_endpoint(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    TikTok webhook endpoint.
    
    Receives callbacks from TikTok API when video tasks complete.
    
    Example payload:
    ```json
    {
        "external_post_id": "tiktok_video_67890",
        "task_id": "task_abc123",
        "complete": true,
        "video_url": "https://www.tiktok.com/@user/video/123"
    }
    ```
    """
    return await handle_tiktok_webhook(db, payload)


@router.post("/webhooks/youtube")
async def youtube_webhook_endpoint(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    YouTube webhook endpoint.
    
    Receives callbacks from YouTube API when videos are published.
    
    Example payload:
    ```json
    {
        "external_post_id": "youtube_video_XYZ789",
        "videoId": "dQw4w9WgXcQ",
        "publishAt": "2024-01-15T10:30:00Z",
        "status": "published"
    }
    ```
    """
    return await handle_youtube_webhook(db, payload)
