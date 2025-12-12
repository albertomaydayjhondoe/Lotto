"""
YouTube Webhook Handler.

Simulates YouTube API callbacks for published videos.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.database import PublishLogModel
from app.ledger import log_event

logger = logging.getLogger(__name__)


async def handle_youtube_webhook(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handle YouTube webhook callback.
    
    YouTube sends callbacks when videos are published or processing completes.
    
    Expected payload format:
    {
        "external_post_id": "youtube_video_XYZ789",
        "videoId": "dQw4w9WgXcQ",
        "publishAt": "2024-01-15T10:30:00Z",
        "status": "published",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    Args:
        db: Database session
        payload: YouTube webhook payload
        
    Returns:
        Response dict with status
        
    Example:
        result = await handle_youtube_webhook(db, {
            "external_post_id": "yt_123",
            "videoId": "abc123",
            "publishAt": "2024-01-15T10:30:00Z"
        })
    """
    external_post_id = payload.get("external_post_id")
    
    if not external_post_id:
        logger.warning("YouTube webhook missing external_post_id")
        return {"status": "error", "message": "Missing external_post_id"}
    
    # Find the publish log
    query = select(PublishLogModel).where(
        PublishLogModel.external_post_id == external_post_id,
        PublishLogModel.platform == "youtube"
    )
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        logger.warning(f"YouTube webhook: log not found for external_post_id={external_post_id}")
        return {"status": "error", "message": "Log not found"}
    
    # Update metadata with webhook data
    if log.extra_metadata is None:
        log.extra_metadata = {}
    else:
        log.extra_metadata = dict(log.extra_metadata)
    
    log.extra_metadata.update({
        "webhook_received": True,
        "webhook_timestamp": datetime.utcnow().isoformat(),
        "webhook_platform": "youtube",
        "videoId": payload.get("videoId"),
        "publishAt": payload.get("publishAt"),
        "webhook_status": payload.get("status", "published")
    })
    flag_modified(log, "extra_metadata")
    log.updated_at = datetime.utcnow()
    
    db.add(log)
    await db.commit()
    
    # Log event to ledger
    await log_event(
        db,
        event_type="publish_webhook_received",
        severity="info",
        entity_type="publish_log",
        entity_id=str(log.id),
        metadata={
            "platform": "youtube",
            "external_post_id": external_post_id,
            "videoId": payload.get("videoId"),
            "webhook_status": payload.get("status", "published")
        }
    )
    
    logger.info(f"YouTube webhook processed for log {log.id}")
    
    return {"status": "ok"}
