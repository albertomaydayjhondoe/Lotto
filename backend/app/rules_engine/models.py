"""
Data models for the Rule Engine.
"""
from typing import Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class RuleWeight(BaseModel):
    """Individual feature weight."""
    name: str
    weight: float = Field(ge=0.0, le=1.0)


class AdaptiveRuleSet(BaseModel):
    """Complete weight set for a platform."""
    platform: Literal["tiktok", "instagram", "youtube"]
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "visual_score": 0.5,
            "duration_ms": 0.2,
            "cut_position": 0.2,
            "motion_intensity": 0.1
        }
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Default weights for each platform (before any training)
DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "tiktok": {
        "visual_score": 0.5,
        "duration_ms": 0.2,
        "cut_position": 0.2,
        "motion_intensity": 0.1
    },
    "instagram": {
        "visual_score": 0.5,
        "duration_ms": 0.2,
        "cut_position": 0.2,
        "motion_intensity": 0.1
    },
    "youtube": {
        "visual_score": 0.5,
        "duration_ms": 0.2,
        "cut_position": 0.2,
        "motion_intensity": 0.1
    }
}
