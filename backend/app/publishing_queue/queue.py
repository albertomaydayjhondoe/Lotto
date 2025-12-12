"""
Publishing Queue Implementation.

This module provides safe queue operations for processing publish_logs
with proper concurrency handling for both PostgreSQL and SQLite databases.

Key Functions:
- fetch_next_pending_log: Get the next pending log with locking
- mark_log_processing: Mark a log as being processed
- mark_log_success: Mark a log as successfully published
- mark_log_failed: Mark a log as failed with error details

Transaction Policy:
All functions commit their changes automatically. This ensures that status
updates are immediately visible to other processes/workers.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import PublishLogModel
from app.core.database import engine


async def fetch_next_pending_log(db: AsyncSession) -> Optional[PublishLogModel]:
    """
    Fetch the next pending publish log from the queue.
    
    This function selects the oldest pending log (by requested_at) and
    locks it to prevent concurrent processing.
    
    Concurrency Strategy:
    - PostgreSQL: Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent access.
      Multiple workers can safely poll the queue, and each will get a different log.
    
    - SQLite: SKIP LOCKED is not supported. The query uses FOR UPDATE (which SQLite
      largely ignores), but relies on serialized transactions for safety.
      In production with SQLite, ensure only one worker processes the queue,
      or accept that race conditions may occur (tests use isolated transactions).
    
    Args:
        db: Active database session
        
    Returns:
        The next pending PublishLogModel, or None if no pending logs exist
        
    Example:
        log = await fetch_next_pending_log(db)
        if log:
            await mark_log_processing(db, log)
            # ... process the log ...
    """
    # Detect database type
    is_postgres = engine.dialect.name == "postgresql"
    
    # Build query: get oldest pending or retry log
    query = (
        select(PublishLogModel)
        .where(PublishLogModel.status.in_(["pending", "retry"]))
        .order_by(PublishLogModel.requested_at.asc())
        .limit(1)
    )
    
    # Add locking for safe concurrent access
    if is_postgres:
        # PostgreSQL: Use SKIP LOCKED to safely handle concurrent workers
        query = query.with_for_update(skip_locked=True)
    else:
        # SQLite: Use FOR UPDATE (mostly ignored, but doesn't hurt)
        # Note: SQLite doesn't support SKIP LOCKED, so concurrent access
        # should be avoided or handled at the application level
        query = query.with_for_update()
    
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    return log


async def mark_log_processing(db: AsyncSession, log: PublishLogModel) -> None:
    """
    Mark a publish log as being processed.
    
    Updates the log status to "processing" and commits the change.
    This prevents other workers from picking up the same log.
    
    Args:
        db: Active database session
        log: The PublishLogModel to mark as processing
        
    Example:
        log = await fetch_next_pending_log(db)
        if log:
            await mark_log_processing(db, log)
    """
    log.status = "processing"
    log.updated_at = datetime.utcnow()
    
    db.add(log)
    await db.commit()
    await db.refresh(log)


async def mark_log_success(
    db: AsyncSession,
    log: PublishLogModel,
    external_post_id: Optional[str] = None,
    external_url: Optional[str] = None,
    extra_metadata: Optional[dict] = None
) -> None:
    """
    Mark a publish log as successfully published.
    
    Updates the log with success status, publication timestamp, and
    external platform details (post ID, URL, metadata).
    
    Args:
        db: Active database session
        log: The PublishLogModel to mark as successful
        external_post_id: The ID assigned by the external platform (e.g., Instagram media ID)
        external_url: The public URL of the published post
        extra_metadata: Additional metadata to merge with existing metadata
        
    Example:
        await mark_log_success(
            db,
            log,
            external_post_id="17841405793187218",
            external_url="https://instagram.com/p/ABC123",
            extra_metadata={"likes_count": 0, "comments_count": 0}
        )
    """
    log.status = "success"
    log.published_at = datetime.utcnow()
    log.updated_at = datetime.utcnow()
    
    if external_post_id is not None:
        log.external_post_id = external_post_id
    
    if external_url is not None:
        log.external_url = external_url
    
    if extra_metadata is not None:
        # Merge with existing metadata
        if log.extra_metadata is None:
            log.extra_metadata = {}
        else:
            # Make a copy to ensure SQLAlchemy detects the change
            log.extra_metadata = dict(log.extra_metadata)
        log.extra_metadata.update(extra_metadata)
        # Mark the attribute as modified to ensure SQLAlchemy saves it
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(log, "extra_metadata")
    
    db.add(log)
    await db.commit()
    await db.refresh(log)


async def mark_log_failed(
    db: AsyncSession,
    log: PublishLogModel,
    error_message: str,
    extra_metadata: Optional[dict] = None
) -> None:
    """
    Mark a publish log as failed.
    
    Updates the log with failed status and stores the error message
    for debugging and retry logic.
    
    Args:
        db: Active database session
        log: The PublishLogModel to mark as failed
        error_message: Description of the failure (exception message, API error, etc.)
        extra_metadata: Additional metadata about the failure (error codes, stack traces, etc.)
        
    Example:
        try:
            await publish_to_platform(log)
        except Exception as e:
            await mark_log_failed(
                db,
                log,
                error_message=str(e),
                extra_metadata={"error_type": type(e).__name__}
            )
    """
    log.status = "failed"
    log.error_message = error_message
    log.updated_at = datetime.utcnow()
    
    if extra_metadata is not None:
        # Merge with existing metadata
        if log.extra_metadata is None:
            log.extra_metadata = {}
        else:
            # Make a copy to ensure SQLAlchemy detects the change
            log.extra_metadata = dict(log.extra_metadata)
        log.extra_metadata.update(extra_metadata)
        # Mark the attribute as modified to ensure SQLAlchemy saves it
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(log, "extra_metadata")
    
    db.add(log)
    await db.commit()
    await db.refresh(log)


async def mark_log_retry(
    db: AsyncSession,
    log: PublishLogModel,
    error_message: str,
    extra_metadata: Optional[dict] = None
) -> None:
    """
    Mark a publish log for retry.
    
    Increments the retry count and sets status to "retry" if retries remain,
    or "failed" if max retries reached.
    
    Args:
        db: Active database session
        log: The PublishLogModel to mark for retry
        error_message: Description of the failure that triggered the retry
        extra_metadata: Additional metadata about the retry attempt
        
    Example:
        try:
            await publish_to_platform(log)
        except Exception as e:
            await mark_log_retry(
                db,
                log,
                error_message=str(e),
                extra_metadata={"error_type": type(e).__name__}
            )
    """
    log.retry_count += 1
    log.last_retry_at = datetime.utcnow()
    log.error_message = error_message
    log.updated_at = datetime.utcnow()
    
    # Determine if we should retry or mark as failed
    if log.retry_count < log.max_retries:
        log.status = "retry"
    else:
        log.status = "failed"
    
    if extra_metadata is not None:
        # Merge with existing metadata
        if log.extra_metadata is None:
            log.extra_metadata = {}
        else:
            # Make a copy to ensure SQLAlchemy detects the change
            log.extra_metadata = dict(log.extra_metadata)
        log.extra_metadata.update(extra_metadata)
        # Mark the attribute as modified to ensure SQLAlchemy saves it
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(log, "extra_metadata")
    
    db.add(log)
    await db.commit()
    await db.refresh(log)
