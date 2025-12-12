from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    """Request to schedule a publication"""
    clip_id: str = Field(..., description="ID of the clip to publish")
    platform: str = Field(..., description="Platform: instagram, tiktok, youtube")
    social_account_id: str = Field(..., description="ID of the social account")
    scheduled_for: datetime = Field(..., description="Desired publication time (UTC)")
    scheduled_window_end: Optional[datetime] = Field(None, description="Optional end of time window")
    scheduled_by: str = Field(default="manual", description="Who scheduled: manual, rule_engine, campaign_orchestrator")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "clip_id": "clip_123",
                "platform": "instagram",
                "social_account_id": "acc_456",
                "scheduled_for": "2024-01-15T20:00:00Z",
                "scheduled_window_end": "2024-01-15T22:00:00Z",
                "scheduled_by": "manual"
            }]
        }
    }


class ScheduleResponse(BaseModel):
    """Response from scheduling a publication"""
    publish_log_id: str = Field(..., description="ID of the created publish log")
    status: str = Field(..., description="scheduled or rejected")
    reason: Optional[str] = Field(None, description="Reason if rejected or adjusted")
    scheduled_for: Optional[datetime] = Field(None, description="Final scheduled time (may be adjusted)")
    scheduled_window_end: Optional[datetime] = Field(None, description="Final window end")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "publish_log_id": "log_789",
                "status": "scheduled",
                "reason": "Adjusted 5min forward to respect 60min gap",
                "scheduled_for": "2024-01-15T20:05:00Z",
                "scheduled_window_end": "2024-01-15T22:00:00Z"
            }]
        }
    }


class PublishLogScheduledInfo(BaseModel):
    """Info about a scheduled publish log"""
    id: str
    clip_id: str
    platform: str
    social_account_id: str
    status: str
    schedule_type: str
    scheduled_for: Optional[datetime]
    scheduled_window_end: Optional[datetime]
    scheduled_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchedulerTickResponse(BaseModel):
    """Response from scheduler tick"""
    moved: int = Field(..., description="Number of logs moved to pending")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    log_ids: List[str] = Field(default_factory=list, description="IDs of moved logs")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "moved": 3,
                "dry_run": False,
                "log_ids": ["log_1", "log_2", "log_3"]
            }]
        }
    }
