"""
Instagram Webhook Handler.

Simulates Instagram API callbacks for published posts.
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


async def handle_instagram_webhook(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handle Instagram webhook callback.
    
    Instagram sends callbacks when media is published or encounters errors.
    
    Expected payload format:
    {
        "external_post_id": "instagram_post_12345",
        "media_url": "https://www.instagram.com/p/ABC123/",
        "status": "published",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    Args:
        db: Database session
        payload: Instagram webhook payload
        
    Returns:
        Response dict with status
        
    Example:
        result = await handle_instagram_webhook(db, {
            "external_post_id": "ig_post_123",
            "media_url": "https://instagram.com/p/ABC/",
            "status": "published"
        })
    """
    external_post_id = payload.get("external_post_id")
    
    if not external_post_id:
        logger.warning("Instagram webhook missing external_post_id")
        return {"status": "error", "message": "Missing external_post_id"}
    
    # Find the publish log
    query = select(PublishLogModel).where(
        PublishLogModel.external_post_id == external_post_id,
        PublishLogModel.platform == "instagram"
    )
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        logger.warning(f"Instagram webhook: log not found for external_post_id={external_post_id}")
        return {"status": "error", "message": "Log not found"}
    
    # Update metadata with webhook data
    if log.extra_metadata is None:
        log.extra_metadata = {}
    else:
        log.extra_metadata = dict(log.extra_metadata)
    
    log.extra_metadata.update({
        "webhook_received": True,
        "webhook_timestamp": datetime.utcnow().isoformat(),
        "webhook_platform": "instagram",
        "media_url": payload.get("media_url"),
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
            "platform": "instagram",
            "external_post_id": external_post_id,
            "webhook_status": payload.get("status", "published")
        }
    )
    
    logger.info(f"Instagram webhook processed for log {log.id}")
    
    return {"status": "ok"}
