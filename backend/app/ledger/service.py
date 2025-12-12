"""
Ledger service layer for event logging.

Provides fail-safe functions to log events without breaking application flow.
All functions catch exceptions and only log errors, never raising them.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger.models import LedgerEvent, EventSeverity
from app.core.logging import get_logger

logger = get_logger(__name__)


async def log_event(
    db: AsyncSession,
    event_type: str,
    entity_type: str,
    entity_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
    worker_id: Optional[str] = None,
    job_id: Optional[UUID] = None,
    clip_id: Optional[UUID] = None
) -> Optional[LedgerEvent]:
    """
    Log a generic event to the ledger.
    
    This function is fail-safe: if logging fails, it will only log the error
    and return None, never raising an exception to the caller.
    
    Args:
        db: Database session
        event_type: Type of event (e.g., "video_uploaded", "job_created")
        entity_type: Type of entity (e.g., "video_asset", "job", "clip")
        entity_id: ID of the entity (as string)
        metadata: Additional data about the event (optional)
        severity: Event severity - INFO, WARN, or ERROR (default: INFO)
        worker_id: ID of the worker that processed the event (optional)
        job_id: UUID of related job (optional)
        clip_id: UUID of related clip (optional)
        
    Returns:
        LedgerEvent instance if successful, None if failed
        
    Example:
        >>> await log_event(
        ...     db=db,
        ...     event_type="video_uploaded",
        ...     entity_type="video_asset",
        ...     entity_id=str(video_asset.id),
        ...     metadata={"filename": "video.mp4", "size": 1024000}
        ... )
    """
    try:
        # Validate severity
        severity_value = EventSeverity[severity.upper()]
        
        # Create ledger event
        event = LedgerEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=metadata or {},  # Store in event_data field
            severity=severity_value,
            worker_id=worker_id,
            job_id=job_id,
            clip_id=clip_id
        )
        
        db.add(event)
        # Note: We don't commit here - let the caller manage transaction
        
        logger.info(
            f"Ledger event logged: {event_type}",
            extra={
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "severity": severity,
                "job_id": str(job_id) if job_id else None,
                "clip_id": str(clip_id) if clip_id else None
            }
        )
        
        return event
        
    except Exception as e:
        # Never break the flow - just log the error
        logger.error(
            f"Failed to log ledger event: {event_type}",
            extra={
                "error": str(e),
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )
        return None


async def log_job_event(
    db: AsyncSession,
    job_id: UUID,
    event_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
    worker_id: Optional[str] = None
) -> Optional[LedgerEvent]:
    """
    Log an event related to a job.
    
    Convenience wrapper around log_event() specifically for job-related events.
    
    Args:
        db: Database session
        job_id: UUID of the job
        event_type: Type of event (e.g., "job_created", "job_processing_started")
        metadata: Additional data about the event (optional)
        severity: Event severity - INFO, WARN, or ERROR (default: INFO)
        worker_id: ID of the worker processing the job (optional)
        
    Returns:
        LedgerEvent instance if successful, None if failed
        
    Example:
        >>> await log_job_event(
        ...     db=db,
        ...     job_id=job.id,
        ...     event_type="job_processing_started",
        ...     metadata={"job_type": "cut_analysis"}
        ... )
    """
    return await log_event(
        db=db,
        event_type=event_type,
        entity_type="job",
        entity_id=str(job_id),
        metadata=metadata,
        severity=severity,
        worker_id=worker_id,
        job_id=job_id
    )


async def log_clip_event(
    db: AsyncSession,
    clip_id: UUID,
    event_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
    job_id: Optional[UUID] = None
) -> Optional[LedgerEvent]:
    """
    Log an event related to a clip.
    
    Convenience wrapper around log_event() specifically for clip-related events.
    
    Args:
        db: Database session
        clip_id: UUID of the clip
        event_type: Type of event (e.g., "clip_created", "clip_published")
        metadata: Additional data about the event (optional)
        severity: Event severity - INFO, WARN, or ERROR (default: INFO)
        job_id: UUID of related job (optional)
        
    Returns:
        LedgerEvent instance if successful, None if failed
        
    Example:
        >>> await log_clip_event(
        ...     db=db,
        ...     clip_id=clip.id,
        ...     event_type="clip_created",
        ...     metadata={
        ...         "start_ms": 0,
        ...         "end_ms": 10000,
        ...         "visual_score": 0.85
        ...     }
        ... )
    """
    return await log_event(
        db=db,
        event_type=event_type,
        entity_type="clip",
        entity_id=str(clip_id),
        metadata=metadata,
        severity=severity,
        job_id=job_id,
        clip_id=clip_id
    )
