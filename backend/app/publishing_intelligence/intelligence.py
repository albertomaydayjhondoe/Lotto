"""
Publishing Intelligence Layer (APIL)
Provides priority calculation, forecasting, and intelligent auto-scheduling
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from uuid import UUID, uuid4
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Clip, PublishLogModel, Campaign, SocialAccountModel
from app.core.config import settings
from app.ledger.service import log_event
from app.publishing_intelligence.models import (
    PriorityCalculation,
    PlatformForecast,
    GlobalForecast,
    ConflictInfo,
    AutoScheduleResponse
)

# Configuration constants
PLATFORM_WINDOWS = settings.PLATFORM_WINDOWS
MIN_GAP_MINUTES = settings.MIN_GAP_MINUTES
DEFAULT_TIMEZONE = settings.DEFAULT_TIMEZONE


async def calculate_priority(
    db: AsyncSession,
    clip_id: str,
    platform: str
) -> PriorityCalculation:
    """
    Calculate dynamic priority for a clip based on multiple factors
    
    Formula:
    priority = (visual_score * 0.4) +
               (engagement_score * 0.3) +
               (predicted_virality * 0.2) +
               (campaign_weight * 0.1) +
               delay_penalty
    
    All components normalized to 0-100 scale
    """
    clip_uuid = UUID(clip_id) if isinstance(clip_id, str) else clip_id
    
    # Fetch clip
    clip_query = select(Clip).where(Clip.id == clip_uuid)
    clip_result = await db.execute(clip_query)
    clip = clip_result.scalar_one_or_none()
    
    if not clip:
        raise ValueError(f"Clip {clip_id} not found")
    
    # 1. Visual score (0-100, already normalized)
    visual_score = clip.visual_score or 0.0
    
    # 2. Engagement score (simulated from metadata or params)
    # In real scenario: fetch from analytics or metadata
    engagement_score = 0.0
    if clip.params and isinstance(clip.params, dict):
        engagement_score = clip.params.get("engagement_score", 0.0)
    
    # 3. Predicted virality (use rule engine estimation)
    # Simple heuristic: higher visual score + recent clip = higher virality
    predicted_virality = _estimate_virality(clip, platform)
    
    # 4. Campaign weight (larger budget = higher priority)
    campaign_weight = await _calculate_campaign_weight(db, clip_uuid)
    
    # 5. Delay penalty (older clips get priority boost)
    delay_penalty = _calculate_delay_penalty(clip)
    
    # Calculate final priority
    priority = (
        (visual_score * 0.4) +
        (engagement_score * 0.3) +
        (predicted_virality * 0.2) +
        (campaign_weight * 0.1) +
        delay_penalty
    )
    
    # Cap at 100
    priority = min(100.0, max(0.0, priority))
    
    breakdown = {
        "visual_score_contribution": visual_score * 0.4,
        "engagement_score_contribution": engagement_score * 0.3,
        "predicted_virality_contribution": predicted_virality * 0.2,
        "campaign_weight_contribution": campaign_weight * 0.1,
        "delay_penalty_contribution": delay_penalty
    }
    
    return PriorityCalculation(
        clip_id=str(clip_uuid),
        priority=priority,
        visual_score=visual_score,
        engagement_score=engagement_score,
        predicted_virality=predicted_virality,
        campaign_weight=campaign_weight,
        delay_penalty=delay_penalty,
        breakdown=breakdown
    )


def _estimate_virality(clip: Clip, platform: str) -> float:
    """
    Estimate virality potential (0-100)
    Uses visual score and platform-specific heuristics
    """
    base_virality = (clip.visual_score or 0.0) * 0.6
    
    # Platform-specific bonuses
    platform_multipliers = {
        "tiktok": 1.3,    # TikTok favors viral content
        "instagram": 1.1,  # Instagram moderate virality
        "youtube": 1.0     # YouTube slower viral spread
    }
    
    multiplier = platform_multipliers.get(platform, 1.0)
    virality = base_virality * multiplier
    
    return min(100.0, virality)


async def _calculate_campaign_weight(db: AsyncSession, clip_id: UUID) -> float:
    """
    Calculate campaign weight (0-100) based on associated campaigns
    Larger budgets = higher weight
    """
    # Fetch campaigns for this clip
    campaign_query = select(Campaign).where(Campaign.clip_id == clip_id)
    campaign_result = await db.execute(campaign_query)
    campaigns = campaign_result.scalars().all()
    
    if not campaigns:
        return 0.0
    
    # Sum budgets (in cents) and normalize
    total_budget_cents = sum(c.budget_cents for c in campaigns)
    
    # Normalize: $100 = 50 points, $500 = 100 points
    # Formula: min(100, budget_cents / 50000 * 100)
    weight = min(100.0, (total_budget_cents / 50000) * 100)
    
    return weight


def _calculate_delay_penalty(clip: Clip) -> float:
    """
    Calculate delay penalty/boost (0-20 points)
    Older clips get priority boost to avoid staleness
    """
    if not clip.created_at:
        return 0.0
    
    age_hours = (datetime.utcnow() - clip.created_at).total_seconds() / 3600
    
    # 0-24h: 0 penalty
    # 24-48h: +5 points
    # 48-72h: +10 points
    # 72h+: +20 points (max boost)
    
    if age_hours < 24:
        return 0.0
    elif age_hours < 48:
        return 5.0
    elif age_hours < 72:
        return 10.0
    else:
        return 20.0


async def get_global_forecast(db: AsyncSession) -> GlobalForecast:
    """
    Generate forecast for all platforms showing available slots and saturation
    """
    now = datetime.utcnow()
    forecast_date = now
    
    instagram_forecast = await _get_platform_forecast(db, "instagram", now)
    tiktok_forecast = await _get_platform_forecast(db, "tiktok", now)
    youtube_forecast = await _get_platform_forecast(db, "youtube", now)
    
    return GlobalForecast(
        forecast_date=forecast_date,
        instagram=instagram_forecast,
        tiktok=tiktok_forecast,
        youtube=youtube_forecast
    )


async def _get_platform_forecast(
    db: AsyncSession,
    platform: str,
    reference_time: datetime
) -> PlatformForecast:
    """
    Calculate forecast for a single platform
    """
    window = PLATFORM_WINDOWS.get(platform, {"start_hour": 18, "end_hour": 23})
    min_gap = MIN_GAP_MINUTES.get(platform, 60)
    
    start_hour = window["start_hour"]
    end_hour = window["end_hour"]
    
    # Calculate window duration in minutes
    if end_hour < start_hour:  # Crosses midnight (e.g., TikTok 16-24)
        window_duration_minutes = (24 - start_hour + end_hour) * 60
    else:
        window_duration_minutes = (end_hour - start_hour) * 60
    
    # Theoretical max slots per day
    max_slots_per_day = window_duration_minutes // min_gap
    
    # Count scheduled logs for today
    today_start = reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    scheduled_query = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.platform == platform,
            PublishLogModel.schedule_type == "scheduled",
            PublishLogModel.scheduled_for >= today_start,
            PublishLogModel.scheduled_for < today_end
        )
    )
    scheduled_result = await db.execute(scheduled_query)
    scheduled_count = scheduled_result.scalar() or 0
    
    # Calculate remaining slots
    slots_remaining = max(0, max_slots_per_day - scheduled_count)
    
    # Calculate risk level
    utilization = scheduled_count / max_slots_per_day if max_slots_per_day > 0 else 0
    if utilization < 0.5:
        risk = "low"
    elif utilization < 0.8:
        risk = "medium"
    else:
        risk = "high"
    
    # Find next available slot
    next_slot = await _find_next_slot(db, platform, reference_time)
    
    return PlatformForecast(
        platform=platform,
        next_slot=next_slot,
        slots_remaining_today=slots_remaining,
        risk=risk,
        scheduled_count=scheduled_count,
        window_start_hour=start_hour,
        window_end_hour=end_hour,
        min_gap_minutes=min_gap
    )


async def _find_next_slot(
    db: AsyncSession,
    platform: str,
    after_time: datetime
) -> Optional[datetime]:
    """
    Find the next available slot for a platform
    """
    window = PLATFORM_WINDOWS.get(platform, {"start_hour": 18, "end_hour": 23})
    min_gap = MIN_GAP_MINUTES.get(platform, 60)
    
    start_hour = window["start_hour"]
    end_hour = window["end_hour"]
    
    # Start from after_time
    candidate = after_time + timedelta(minutes=5)  # Small buffer
    
    # Adjust to next window if outside
    candidate_hour = candidate.hour
    if start_hour <= end_hour:  # Normal window
        if candidate_hour < start_hour:
            candidate = candidate.replace(hour=start_hour, minute=0, second=0)
        elif candidate_hour >= end_hour:
            # Move to next day
            candidate = (candidate + timedelta(days=1)).replace(hour=start_hour, minute=0, second=0)
    else:  # Crosses midnight (e.g., TikTok 16-24)
        if candidate_hour < start_hour and candidate_hour >= end_hour:
            candidate = candidate.replace(hour=start_hour, minute=0, second=0)
    
    # Check for conflicts with existing scheduled logs
    max_attempts = 20  # Prevent infinite loops
    for _ in range(max_attempts):
        conflict = await _check_slot_conflict(db, platform, candidate, min_gap)
        if not conflict:
            return candidate
        # Move to next potential slot
        candidate = candidate + timedelta(minutes=min_gap)
    
    return None  # No slot found


async def _check_slot_conflict(
    db: AsyncSession,
    platform: str,
    proposed_time: datetime,
    min_gap_minutes: int
) -> bool:
    """
    Check if proposed time conflicts with existing scheduled logs
    Returns True if conflict exists
    """
    buffer = timedelta(minutes=min_gap_minutes)
    
    conflict_query = select(PublishLogModel).where(
        and_(
            PublishLogModel.platform == platform,
            PublishLogModel.schedule_type == "scheduled",
            PublishLogModel.status == "scheduled",
            PublishLogModel.scheduled_for >= proposed_time - buffer,
            PublishLogModel.scheduled_for <= proposed_time + buffer
        )
    )
    
    conflict_result = await db.execute(conflict_query)
    conflicts = conflict_result.scalars().all()
    
    return len(conflicts) > 0


async def auto_schedule_clip(
    db: AsyncSession,
    clip_id: str,
    platform: str,
    social_account_id: Optional[str] = None,
    force_slot: Optional[datetime] = None
) -> AutoScheduleResponse:
    """
    Intelligently auto-schedule a clip
    
    Steps:
    1. Calculate priority
    2. Get forecast
    3. Select best slot
    4. Check for conflicts
    5. Create PublishLogModel with status="scheduled"
    6. Log ledger event
    """
    clip_uuid = UUID(clip_id) if isinstance(clip_id, str) else clip_id
    
    # 1. Calculate priority
    priority_calc = await calculate_priority(db, clip_id, platform)
    
    # 2. Get forecast
    forecast = await get_global_forecast(db)
    platform_forecast = getattr(forecast, platform)
    
    # 3. Select slot
    if force_slot:
        scheduled_for = force_slot
    else:
        scheduled_for = platform_forecast.next_slot
        if not scheduled_for:
            raise ValueError(f"No available slots for {platform}")
    
    # 4. Check for conflicts and resolve
    conflict_info = await _resolve_conflicts(
        db, platform, scheduled_for, priority_calc.priority
    )
    
    # If conflict shifted our time, update
    if conflict_info.detected and conflict_info.shifted_slot:
        scheduled_for = conflict_info.shifted_slot
    
    # 5. Get or create social account
    if not social_account_id:
        # Get first available account for platform
        account_query = select(SocialAccountModel).where(
            SocialAccountModel.platform == platform
        ).limit(1)
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()
        if not account:
            raise ValueError(f"No social account found for {platform}")
        social_account_id = str(account.id)
    
    # 6. Create PublishLogModel
    publish_log = PublishLogModel(
        id=uuid4(),
        clip_id=clip_uuid,
        platform=platform,
        social_account_id=UUID(social_account_id),
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=scheduled_for,
        scheduled_by="auto_intelligence",
        metadata={
            "priority": priority_calc.priority,
            "auto_scheduled": True,
            "priority_breakdown": priority_calc.breakdown
        }
    )
    
    db.add(publish_log)
    await db.commit()
    await db.refresh(publish_log)
    
    # 7. Log ledger event
    await log_event(
        db=db,
        event_type="auto_schedule_created",
        entity_type="publish_log",
        entity_id=publish_log.id,
        metadata={
            "clip_id": str(clip_uuid),
            "platform": platform,
            "scheduled_for": scheduled_for.isoformat(),
            "priority": priority_calc.priority,
            "conflict_detected": conflict_info.detected
        }
    )
    
    reason = None
    if conflict_info.detected:
        reason = f"Scheduled with priority {priority_calc.priority:.1f}. {conflict_info.resolution}"
    else:
        reason = f"Scheduled with priority {priority_calc.priority:.1f}"
    
    return AutoScheduleResponse(
        publish_log_id=str(publish_log.id),
        clip_id=str(clip_uuid),
        platform=platform,
        scheduled_for=scheduled_for,
        priority=priority_calc.priority,
        conflict_info=conflict_info,
        reason=reason
    )


async def _resolve_conflicts(
    db: AsyncSession,
    platform: str,
    proposed_time: datetime,
    proposed_priority: float
) -> ConflictInfo:
    """
    Check for conflicts and resolve by priority
    
    If higher priority: take the slot, shift lower priority
    If lower priority: get shifted to next slot
    """
    min_gap = MIN_GAP_MINUTES.get(platform, 60)
    buffer = timedelta(minutes=min_gap)
    
    # Find conflicting logs
    conflict_query = select(PublishLogModel).where(
        and_(
            PublishLogModel.platform == platform,
            PublishLogModel.schedule_type == "scheduled",
            PublishLogModel.status == "scheduled",
            PublishLogModel.scheduled_for >= proposed_time - buffer,
            PublishLogModel.scheduled_for <= proposed_time + buffer
        )
    )
    
    conflict_result = await db.execute(conflict_query)
    conflicts = conflict_result.scalars().all()
    
    if not conflicts:
        return ConflictInfo(detected=False)
    
    # Take the first conflict (closest time)
    conflict_log = conflicts[0]
    conflict_priority = 0.0
    if conflict_log.metadata and isinstance(conflict_log.metadata, dict):
        conflict_priority = conflict_log.metadata.get("priority", 0.0)
    
    # Compare priorities
    if proposed_priority > conflict_priority:
        # We win: shift the conflicting log
        new_slot = await _find_next_slot(db, platform, proposed_time + buffer)
        if new_slot:
            original_time = conflict_log.scheduled_for
            conflict_log.scheduled_for = new_slot
            await db.commit()
            
            # Log conflict events
            await log_event(
                db=db,
                event_type="schedule_conflict_detected",
                entity_type="publish_log",
                entity_id=conflict_log.id,
                metadata={
                    "original_slot": original_time.isoformat(),
                    "new_slot": new_slot.isoformat(),
                    "reason": "Lower priority, shifted by higher priority request"
                }
            )
            
            await log_event(
                db=db,
                event_type="schedule_conflict_resolved",
                entity_type="publish_log",
                entity_id=conflict_log.id,
                metadata={
                    "shifted_to": new_slot.isoformat(),
                    "conflict_priority": conflict_priority,
                    "winner_priority": proposed_priority
                }
            )
            
            return ConflictInfo(
                detected=True,
                conflicting_log_id=str(conflict_log.id),
                resolution=f"Higher priority ({proposed_priority:.1f} > {conflict_priority:.1f}). Conflicting log shifted.",
                original_slot=original_time,
                shifted_slot=proposed_time  # We keep proposed_time
            )
    
    else:
        # We lose: find next slot for us
        new_slot = await _find_next_slot(db, platform, proposed_time + buffer)
        if not new_slot:
            raise ValueError(f"No available slots after conflict resolution")
        
        await log_event(
            db=db,
            event_type="schedule_conflict_detected",
            entity_type="publish_log",
            entity_id=None,  # Log being created
            metadata={
                "proposed_slot": proposed_time.isoformat(),
                "shifted_to": new_slot.isoformat(),
                "reason": "Lower priority, shifted to next available slot"
            }
        )
        
        return ConflictInfo(
            detected=True,
            conflicting_log_id=str(conflict_log.id),
            resolution=f"Lower priority ({proposed_priority:.1f} <= {conflict_priority:.1f}). Shifted to next slot.",
            original_slot=proposed_time,
            shifted_slot=new_slot
        )
    
    return ConflictInfo(detected=False)
