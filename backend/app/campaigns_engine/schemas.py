"""Pydantic schemas for campaigns orchestrator module."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ClipScore(BaseModel):
    """Score of a clip for a specific platform."""
    
    clip_id: UUID
    platform: Literal["tiktok", "instagram", "youtube"]
    score: float = Field(ge=0.0, le=1.0, description="Score between 0 and 1")


class BestClipDecision(BaseModel):
    """Decision record for the best clip selected for a platform."""
    
    video_asset_id: UUID
    platform: Literal["tiktok", "instagram", "youtube"]
    clip_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    decided_at: datetime


class OrchestrateCampaignRequest(BaseModel):
    """Request to orchestrate campaigns for a video asset."""
    
    video_asset_id: UUID
    platforms: list[Literal["tiktok", "instagram", "youtube"]] = Field(
        default=["instagram"],
        description="Platforms to orchestrate campaigns for"
    )


class OrchestrateCampaignResponse(BaseModel):
    """Response from campaign orchestration."""
    
    decisions: list[BestClipDecision]
    campaigns_created: list[str] = Field(
        description="Campaign IDs created as strings"
    )
