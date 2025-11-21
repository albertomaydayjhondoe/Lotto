from datetime import datetime, timedelta
from typing import Tuple, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.database import Clip, SocialAccountModel, PublishLogModel
from app.core.config import Settings
from app.ledger import log_event
from .models import ScheduleRequest, ScheduleResponse, PublishLogScheduledInfo

settings = Settings()


async def validate_and_adjust_schedule(
    db: AsyncSession,
    request: ScheduleRequest
) -> Tuple[datetime, Optional[datetime], Optional[str]]:
    """
    Validate and adjust scheduled time to respect platform windows and minimum gaps.
    
    Returns:
        Tuple of (adjusted_scheduled_for, adjusted_window_end, reason_string)
    """
    platform = request.platform.lower()
    scheduled_for = request.scheduled_for
    window_end = request.scheduled_window_end
    
    # Convert string IDs to UUID
    account_uuid = UUID(request.social_account_id) if isinstance(request.social_account_id, str) else request.social_account_id
    
    # Get platform window from config
    if platform not in settings.PLATFORM_WINDOWS:
        return scheduled_for, window_end, f"Unknown platform: {platform}"
    
    window = settings.PLATFORM_WINDOWS[platform]
    start_hour = window["start_hour"]
    end_hour = window["end_hour"]
    
    # Check if scheduled time is within platform window
    scheduled_hour = scheduled_for.hour
    scheduled_minute = scheduled_for.minute
    scheduled_time_decimal = scheduled_hour + (scheduled_minute / 60.0)
    
    # Handle windows that cross midnight (e.g., 22:00 to 02:00)
    if end_hour < start_hour:
        # Window crosses midnight
        within_window = (scheduled_time_decimal >= start_hour) or (scheduled_time_decimal < end_hour)
    else:
        # Normal window
        within_window = (start_hour <= scheduled_time_decimal < end_hour)
    
    reasons = []
    adjusted_time = scheduled_for
    adjusted_window = window_end
    
    if not within_window:
        # Adjust to start of window on same day or next day
        if scheduled_time_decimal < start_hour:
            # Before window starts today - move to window start today
            adjusted_time = scheduled_for.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        else:
            # After window ends today - move to window start tomorrow
            next_day = scheduled_for + timedelta(days=1)
            adjusted_time = next_day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        reasons.append(f"Moved to platform window ({start_hour}:00-{end_hour}:00)")
        
        # Adjust window_end if it exists
        if window_end:
            time_shift = adjusted_time - scheduled_for
            adjusted_window = window_end + time_shift
    
    # Check minimum gap with existing posts on same platform + account
    min_gap_minutes = settings.MIN_GAP_MINUTES.get(platform, 60)
    min_gap = timedelta(minutes=min_gap_minutes)
    
    # Query existing scheduled/pending/processing logs for same platform+account
    query = select(PublishLogModel).where(
        and_(
            PublishLogModel.platform == request.platform,
            PublishLogModel.social_account_id == account_uuid,
            PublishLogModel.status.in_(["scheduled", "pending", "processing"]),
            PublishLogModel.scheduled_for.isnot(None)
        )
    )
    result = await db.execute(query)
    existing_logs = result.scalars().all()
    
    # Find conflicts
    adjusted_again = False
    for existing_log in existing_logs:
        if existing_log.scheduled_for:
            time_diff = abs((adjusted_time - existing_log.scheduled_for).total_seconds())
            if time_diff < min_gap.total_seconds():
                # Too close! Push forward
                if adjusted_time < existing_log.scheduled_for:
                    # Our time is before existing - move to after existing + gap
                    adjusted_time = existing_log.scheduled_for + min_gap
                else:
                    # Our time is after existing but too close - move further
                    adjusted_time = existing_log.scheduled_for + min_gap
                
                adjusted_again = True
                reasons.append(f"Adjusted {min_gap_minutes}min forward to respect minimum gap")
                
                # Adjust window_end proportionally
                if window_end:
                    adjusted_window = adjusted_time + (window_end - scheduled_for)
    
    # Re-check if adjusted time is still within window
    if adjusted_again:
        adjusted_hour = adjusted_time.hour + (adjusted_time.minute / 60.0)
        
        if end_hour < start_hour:
            # Window crosses midnight
            still_within = (adjusted_hour >= start_hour) or (adjusted_hour < end_hour)
        else:
            still_within = (start_hour <= adjusted_hour < end_hour)
        
        if not still_within:
            # Pushed outside window - move to next window start
            if adjusted_hour < start_hour:
                # Before window today
                adjusted_time = adjusted_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            else:
                # After window today - move to tomorrow's window
                next_day = adjusted_time + timedelta(days=1)
                adjusted_time = next_day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            
            reasons.append(f"Re-adjusted to stay within platform window")
            
            if window_end:
                adjusted_window = adjusted_time + (window_end - scheduled_for)
    
    reason_text = "; ".join(reasons) if reasons else None
    return adjusted_time, adjusted_window, reason_text


async def schedule_publication(
    db: AsyncSession,
    request: ScheduleRequest
) -> ScheduleResponse:
    """
    Schedule a publication for a clip.
    
    Creates a PublishLogModel with status="scheduled" and validates/adjusts the time.
    """
    # Convert string IDs to UUID for queries
    clip_uuid = UUID(request.clip_id) if isinstance(request.clip_id, str) else request.clip_id
    account_uuid = UUID(request.social_account_id) if isinstance(request.social_account_id, str) else request.social_account_id
    
    # Validate clip exists
    clip_query = select(Clip).where(Clip.id == clip_uuid)
    clip_result = await db.execute(clip_query)
    clip = clip_result.scalar_one_or_none()
    
    if not clip:
        return ScheduleResponse(
            publish_log_id="",
            status="rejected",
            reason=f"Clip not found: {request.clip_id}"
        )
    
    # Validate social account exists and matches platform
    account_query = select(SocialAccountModel).where(SocialAccountModel.id == account_uuid)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    if not account:
        return ScheduleResponse(
            publish_log_id="",
            status="rejected",
            reason=f"Social account not found: {request.social_account_id}"
        )
    
    if account.platform.lower() != request.platform.lower():
        return ScheduleResponse(
            publish_log_id="",
            status="rejected",
            reason=f"Platform mismatch: account is {account.platform}, request is {request.platform}"
        )
    
    # Validate and adjust schedule
    adjusted_for, adjusted_window, reason = await validate_and_adjust_schedule(db, request)
    
    # Create scheduled publish log
    log = PublishLogModel(
        clip_id=clip_uuid,
        platform=request.platform,
        social_account_id=account_uuid,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=adjusted_for,
        scheduled_window_end=adjusted_window,
        scheduled_by=request.scheduled_by,
        extra_metadata={
            "original_scheduled_for": request.scheduled_for.isoformat(),
            "original_window_end": request.scheduled_window_end.isoformat() if request.scheduled_window_end else None,
            "adjustment_reason": reason
        }
    )
    
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    # Log to ledger
    await log_event(
        db=db,
        event_type="publish_scheduled_created",
        entity_type="publish_log",
        entity_id=str(log.id),
        metadata={
            "clip_id": request.clip_id,
            "platform": request.platform,
            "social_account_id": request.social_account_id,
            "scheduled_for": adjusted_for.isoformat(),
            "scheduled_window_end": adjusted_window.isoformat() if adjusted_window else None,
            "scheduled_by": request.scheduled_by,
            "status": "scheduled"
        }
    )
    
    if reason:
        await log_event(
            db=db,
            event_type="publish_scheduled_adjusted",
            entity_type="publish_log",
            entity_id=str(log.id),
            metadata={
                "clip_id": request.clip_id,
                "platform": request.platform,
                "original_time": request.scheduled_for.isoformat(),
                "adjusted_time": adjusted_for.isoformat(),
                "reason": reason
            }
        )
    
    return ScheduleResponse(
        publish_log_id=str(log.id),
        status="scheduled",
        reason=reason,
        scheduled_for=adjusted_for,
        scheduled_window_end=adjusted_window
    )


async def get_scheduled_logs_for_clip(
    db: AsyncSession,
    clip_id: str
) -> List[PublishLogScheduledInfo]:
    """Get all scheduled publish logs for a clip"""
    clip_uuid = UUID(clip_id) if isinstance(clip_id, str) else clip_id
    
    query = select(PublishLogModel).where(
        and_(
            PublishLogModel.clip_id == clip_uuid,
            PublishLogModel.schedule_type == "scheduled"
        )
    ).order_by(PublishLogModel.scheduled_for)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [PublishLogScheduledInfo.model_validate(log) for log in logs]


async def scheduler_tick(
    db: AsyncSession,
    now: Optional[datetime] = None,
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Execute scheduler tick: move due scheduled logs to pending status.
    
    Args:
        db: Database session
        now: Current time (defaults to utcnow)
        dry_run: If True, only count without modifying
    
    Returns:
        Tuple of (count_moved, list_of_log_ids)
    """
    if now is None:
        now = datetime.utcnow()
    
    # Find logs that are due (scheduled_for <= now and status=scheduled)
    query = select(PublishLogModel).where(
        and_(
            PublishLogModel.status == "scheduled",
            PublishLogModel.scheduled_for <= now
        )
    )
    
    result = await db.execute(query)
    due_logs = result.scalars().all()
    
    moved_ids = []
    
    for log in due_logs:
        if not dry_run:
            # Change status to pending
            log.status = "pending"
            log.extra_metadata = log.extra_metadata or {}
            log.extra_metadata["enqueued_at"] = now.isoformat()
            log.extra_metadata["enqueued_from_scheduled"] = True
            
            db.add(log)
            
            # Log event
            await log_event(
                db=db,
                event_type="publish_scheduled_enqueued",
                entity_type="publish_log",
                entity_id=str(log.id),
                metadata={
                    "clip_id": str(log.clip_id),
                    "platform": log.platform,
                    "social_account_id": str(log.social_account_id),
                    "scheduled_for": log.scheduled_for.isoformat(),
                    "enqueued_at": now.isoformat()
                }
            )
        
        moved_ids.append(str(log.id))
    
    if not dry_run:
        await db.commit()
    
    return len(moved_ids), moved_ids
