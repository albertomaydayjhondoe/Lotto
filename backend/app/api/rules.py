"""
Platform rules endpoint handler.
GET /rules - Get active platform rules
POST /rules - Propose rule changes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.models.schemas import PlatformRules as PlatformRulesSchema, PlatformRulesCreate
from app.models.database import PlatformRule, RuleStatus
from app.core.database import get_db
from app.auth.permissions import require_role

router = APIRouter()


@router.get("/rules", response_model=List[PlatformRulesSchema])
async def get_rules(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get active platform rules.
    
    Args:
        db: Database session
        
    Returns:
        List of active PlatformRules
    """
    result = await db.execute(
        select(PlatformRule)
        .where(PlatformRule.status == RuleStatus.ACTIVE)
        .order_by(PlatformRule.created_at.desc())
    )
    rules = result.scalars().all()
    
    return [PlatformRulesSchema.model_validate(rule) for rule in rules]


@router.post("/rules", response_model=PlatformRulesSchema, status_code=202)
async def create_rule_proposal(
    rule_data: PlatformRulesCreate,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Propose rule changes (creates a candidate ruleset requiring approval).
    
    Args:
        rule_data: Platform rules data
        db: Database session
        
    Returns:
        Created PlatformRules object with candidate status
    """
    # Create rule proposal
    rule = PlatformRule(
        id=uuid4(),
        name=rule_data.name,
        rules=rule_data.rules,
        status=RuleStatus.CANDIDATE
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return PlatformRulesSchema.model_validate(rule)
