"""
Live Telemetry Models

Pydantic schemas for real-time telemetry payloads.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class QueueStats(BaseModel):
    """Queue statistics snapshot."""
    pending: int = Field(ge=0, description="Pending publications")
    processing: int = Field(ge=0, description="Processing publications")
    success: int = Field(ge=0, description="Successful publications")
    failed: int = Field(ge=0, description="Failed publications")
    total: int = Field(ge=0, description="Total items in queue")


class SchedulerStats(BaseModel):
    """Scheduler statistics snapshot."""
    scheduled_today: int = Field(ge=0, description="Publications scheduled for today")
    scheduled_next_hour: int = Field(ge=0, description="Publications in next hour")
    overdue: int = Field(ge=0, description="Overdue publications")
    avg_delay_seconds: Optional[float] = Field(None, description="Average delay in seconds")


class OrchestratorStats(BaseModel):
    """Orchestrator statistics snapshot."""
    actions_last_minute: int = Field(ge=0, description="Actions executed in last minute")
    decisions_pending: int = Field(ge=0, description="Pending decisions")
    saturation_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Saturation rate 0-1")
    last_run_seconds_ago: Optional[int] = Field(None, description="Seconds since last run")


class PlatformStats(BaseModel):
    """Platform statistics snapshot."""
    instagram: int = Field(ge=0, description="Clips ready for Instagram")
    tiktok: int = Field(ge=0, description="Clips ready for TikTok")
    youtube: int = Field(ge=0, description="Clips ready for YouTube")
    facebook: int = Field(ge=0, description="Clips ready for Facebook")


class WorkerStats(BaseModel):
    """Worker statistics snapshot."""
    active_workers: int = Field(ge=0, description="Number of active workers")
    tasks_processing: int = Field(ge=0, description="Tasks currently processing")
    avg_processing_time_ms: Optional[float] = Field(None, description="Average processing time in ms")


class TelemetryPayload(BaseModel):
    """
    Complete telemetry payload sent via WebSocket.
    
    Example:
        {
            "queue": {
                "pending": 15,
                "processing": 3,
                "success": 189,
                "failed": 12,
                "total": 219
            },
            "scheduler": {
                "scheduled_today": 45,
                "scheduled_next_hour": 8,
                "overdue": 2,
                "avg_delay_seconds": 120.5
            },
            "orchestrator": {
                "actions_last_minute": 5,
                "decisions_pending": 12,
                "saturation_rate": 0.65,
                "last_run_seconds_ago": 30
            },
            "platforms": {
                "instagram": 25,
                "tiktok": 30,
                "youtube": 15,
                "facebook": 8
            },
            "workers": {
                "active_workers": 4,
                "tasks_processing": 7,
                "avg_processing_time_ms": 2145.5
            },
            "timestamp": "2025-11-22T10:30:00.123456"
        }
    """
    queue: QueueStats = Field(description="Queue statistics")
    scheduler: SchedulerStats = Field(description="Scheduler statistics")
    orchestrator: OrchestratorStats = Field(description="Orchestrator statistics")
    platforms: PlatformStats = Field(description="Platform statistics")
    workers: WorkerStats = Field(description="Worker statistics")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of metrics collection")

    class Config:
        json_schema_extra = {
            "example": {
                "queue": {
                    "pending": 15,
                    "processing": 3,
                    "success": 189,
                    "failed": 12,
                    "total": 219
                },
                "scheduler": {
                    "scheduled_today": 45,
                    "scheduled_next_hour": 8,
                    "overdue": 2,
                    "avg_delay_seconds": 120.5
                },
                "orchestrator": {
                    "actions_last_minute": 5,
                    "decisions_pending": 12,
                    "saturation_rate": 0.65,
                    "last_run_seconds_ago": 30
                },
                "platforms": {
                    "instagram": 25,
                    "tiktok": 30,
                    "youtube": 15,
                    "facebook": 8
                },
                "workers": {
                    "active_workers": 4,
                    "tasks_processing": 7,
                    "avg_processing_time_ms": 2145.5
                },
                "timestamp": "2025-11-22T10:30:00.123456"
            }
        }
