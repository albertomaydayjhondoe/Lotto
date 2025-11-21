from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.core.database import get_db
from .models import ScheduleRequest, ScheduleResponse, PublishLogScheduledInfo, SchedulerTickResponse
from .scheduler import schedule_publication, get_scheduled_logs_for_clip, scheduler_tick

router = APIRouter()


@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_publish(
    request: ScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a publication for future delivery.
    
    The scheduler will:
    - Validate the clip and social account exist
    - Check if scheduled time is within the platform's publishing window
    - Ensure minimum time gap between posts on the same account
    - Automatically adjust the time if needed
    - Create a PublishLogModel with status="scheduled"
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/publishing/schedule \
      -H "Content-Type: application/json" \
      -d '{
        "clip_id": "clip_123",
        "platform": "instagram",
        "social_account_id": "acc_456",
        "scheduled_for": "2024-01-15T20:00:00Z",
        "scheduled_by": "manual"
      }'
    ```
    
    Returns:
    - publish_log_id: ID of the created log
    - status: "scheduled" or "rejected"
    - reason: Explanation if time was adjusted or rejected
    - scheduled_for: Final scheduled time (may differ from request)
    - scheduled_window_end: End of scheduling window if provided
    """
    return await schedule_publication(db, request)


@router.get("/schedule/{clip_id}", response_model=List[PublishLogScheduledInfo])
async def get_scheduled_publications(
    clip_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all scheduled publications for a clip.
    
    Returns list of PublishLogModel entries with schedule_type="scheduled"
    ordered by scheduled_for time.
    
    Example:
    ```bash
    curl http://localhost:8000/publishing/schedule/clip_123
    ```
    """
    return await get_scheduled_logs_for_clip(db, clip_id)


@router.post("/scheduler/tick", response_model=SchedulerTickResponse)
async def execute_scheduler_tick(
    dry_run: bool = Query(default=False, description="If true, only count without modifying"),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute scheduler tick: move due scheduled logs to pending status.
    
    This endpoint should be called periodically (e.g., every minute via cron)
    to check for scheduled publications that are now due and move them to
    the pending queue for processing.
    
    Args:
    - dry_run: If true, only count logs without changing status
    
    Returns:
    - moved: Number of logs moved to pending
    - dry_run: Whether this was a dry run
    - log_ids: List of affected log IDs
    
    Example (production):
    ```bash
    curl -X POST http://localhost:8000/publishing/scheduler/tick
    ```
    
    Example (dry run for monitoring):
    ```bash
    curl -X POST "http://localhost:8000/publishing/scheduler/tick?dry_run=true"
    ```
    
    Cron job example (every minute):
    ```bash
    * * * * * curl -X POST http://localhost:8000/publishing/scheduler/tick
    ```
    """
    now = datetime.utcnow()
    moved, log_ids = await scheduler_tick(db, now, dry_run)
    
    return SchedulerTickResponse(
        moved=moved,
        dry_run=dry_run,
        log_ids=log_ids
    )
