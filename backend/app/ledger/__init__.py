"""
Ledger module for system-wide event tracking and auditing.

This module provides comprehensive logging of all important system actions
in a structured, queryable format for:
- Worker learning and optimization
- Handler logic improvement
- Campaign optimization
- Anomaly detection
- AI context understanding

Usage:
    from app.ledger import log_event, log_job_event, log_clip_event
    
    # Log a generic event
    await log_event(
        db=db,
        event_type="video_uploaded",
        entity_type="video_asset",
        entity_id=str(video_id),
        metadata={"filename": "video.mp4"}
    )
    
    # Log a job event
    await log_job_event(
        db=db,
        job_id=job.id,
        event_type="job_created",
        metadata={"job_type": "cut_analysis"}
    )
    
    # Log a clip event
    await log_clip_event(
        db=db,
        clip_id=clip.id,
        event_type="clip_created",
        metadata={"visual_score": 0.85}
    )
"""

from app.ledger.models import LedgerEvent, EventSeverity
from app.ledger.service import log_event, log_job_event, log_clip_event
from app.ledger.ledger import (
    get_recent_events,
    get_events_by_type,
    get_events_by_entity,
    get_events_by_job,
    get_error_count,
    get_total_events
)

__all__ = [
    # Models
    "LedgerEvent",
    "EventSeverity",
    
    # Service functions
    "log_event",
    "log_job_event",
    "log_clip_event",
    
    # Query functions
    "get_recent_events",
    "get_events_by_type",
    "get_events_by_entity",
    "get_events_by_job",
    "get_error_count",
    "get_total_events",
]
