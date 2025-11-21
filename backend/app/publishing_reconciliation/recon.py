"""
Publishing Reconciliation Logic.

Automatically reconciles publish_logs in "processing" or "retry" status
based on webhook data and timeout rules.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import PublishLogModel
from app.publishing_queue import mark_log_success, mark_log_failed
from app.ledger import log_event

logger = logging.getLogger(__name__)


async def reconcile_publications(
    db: AsyncSession,
    *,
    since_minutes: int = 10
) -> Dict[str, Any]:
    """
    Reconcile publication status for logs in processing or retry state.
    
    This function checks publish_logs that have been in "processing" or "retry"
    status for more than the specified time period, and reconciles their state
    based on:
    
    1. Webhook Data: If extra_metadata contains webhook_received=True, mark as success
    2. Timeout: If no webhook after X minutes, mark as failed
    3. Success Logs: Skip logs already in "success" or "failed" state
    
    Args:
        db: Database session
        since_minutes: How many minutes back to look for stale logs (default: 10)
        
    Returns:
        Dict with reconciliation statistics:
        {
            "total_checked": int,
            "marked_success": int,
            "marked_failed": int,
            "skipped": int,
            "success_log_ids": [UUID, ...],
            "failed_log_ids": [UUID, ...]
        }
        
    Example:
        result = await reconcile_publications(db, since_minutes=15)
        # Returns: {"total_checked": 10, "marked_success": 3, "marked_failed": 5, ...}
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=since_minutes)
    
    # Find logs in processing or retry status that are older than cutoff
    query = (
        select(PublishLogModel)
        .where(
            PublishLogModel.status.in_(["processing", "retry"]),
            PublishLogModel.updated_at < cutoff_time
        )
        .order_by(PublishLogModel.updated_at.asc())
    )
    
    result = await db.execute(query)
    stale_logs = result.scalars().all()
    
    stats = {
        "total_checked": len(stale_logs),
        "marked_success": 0,
        "marked_failed": 0,
        "skipped": 0,
        "success_log_ids": [],
        "failed_log_ids": []
    }
    
    for log in stale_logs:
        # Check if webhook was received
        webhook_received = False
        webhook_status = None
        
        if log.extra_metadata:
            webhook_received = log.extra_metadata.get("webhook_received", False)
            webhook_status = log.extra_metadata.get("webhook_status")
        
        if webhook_received and webhook_status == "published":
            # Webhook confirms success -> mark as success
            await mark_log_success(
                db,
                log,
                external_post_id=log.external_post_id or f"reconciled_{log.id}",
                external_url=log.external_url or log.extra_metadata.get("media_url", ""),
                extra_metadata={
                    "reconciled": True,
                    "reconciled_at": datetime.utcnow().isoformat(),
                    "reconciliation_reason": "webhook_confirmed"
                }
            )
            
            # Log reconciliation event
            await log_event(
                db,
                event_type="publish_reconciled",
                severity="info",
                entity_type="publish_log",
                entity_id=str(log.id),
                metadata={
                    "platform": log.platform,
                    "action": "marked_success",
                    "reason": "webhook_confirmed",
                    "external_post_id": log.external_post_id
                }
            )
            
            stats["marked_success"] += 1
            stats["success_log_ids"].append(str(log.id))
            logger.info(f"Reconciliation: Marked log {log.id} as success (webhook confirmed)")
            
        elif not webhook_received:
            # No webhook after timeout -> mark as failed
            error_msg = f"No webhook received after {since_minutes} minutes"
            
            await mark_log_failed(
                db,
                log,
                error_message=error_msg,
                extra_metadata={
                    "reconciled": True,
                    "reconciled_at": datetime.utcnow().isoformat(),
                    "reconciliation_reason": "webhook_timeout"
                }
            )
            
            # Log reconciliation event
            await log_event(
                db,
                event_type="publish_reconciled",
                severity="warn",
                entity_type="publish_log",
                entity_id=str(log.id),
                metadata={
                    "platform": log.platform,
                    "action": "marked_failed",
                    "reason": "webhook_timeout",
                    "timeout_minutes": since_minutes
                }
            )
            
            stats["marked_failed"] += 1
            stats["failed_log_ids"].append(str(log.id))
            logger.warning(f"Reconciliation: Marked log {log.id} as failed (no webhook after {since_minutes}min)")
            
        else:
            # Webhook received but status unclear -> skip for now
            stats["skipped"] += 1
            logger.info(f"Reconciliation: Skipped log {log.id} (webhook_received={webhook_received}, status={webhook_status})")
    
    logger.info(
        f"Reconciliation complete: checked={stats['total_checked']}, "
        f"success={stats['marked_success']}, failed={stats['marked_failed']}, skipped={stats['skipped']}"
    )
    
    return stats
