"""
Adaptive trainer - learns weights from ledger events.
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.ledger.models import LedgerEvent
from app.rules_engine.models import AdaptiveRuleSet, DEFAULT_WEIGHTS
from app.rules_engine.persistence import save_rules
from app.ledger import log_event


# Learning rate for weight updates
LEARNING_RATE = 0.05


async def train_rules(
    db: AsyncSession,
    platform: str
) -> AdaptiveRuleSet:
    """
    Train rule weights based on performance data from the ledger.
    
    Analyzes ledger events to identify successful clips and updates
    weights using gradient-like optimization.
    
    Args:
        db: Database session
        platform: Platform to train rules for
        
    Returns:
        Updated AdaptiveRuleSet
    """
    # Load current weights (from persistence or defaults)
    from app.rules_engine.loader import load_rules
    current_rules = await load_rules(db, platform)
    
    # Collect training examples from ledger
    training_examples = await _collect_training_examples(db, platform)
    
    if not training_examples:
        # No training data available, return current rules
        return current_rules
    
    # Update weights based on training examples
    new_weights = current_rules.weights.copy()
    
    for features, target_score in training_examples:
        # Compute current prediction
        predicted_score = sum(
            features.get(name, 0.0) * weight
            for name, weight in new_weights.items()
        )
        
        # Compute error
        error = target_score - predicted_score
        
        # Update weights (gradient descent-like)
        for feature_name in new_weights.keys():
            feature_value = features.get(feature_name, 0.0)
            new_weights[feature_name] += LEARNING_RATE * error * feature_value
    
    # Normalize weights to sum to ~1.0
    new_weights = _normalize_weights(new_weights)
    
    # Create updated rule set
    updated_rules = AdaptiveRuleSet(
        platform=platform,  # type: ignore
        weights=new_weights,
        updated_at=datetime.utcnow()
    )
    
    # Save to database
    await save_rules(db, updated_rules)
    
    # Log training event
    await log_event(
        db=db,
        event_type="rule_weight_updated",
        entity_type="rules_engine",
        entity_id=platform,
        metadata={
            "platform": platform,
            "new_weights": new_weights,
            "training_examples_count": len(training_examples)
        }
    )
    
    return updated_rules


async def _collect_training_examples(
    db: AsyncSession,
    platform: str,
    lookback_days: int = 7
) -> List[Tuple[Dict[str, float], float]]:
    """
    Collect training examples from ledger events.
    
    Returns list of (features, target_score) tuples.
    """
    training_examples = []
    
    # Look back N days for performance data
    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    
    # Find clip_evaluated events for this platform
    result = await db.execute(
        select(LedgerEvent)
        .where(
            and_(
                LedgerEvent.event_type == "clip_evaluated",
                LedgerEvent.entity_type == "clip",
                LedgerEvent.timestamp >= cutoff_date
            )
        )
        .order_by(LedgerEvent.timestamp.desc())
        .limit(100)
    )
    
    events = result.scalars().all()
    
    for event in events:
        metadata = event.event_data or {}
        
        # Check if this event is for the target platform
        if metadata.get("platform") != platform:
            continue
        
        features = metadata.get("features", {})
        score = metadata.get("score", 0.5)
        
        # Determine target based on engagement signals
        # For now, use a simple heuristic:
        # - If clip was published and got engagement, target = 1.0
        # - If clip was evaluated but never published, target = 0.5
        # - If clip had low score, target = 0.0
        
        target = _compute_target_score(score, metadata)
        
        if features:
            training_examples.append((features, target))
    
    return training_examples


def _compute_target_score(current_score: float, metadata: Dict) -> float:
    """
    Compute target score based on engagement signals.
    
    This is a simplified heuristic. In production, you'd analyze:
    - Views, likes, shares from social platforms
    - Retention rates
    - Conversion metrics
    """
    # Check for engagement signals in metadata
    engagement = metadata.get("engagement", {})
    
    if engagement:
        # If we have engagement data, use it
        views = engagement.get("views", 0)
        likes = engagement.get("likes", 0)
        
        if views > 1000 and likes > 50:
            return 1.0
        elif views > 100:
            return 0.7
        else:
            return 0.3
    
    # No engagement data - use current score as baseline
    # with slight regression toward mean
    if current_score > 0.7:
        return 0.8
    elif current_score < 0.3:
        return 0.2
    else:
        return 0.5


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize weights to sum to approximately 1.0.
    Also ensure no negative weights.
    """
    # Clip negative weights to 0
    weights = {name: max(0.0, w) for name, w in weights.items()}
    
    # Compute sum
    total = sum(weights.values())
    
    if total == 0:
        # All weights are zero, reset to defaults
        return DEFAULT_WEIGHTS.get("tiktok", {}).copy()
    
    # Normalize to sum to 1.0
    return {name: w / total for name, w in weights.items()}
