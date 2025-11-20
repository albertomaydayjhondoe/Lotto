"""
Ledger core logic and utilities.

This module provides additional utilities for working with the ledger system,
such as querying events, analyzing patterns, and generating reports.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.ledger.models import LedgerEvent, EventSeverity


async def get_recent_events(
    db: AsyncSession,
    limit: int = 50
) -> List[LedgerEvent]:
    """
    Get the most recent ledger events.
    
    Args:
        db: Database session
        limit: Maximum number of events to return (default: 50)
        
    Returns:
        List of LedgerEvent instances, ordered by timestamp descending
    """
    result = await db.execute(
        select(LedgerEvent)
        .order_by(desc(LedgerEvent.timestamp))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_events_by_type(
    db: AsyncSession,
    event_type: str,
    limit: int = 100
) -> List[LedgerEvent]:
    """
    Get events filtered by type.
    
    Args:
        db: Database session
        event_type: Event type to filter by
        limit: Maximum number of events to return
        
    Returns:
        List of LedgerEvent instances
    """
    result = await db.execute(
        select(LedgerEvent)
        .where(LedgerEvent.event_type == event_type)
        .order_by(desc(LedgerEvent.timestamp))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_events_by_entity(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    limit: int = 100
) -> List[LedgerEvent]:
    """
    Get all events for a specific entity.
    
    Args:
        db: Database session
        entity_type: Type of entity (e.g., "video_asset", "job")
        entity_id: ID of the entity
        limit: Maximum number of events to return
        
    Returns:
        List of LedgerEvent instances, ordered by timestamp
    """
    result = await db.execute(
        select(LedgerEvent)
        .where(
            LedgerEvent.entity_type == entity_type,
            LedgerEvent.entity_id == entity_id
        )
        .order_by(LedgerEvent.timestamp)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_events_by_job(
    db: AsyncSession,
    job_id: str
) -> List[LedgerEvent]:
    """
    Get all events related to a specific job.
    
    Args:
        db: Database session
        job_id: UUID of the job
        
    Returns:
        List of LedgerEvent instances, ordered by timestamp
    """
    result = await db.execute(
        select(LedgerEvent)
        .where(LedgerEvent.job_id == job_id)
        .order_by(LedgerEvent.timestamp)
    )
    return list(result.scalars().all())


async def get_error_count(
    db: AsyncSession,
    since: Optional[datetime] = None
) -> int:
    """
    Count error events since a given timestamp.
    
    Args:
        db: Database session
        since: Only count errors after this timestamp (optional)
        
    Returns:
        Number of error events
    """
    query = select(func.count()).select_from(LedgerEvent).where(
        LedgerEvent.severity == EventSeverity.ERROR
    )
    
    if since:
        query = query.where(LedgerEvent.timestamp >= since)
    
    result = await db.execute(query)
    return result.scalar() or 0


async def get_total_events(db: AsyncSession) -> int:
    """
    Get total count of all events in the ledger.
    
    Args:
        db: Database session
        
    Returns:
        Total number of events
    """
    result = await db.execute(
        select(func.count()).select_from(LedgerEvent)
    )
    return result.scalar() or 0
