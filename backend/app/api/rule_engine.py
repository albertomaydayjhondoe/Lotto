"""
API endpoints for the Rule Engine.
"""
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.rules_engine import RuleEngine
from app.rules_engine.models import AdaptiveRuleSet
from app.auth.permissions import require_role


router = APIRouter()


# Request/Response models
class EvaluateClipRequest(BaseModel):
    """Request to evaluate a clip."""
    clip_id: UUID
    platform: Literal["tiktok", "instagram", "youtube"]


class EvaluateClipResponse(BaseModel):
    """Response from clip evaluation."""
    clip_id: UUID
    platform: str
    score: float


class TrainRulesRequest(BaseModel):
    """Request to train rules."""
    platform: Literal["tiktok", "instagram", "youtube"]


class RuleWeightsResponse(BaseModel):
    """Response with rule weights."""
    platform: str
    weights: dict[str, float]
    updated_at: str


@router.get("/engine/weights", response_model=RuleWeightsResponse)
async def get_rule_weights(
    platform: Literal["tiktok", "instagram", "youtube"],
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Get current rule weights for a platform.
    
    Args:
        platform: Target platform (tiktok|instagram|youtube)
        db: Database session
        
    Returns:
        Current weights and update timestamp
    """
    engine = RuleEngine()
    
    try:
        rules = await engine.get_rules(db, platform)
        
        return RuleWeightsResponse(
            platform=rules.platform,
            weights=rules.weights,
            updated_at=rules.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load rules: {str(e)}"
        )


@router.post("/engine/evaluate", response_model=EvaluateClipResponse)
async def evaluate_clip(
    request: EvaluateClipRequest,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager"))
):
    """
    Evaluate a clip for a specific platform.
    
    Args:
        request: Evaluation request with clip_id and platform
        db: Database session
        
    Returns:
        Clip score between 0.0 and 1.0
    """
    engine = RuleEngine()
    
    try:
        score = await engine.evaluate_clip(
            db,
            request.clip_id,
            request.platform
        )
        
        return EvaluateClipResponse(
            clip_id=request.clip_id,
            platform=request.platform,
            score=score
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/engine/train", response_model=RuleWeightsResponse)
async def train_rules(
    request: TrainRulesRequest,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin"))
):
    """
    Train rule weights based on performance data.
    
    Analyzes ledger events to identify successful clips and
    updates weights accordingly.
    
    Args:
        request: Training request with platform
        db: Database session
        
    Returns:
        Updated weights
    """
    engine = RuleEngine()
    
    try:
        rules = await engine.train(db, request.platform)
        
        return RuleWeightsResponse(
            platform=rules.platform,
            weights=rules.weights,
            updated_at=rules.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}"
        )
