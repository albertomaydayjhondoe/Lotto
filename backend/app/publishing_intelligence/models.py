from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class PriorityCalculation(BaseModel):
    """Result of priority calculation"""
    clip_id: str
    priority: float = Field(..., description="Calculated priority score (0-100)")
    visual_score: float = Field(default=0.0)
    engagement_score: float = Field(default=0.0)
    predicted_virality: float = Field(default=0.0)
    campaign_weight: float = Field(default=0.0)
    delay_penalty: float = Field(default=0.0)
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Detailed breakdown of priority calculation")


class PlatformForecast(BaseModel):
    """Forecast for a single platform"""
    platform: str
    next_slot: Optional[datetime] = Field(None, description="Next available slot (UTC)")
    slots_remaining_today: int = Field(..., description="Number of slots left today")
    risk: str = Field(..., description="Saturation risk: low, medium, high")
    scheduled_count: int = Field(default=0, description="Number of already scheduled publications")
    window_start_hour: int
    window_end_hour: int
    min_gap_minutes: int


class GlobalForecast(BaseModel):
    """Global forecast for all platforms"""
    forecast_date: datetime
    instagram: PlatformForecast
    tiktok: PlatformForecast
    youtube: PlatformForecast


class AutoScheduleRequest(BaseModel):
    """Request to auto-schedule a clip"""
    clip_id: str = Field(..., description="ID of the clip to schedule")
    platform: str = Field(..., description="Platform: instagram, tiktok, youtube")
    social_account_id: Optional[str] = Field(None, description="Optional social account ID")
    force_slot: Optional[datetime] = Field(None, description="Force specific slot (overrides intelligence)")


class ConflictInfo(BaseModel):
    """Information about scheduling conflicts"""
    detected: bool = Field(default=False)
    conflicting_log_id: Optional[str] = None
    resolution: Optional[str] = None
    original_slot: Optional[datetime] = None
    shifted_slot: Optional[datetime] = None


class AutoScheduleResponse(BaseModel):
    """Response from auto-scheduling"""
    publish_log_id: str
    clip_id: str
    platform: str
    scheduled_for: datetime
    priority: float
    conflict_info: ConflictInfo
    reason: Optional[str] = None


class PriorityRequest(BaseModel):
    """Request to calculate priority for a clip"""
    clip_id: str
    platform: Optional[str] = None
