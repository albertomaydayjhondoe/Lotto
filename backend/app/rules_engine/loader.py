"""
Database loader for rule weights.
"""
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.rules_engine.models import AdaptiveRuleSet, DEFAULT_WEIGHTS


async def load_rules(
    db: AsyncSession,
    platform: str
) -> AdaptiveRuleSet:
    """
    Load rule weights from database.
    
    If no rules exist for the platform, returns default weights
    and optionally saves them to the database.
    
    Args:
        db: Database session
        platform: Platform to load rules for
        
    Returns:
        AdaptiveRuleSet for the platform
    """
    # Query database
    query = text("""
        SELECT platform, weights, updated_at
        FROM rules_engine_weights
        WHERE platform = :platform
    """)
    
    result = await db.execute(query, {"platform": platform})
    row = result.fetchone()
    
    if row:
        # Found existing rules
        # Parse JSON weights if stored as string
        weights = row.weights
        if isinstance(weights, str):
            weights = json.loads(weights)
        
        return AdaptiveRuleSet(
            platform=platform,  # type: ignore
            weights=weights,
            updated_at=row.updated_at
        )
    
    # No rules found, use defaults
    default_weights = DEFAULT_WEIGHTS.get(platform, DEFAULT_WEIGHTS["tiktok"])
    
    rules = AdaptiveRuleSet(
        platform=platform,  # type: ignore
        weights=default_weights,
        updated_at=datetime.utcnow()
    )
    
    # Optionally save defaults to database
    try:
        from app.rules_engine.persistence import save_rules
        await save_rules(db, rules)
    except Exception:
        # Ignore save errors (table might not exist yet)
        pass
    
    return rules
