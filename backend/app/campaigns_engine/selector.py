"""Clip selection logic for campaigns orchestrator."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Clip, ClipStatus, BestClipDecisionModel
from app.rules_engine import RuleEngine
from app.campaigns_engine.schemas import BestClipDecision, ClipScore
from app.ledger import log_event


async def select_best_clip_for_platform(
    db: AsyncSession,
    video_asset_id: UUID,
    platform: str,
) -> BestClipDecision:
    """
    Select the best clip for a video asset on a specific platform.
    
    Uses Rule Engine to evaluate all READY clips and selects the one with highest score.
    Stores the decision in best_clip_decisions table and logs to ledger.
    
    Args:
        db: Database session
        video_asset_id: UUID of the video asset
        platform: Platform name (tiktok, instagram, youtube)
    
    Returns:
        BestClipDecision with selected clip and score
    
    Raises:
        ValueError: If no READY clips found for the video asset
    """
    # Load all READY clips for this video asset
    stmt = select(Clip).where(
        Clip.video_asset_id == video_asset_id,
        Clip.status == ClipStatus.READY
    )
    result = await db.execute(stmt)
    clips = result.scalars().all()
    
    if not clips:
        raise ValueError(f"No READY clips found for video_asset_id={video_asset_id}")
    
    # Evaluate each clip with Rule Engine
    engine = RuleEngine()
    scores: list[ClipScore] = []
    
    for clip in clips:
        score = await engine.evaluate_clip(db, clip.id, platform)
        scores.append(ClipScore(
            clip_id=clip.id,
            platform=platform,
            score=score
        ))
    
    # Select clip with highest score
    best_score = max(scores, key=lambda s: s.score)
    best_clip = next(c for c in clips if c.id == best_score.clip_id)
    
    # Create decision object
    decision = BestClipDecision(
        video_asset_id=video_asset_id,
        platform=platform,
        clip_id=best_clip.id,
        score=best_score.score,
        decided_at=datetime.utcnow()
    )
    
    # UPSERT to best_clip_decisions table
    await _save_decision_to_db(db, decision)
    
    # Log to ledger
    await log_event(
        db=db,
        event_type="best_clip_selected",
        entity_type="video_asset",
        entity_id=str(video_asset_id),
        metadata={
            "platform": platform,
            "clip_id": str(best_clip.id),
            "score": best_score.score,
            "num_candidates": len(clips)
        }
    )
    
    return decision


async def select_best_clips_for_platforms(
    db: AsyncSession,
    video_asset_id: UUID,
    platforms: list[str],
) -> list[BestClipDecision]:
    """
    Select best clips for multiple platforms.
    
    Args:
        db: Database session
        video_asset_id: UUID of the video asset
        platforms: List of platform names
    
    Returns:
        List of BestClipDecision, one per platform
    """
    decisions = []
    
    for platform in platforms:
        decision = await select_best_clip_for_platform(
            db=db,
            video_asset_id=video_asset_id,
            platform=platform
        )
        decisions.append(decision)
    
    return decisions


async def get_best_clip_decision(
    db: AsyncSession,
    video_asset_id: UUID,
    platform: str,
) -> Optional[BestClipDecision]:
    """
    Get existing best clip decision from database.
    
    Does NOT recalculate - only reads from best_clip_decisions table.
    
    Args:
        db: Database session
        video_asset_id: UUID of the video asset
        platform: Platform name
    
    Returns:
        BestClipDecision if found, None otherwise
    """
    stmt = select(BestClipDecisionModel).where(
        BestClipDecisionModel.video_asset_id == video_asset_id,
        BestClipDecisionModel.platform == platform
    )
    result = await db.execute(stmt)
    decision_model = result.scalar_one_or_none()
    
    if not decision_model:
        return None
    
    return BestClipDecision(
        video_asset_id=decision_model.video_asset_id,
        platform=decision_model.platform,
        clip_id=decision_model.clip_id,
        score=decision_model.score,
        decided_at=decision_model.decided_at
    )


async def _save_decision_to_db(
    db: AsyncSession,
    decision: BestClipDecision,
) -> None:
    """
    Save or update decision in best_clip_decisions table.
    
    Uses check-then-insert/update pattern for SQLite compatibility.
    """
    # Check if decision already exists
    stmt = select(BestClipDecisionModel).where(
        BestClipDecisionModel.video_asset_id == decision.video_asset_id,
        BestClipDecisionModel.platform == decision.platform
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing decision
        existing.clip_id = decision.clip_id
        existing.score = decision.score
        existing.decided_at = decision.decided_at
    else:
        # Insert new decision
        new_decision = BestClipDecisionModel(
            video_asset_id=decision.video_asset_id,
            platform=decision.platform,
            clip_id=decision.clip_id,
            score=decision.score,
            decided_at=decision.decided_at
        )
        db.add(new_decision)
    
    await db.commit()
