"""
Database persistence for rule weights.
"""
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.rules_engine.models import AdaptiveRuleSet


async def save_rules(
    db: AsyncSession,
    rules: AdaptiveRuleSet
) -> None:
    """
    Save rule weights to database.
    
    Uses UPSERT to insert or update existing rules.
    
    Args:
        db: Database session
        rules: Rule set to save
    """
    # UPSERT query
    query = text("""
        INSERT INTO rules_engine_weights (platform, weights, updated_at)
        VALUES (:platform, :weights, :updated_at)
        ON CONFLICT (platform)
        DO UPDATE SET
            weights = EXCLUDED.weights,
            updated_at = EXCLUDED.updated_at
    """)
    
    # Convert weights dict to JSON string for SQLite compatibility
    weights_json = json.dumps(rules.weights)
    
    await db.execute(
        query,
        {
            "platform": rules.platform,
            "weights": weights_json,
            "updated_at": rules.updated_at
        }
    )
    
    await db.commit()
