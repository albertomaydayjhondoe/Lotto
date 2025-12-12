"""
Dashboard Actions Schemas

Pydantic models for action execution requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ForcePublishRequest(BaseModel):
    """Request to force publish a clip."""
    clip_id: UUID = Field(description="Clip ID to publish")
    platform: Optional[str] = Field(None, description="Target platform (if specific)")
    account_id: Optional[UUID] = Field(None, description="Social account ID (if specific)")

    class Config:
        json_schema_extra = {
            "example": {
                "clip_id": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "instagram",
                "account_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class RescheduleRequest(BaseModel):
    """Request to reschedule a publication."""
    log_id: UUID = Field(description="Publish log ID")
    new_time: datetime = Field(description="New scheduled time")

    class Config:
        json_schema_extra = {
            "example": {
                "log_id": "550e8400-e29b-41d4-a716-446655440000",
                "new_time": "2025-11-22T14:00:00"
            }
        }


class RunSchedulerRequest(BaseModel):
    """Request to run scheduler tick."""
    dry_run: bool = Field(False, description="If true, only simulate without executing")

    class Config:
        json_schema_extra = {
            "example": {
                "dry_run": False
            }
        }


class PromoteClipRequest(BaseModel):
    """Request to promote clip to campaign."""
    video_id: UUID = Field(description="Video ID")
    campaign_id: Optional[UUID] = Field(None, description="Target campaign ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "550e8400-e29b-41d4-a716-446655440000",
                "campaign_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class PublishBestClipRequest(BaseModel):
    """Request to publish best available clip."""
    video_id: UUID = Field(description="Video ID")
    platform: Optional[str] = Field(None, description="Target platform (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "instagram"
            }
        }


class ClearFailedRequest(BaseModel):
    """Request to clear failed publications."""
    older_than_days: int = Field(7, description="Clear items older than N days")

    class Config:
        json_schema_extra = {
            "example": {
                "older_than_days": 7
            }
        }


class ActionResult(BaseModel):
    """Generic action execution result."""
    success: bool = Field(description="Whether action succeeded")
    message: str = Field(description="Result message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Result data")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Action completed successfully",
                "data": {"items_processed": 5},
                "executed_at": "2025-11-22T10:30:00"
            }
        }
