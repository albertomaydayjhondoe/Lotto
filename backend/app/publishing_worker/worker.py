"""
Publishing Worker Implementation.

This module provides the async worker loop that processes pending publish_logs
from the queue, executes the publishing logic, and updates log status.

Key Functions:
- run_publishing_worker: Infinite loop worker for continuous processing
- run_publishing_worker_once: Single iteration for testing/manual processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.publishing_queue import (
    fetch_next_pending_log,
    mark_log_processing,
    mark_log_success,
    mark_log_failed,
    mark_log_retry,
)
from app.publishing_engine import publish_clip
from app.publishing_engine.models import PublishRequest
from app.ledger import log_event

logger = logging.getLogger(__name__)

# Backoff configuration
BACKOFF_BASE_SECONDS = 1.0  # Base delay for exponential backoff


def calculate_backoff_delay(retry_count: int) -> float:
    """
    Calculate exponential backoff delay.
    
    Formula: delay = base * (2 ** retry_count)
    
    Args:
        retry_count: Number of retry attempts made
        
    Returns:
        Delay in seconds
        
    Examples:
        retry_count=0 -> 1.0s
        retry_count=1 -> 2.0s
        retry_count=2 -> 4.0s
        retry_count=3 -> 8.0s
    """
    return BACKOFF_BASE_SECONDS * (2 ** retry_count)


async def run_publishing_worker(
    db: AsyncSession,
    *,
    worker_id: str,
    poll_interval: float = 1.0
) -> None:
    """
    Run the publishing worker loop continuously.
    
    This worker polls the publishing queue for pending logs, processes them
    by calling the publishing engine, and updates their status.
    
    The worker is resilient to errors and will continue running even if
    individual log processing fails.
    
    Args:
        db: Database session
        worker_id: Unique identifier for this worker instance
        poll_interval: Seconds to wait between queue polls (default: 1.0)
        
    Example:
        ```python
        async with get_db_session() as db:
            await run_publishing_worker(
                db,
                worker_id="worker-1",
                poll_interval=2.0
            )
        ```
    
    Note:
        This function runs indefinitely until cancelled (via asyncio.CancelledError).
        Use asyncio.create_task() and cancel() to stop the worker.
    """
    await log_event(
        db,
        event_type="publish_worker_started",
        severity="info",
        entity_type="worker",
        entity_id=worker_id,
        metadata={"poll_interval": poll_interval}
    )
    
    logger.info(f"Publishing worker {worker_id} started (poll_interval={poll_interval}s)")
    
    try:
        while True:
            try:
                # Process one log from the queue
                result = await _process_one_log(db, worker_id)
                
                if not result["processed"]:
                    # Queue is empty, log idle state
                    await log_event(
                        db,
                        event_type="publish_worker_idle",
                        severity="debug",
                        entity_type="worker",
                        entity_id=worker_id
                    )
                    logger.debug(f"Worker {worker_id}: Queue empty, waiting...")
                    # Wait before next poll
                    await asyncio.sleep(poll_interval)
                elif result["status"] == "retry":
                    # Calculate backoff delay for retries
                    # Get retry_count from result metadata if available
                    backoff_delay = poll_interval * 2  # Default to 2x poll_interval
                    logger.info(
                        f"Worker {worker_id}: Log {result['log_id']} scheduled for retry, "
                        f"backoff delay: {backoff_delay}s"
                    )
                    await asyncio.sleep(backoff_delay)
                else:
                    # Normal processing (success or final failure)
                    await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                # Worker is being shut down
                logger.info(f"Worker {worker_id} received cancellation signal")
                raise
                
            except Exception as e:
                # Worker should never crash - log error and continue
                logger.error(f"Worker {worker_id} encountered unexpected error: {e}", exc_info=True)
                await log_event(
                    db,
                    event_type="publish_worker_error",
                    severity="error",
                    entity_type="worker",
                    entity_id=worker_id,
                    metadata={"error_type": type(e).__name__, "error": str(e)}
                )
                # Wait a bit longer after error
                await asyncio.sleep(poll_interval * 2)
                
    except asyncio.CancelledError:
        await log_event(
            db,
            event_type="publish_worker_stopped",
            severity="info",
            entity_type="worker",
            entity_id=worker_id
        )
        logger.info(f"Publishing worker {worker_id} stopped")
        raise


async def run_publishing_worker_once(db: AsyncSession) -> Dict[str, Any]:
    """
    Process a single log from the queue (one iteration only).
    
    This is useful for:
    - Manual triggering via API endpoint
    - Testing worker behavior
    - Processing queue in controlled batches
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with processing result:
        {
            "processed": bool,          # Whether a log was processed
            "log_id": str | None,       # ID of processed log
            "status": str | None,       # Final status (success/failed)
            "error": str | None,        # Error message if failed
            "external_post_id": str | None,  # External post ID if success
            "platform": str | None      # Platform name
        }
        
    Example:
        ```python
        result = await run_publishing_worker_once(db)
        if result["processed"]:
            print(f"Processed log {result['log_id']} -> {result['status']}")
        else:
            print("Queue is empty")
        ```
    """
    worker_id = f"manual-{uuid4().hex[:8]}"
    return await _process_one_log(db, worker_id)


async def _process_one_log(db: AsyncSession, worker_id: str) -> Dict[str, Any]:
    """
    Internal function to process a single log from the queue.
    
    Args:
        db: Database session
        worker_id: Worker identifier for logging
        
    Returns:
        Processing result dictionary
    """
    # Fetch next pending log with locking
    log = await fetch_next_pending_log(db)
    
    if log is None:
        # Queue is empty
        return {
            "processed": False,
            "log_id": None,
            "status": None,
            "error": None,
            "external_post_id": None,
            "platform": None
        }
    
    # Log that we took this log
    await log_event(
        db,
        event_type="publish_worker_log_taken",
        severity="info",
        entity_type="publish_log",
        entity_id=str(log.id),
        metadata={
            "worker_id": worker_id,
            "platform": log.platform,
            "clip_id": str(log.clip_id)
        }
    )
    
    logger.info(f"Worker {worker_id}: Processing log {log.id} (platform={log.platform})")
    
    # Mark as processing
    await mark_log_processing(db, log)
    
    try:
        # Build PublishRequest from the log
        request = PublishRequest(
            clip_id=log.clip_id,
            platform=log.platform,
            social_account_id=log.social_account_id
        )
        
        # Call the publishing engine
        result = await publish_clip(db, request)
        
        # Mark as success
        await mark_log_success(
            db,
            log,
            external_post_id=result.external_post_id,
            external_url=result.external_url,
            extra_metadata={
                "worker_id": worker_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        )
        
        # Log success
        await log_event(
            db,
            event_type="publish_worker_log_success",
            severity="info",
            entity_type="publish_log",
            entity_id=str(log.id),
            metadata={
                "worker_id": worker_id,
                "platform": log.platform,
                "external_post_id": result.external_post_id,
                "external_url": result.external_url
            }
        )
        
        logger.info(
            f"Worker {worker_id}: Successfully published log {log.id} "
            f"(external_post_id={result.external_post_id})"
        )
        
        return {
            "processed": True,
            "log_id": str(log.id),
            "status": "success",
            "error": None,
            "external_post_id": result.external_post_id,
            "platform": log.platform
        }
        
    except Exception as e:
        # Handle failure with retry logic
        error_message = str(e)
        
        # Use retry logic instead of immediate failure
        await mark_log_retry(
            db,
            log,
            error_message=error_message,
            extra_metadata={
                "worker_id": worker_id,
                "error_type": type(e).__name__,
                "processed_at": datetime.utcnow().isoformat(),
                "retry_attempt": log.retry_count + 1
            }
        )
        
        # Refresh to get updated status
        await db.refresh(log)
        
        # Determine event type based on final status
        if log.status == "retry":
            event_type = "publish_worker_log_retry"
            severity = "warn"
        else:
            event_type = "publish_worker_log_failed"
            severity = "error"
        
        # Log the event
        await log_event(
            db,
            event_type=event_type,
            severity=severity,
            entity_type="publish_log",
            entity_id=str(log.id),
            metadata={
                "worker_id": worker_id,
                "platform": log.platform,
                "error_type": type(e).__name__,
                "error_message": error_message,
                "retry_count": log.retry_count,
                "max_retries": log.max_retries
            }
        )
        
        logger_msg = (
            f"Worker {worker_id}: Log {log.id} retry {log.retry_count}/{log.max_retries} "
            f"(status={log.status}): {error_message}"
        )
        if log.status == "retry":
            logger.warning(logger_msg)
        else:
            logger.error(logger_msg, exc_info=True)
        
        return {
            "processed": True,
            "log_id": str(log.id),
            "status": log.status,
            "error": error_message,
            "external_post_id": None,
            "platform": log.platform
        }
