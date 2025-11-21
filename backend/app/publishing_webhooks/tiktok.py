"""
TikTok Webhook Handler.

Simulates TikTok API callbacks for published videos.
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


async def handle_tiktok_webhook(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handle TikTok webhook callback.
    
    TikTok sends callbacks when video upload tasks complete.
    
    Expected payload format:
    {
        "external_post_id": "tiktok_video_67890",
        "task_id": "task_abc123",
        "complete": true,
        "video_url": "https://www.tiktok.com/@user/video/123",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    Args:
        db: Database session
        payload: TikTok webhook payload
        
    Returns:
        Response dict with status
        
    Example:
        result = await handle_tiktok_webhook(db, {
            "external_post_id": "tiktok_123",
            "task_id": "task_abc",
            "complete": true
        })
    """
    external_post_id = payload.get("external_post_id")
    
    if not external_post_id:
        logger.warning("TikTok webhook missing external_post_id")
        return {"status": "error", "message": "Missing external_post_id"}
    
    # Find the publish log
    query = select(PublishLogModel).where(
        PublishLogModel.external_post_id == external_post_id,
        PublishLogModel.platform == "tiktok"
    )
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        logger.warning(f"TikTok webhook: log not found for external_post_id={external_post_id}")
        return {"status": "error", "message": "Log not found"}
    
    # Update metadata with webhook data
    if log.extra_metadata is None:
        log.extra_metadata = {}
    else:
        log.extra_metadata = dict(log.extra_metadata)
    
    log.extra_metadata.update({
        "webhook_received": True,
        "webhook_timestamp": datetime.utcnow().isoformat(),
        "webhook_platform": "tiktok",
        "task_id": payload.get("task_id"),
        "complete": payload.get("complete", False),
        "video_url": payload.get("video_url")
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
            "platform": "tiktok",
            "external_post_id": external_post_id,
            "task_id": payload.get("task_id"),
            "complete": payload.get("complete", False)
        }
    )
    
    logger.info(f"TikTok webhook processed for log {log.id}")
    
    return {"status": "ok"}
