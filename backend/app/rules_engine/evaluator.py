"""
Clip evaluator - normalizes features and computes weighted scores.
"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Clip
from app.rules_engine.models import AdaptiveRuleSet
from app.ledger import log_event


async def evaluate_clip(
    db: AsyncSession,
    clip: Clip,
    rules: AdaptiveRuleSet,
    platform: str
) -> float:
    """
    Evaluate a clip and return a score between 0.0 and 1.0.
    
    Args:
        db: Database session
        clip: Clip to evaluate
        rules: Rule set with weights
        platform: Target platform
        
    Returns:
        Score between 0.0 and 1.0
    """
    # Normalize features to [0, 1] range
    features = _normalize_features(clip)
    
    # Apply weights
    score = 0.0
    for feature_name, feature_value in features.items():
        weight = rules.weights.get(feature_name, 0.0)
        score += feature_value * weight
    
    # Clamp to [0.0, 1.0]
    score = max(0.0, min(1.0, score))
    
    # Log evaluation event to ledger
    await log_event(
        db=db,
        event_type="clip_evaluated",
        entity_type="clip",
        entity_id=str(clip.id),
        metadata={
            "platform": platform,
            "score": score,
            "weights": rules.weights,
            "features": features
        }
    )
    
    return score


def _normalize_features(clip: Clip) -> Dict[str, float]:
    """
    Normalize clip features to [0, 1] range.
    
    Args:
        clip: Clip to extract features from
        
    Returns:
        Dictionary of normalized features
    """
    features = {}
    
    # visual_score - already in [0, 1]
    features["visual_score"] = min(1.0, max(0.0, clip.visual_score or 0.5))
    
    # duration_ms - normalize to [0, 1], cap at 60 seconds
    if clip.duration_ms:
        features["duration_ms"] = min(1.0, clip.duration_ms / 60000.0)
    else:
        features["duration_ms"] = 0.5
    
    # cut_position - relative position in video
    # If we have start_time and source video duration, we can compute this
    # For now, use a default of 0.5 (middle of video)
    features["cut_position"] = 0.5
    
    # motion_intensity - simulated for now (would come from video analysis)
    # Use a default value
    features["motion_intensity"] = 0.5
    
    return features


async def evaluate_clip_by_id(
    db: AsyncSession,
    clip_id: UUID,
    rules: AdaptiveRuleSet,
    platform: str
) -> float:
    """
    Evaluate a clip by ID.
    
    Args:
        db: Database session
        clip_id: ID of clip to evaluate
        rules: Rule set with weights
        platform: Target platform
        
    Returns:
        Score between 0.0 and 1.0
        
    Raises:
        ValueError: If clip not found
    """
    result = await db.execute(
        select(Clip).where(Clip.id == clip_id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise ValueError(f"Clip {clip_id} not found")
    
    return await evaluate_clip(db, clip, rules, platform)
