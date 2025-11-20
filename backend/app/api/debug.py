"""
Debug Endpoints (Development Only)

IMPORTANT: These endpoints should be protected with authentication in production.
For now, they are open for development purposes only.
Set DEBUG_ENDPOINTS_ENABLED=False in production to disable these endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, Any

from app.core.database import get_db
from app.models.database import Job, JobStatus, Clip, ClipStatus, VideoAsset
from app.core.logging import get_logger
from app.ledger import get_recent_events, get_total_events
from app.ledger.models import LedgerEvent

router = APIRouter()
logger = get_logger(__name__)


@router.get("/jobs/summary")
async def get_jobs_summary(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get summary of jobs by status.
    
    Returns:
        {
            "total": int,
            "by_status": {
                "pending": int,
                "processing": int,
                "retry": int,
                "completed": int,
                "failed": int
            }
        }
    """
    logger.info("Fetching jobs summary")
    
    try:
        # Get total count
        total_result = await db.execute(
            select(func.count(Job.id))
        )
        total = total_result.scalar() or 0
        
        # Get counts by status
        status_result = await db.execute(
            select(Job.status, func.count(Job.id))
            .group_by(Job.status)
        )
        status_counts = {status: count for status, count in status_result.all()}
        
        # Build response with all possible statuses
        by_status = {
            "pending": status_counts.get(JobStatus.PENDING, 0),
            "processing": status_counts.get(JobStatus.PROCESSING, 0),
            "retry": status_counts.get(JobStatus.RETRY, 0),
            "completed": status_counts.get(JobStatus.COMPLETED, 0),
            "failed": status_counts.get(JobStatus.FAILED, 0),
        }
        
        logger.info("Jobs summary retrieved", extra={"total": total, "by_status": by_status})
        
        return {
            "total": total,
            "by_status": by_status
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs summary: {str(e)}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching jobs summary: {str(e)}"
        )


@router.get("/clips/summary")
async def get_clips_summary(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get summary of clips by status.
    
    Returns:
        {
            "total": int,
            "by_status": {
                "pending": int,
                "processing": int,
                "ready": int,
                "published": int,
                "failed": int
            }
        }
    """
    logger.info("Fetching clips summary")
    
    try:
        # Get total count
        total_result = await db.execute(
            select(func.count(Clip.id))
        )
        total = total_result.scalar() or 0
        
        # Get counts by status
        status_result = await db.execute(
            select(Clip.status, func.count(Clip.id))
            .group_by(Clip.status)
        )
        status_counts = {status: count for status, count in status_result.all()}
        
        # Build response with all possible statuses
        by_status = {
            "pending": status_counts.get(ClipStatus.PENDING, 0),
            "processing": status_counts.get(ClipStatus.PROCESSING, 0),
            "ready": status_counts.get(ClipStatus.READY, 0),
            "published": status_counts.get(ClipStatus.PUBLISHED, 0),
            "failed": status_counts.get(ClipStatus.FAILED, 0),
        }
        
        logger.info("Clips summary retrieved", extra={"total": total, "by_status": by_status})
        
        return {
            "total": total,
            "by_status": by_status
        }
        
    except Exception as e:
        logger.error(f"Error fetching clips summary: {str(e)}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clips summary: {str(e)}"
        )


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Health check endpoint.
    
    Verifies:
    - Database connection
    - Main tables exist (jobs, video_assets, clips)
    
    Returns:
        200: {"status": "ok"}
        500: {"status": "error", "detail": "error message"}
    """
    logger.info("Health check requested")
    
    try:
        # Test database connection with simple query
        await db.execute(text("SELECT 1"))
        
        # Verify main tables exist by checking we can query them
        # This will raise an exception if tables don't exist
        await db.execute(select(func.count(Job.id)))
        await db.execute(select(func.count(VideoAsset.id)))
        await db.execute(select(func.count(Clip.id)))
        
        logger.info("Health check passed")
        
        return {"status": "ok"}
        
    except Exception as e:
        error_msg = f"Database health check failed: {str(e)}"
        logger.error(error_msg, extra={"error": str(e)})
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/ledger/recent")
async def get_ledger_recent(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent ledger events.
    
    Returns the most recent system events from the ledger in descending order
    (newest first). Useful for monitoring, debugging, and understanding system
    activity.
    
    Query Parameters:
        limit: Number of events to return (default: 50, max: 500)
        
    Returns:
        {
            "events": [
                {
                    "id": "uuid",
                    "timestamp": "2025-11-20T10:30:00Z",
                    "event_type": "clip_created",
                    "entity_type": "clip",
                    "entity_id": "uuid",
                    "metadata": {...},
                    "severity": "INFO",
                    "worker_id": null,
                    "job_id": "uuid",
                    "clip_id": "uuid"
                },
                ...
            ],
            "total": 150,
            "limit": 50
        }
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 500)
        
        # Get recent events
        events = await get_recent_events(db, limit=limit)
        
        # Get total count
        total = await get_total_events(db)
        
        # Format response
        events_data = [
            {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "event_type": event.event_type,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "metadata": event.event_data or {},  # Return as 'metadata' in API
                "severity": event.severity.value if event.severity else "INFO",
                "worker_id": event.worker_id,
                "job_id": str(event.job_id) if event.job_id else None,
                "clip_id": str(event.clip_id) if event.clip_id else None
            }
            for event in events
        ]
        
        logger.info(
            f"Retrieved {len(events)} ledger events",
            extra={"count": len(events), "limit": limit, "total": total}
        )
        
        return {
            "events": events_data,
            "total": total,
            "limit": limit
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve ledger events: {str(e)}"
        logger.error(error_msg, extra={"error": str(e)})
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
