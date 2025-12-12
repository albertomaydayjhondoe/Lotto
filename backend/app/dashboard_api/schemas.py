"""
Dashboard API Schemas

Pydantic models for all dashboard API responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    """
    Global statistics overview.
    
    Example:
        {
            "total_videos": 150,
            "total_clips": 320,
            "total_jobs": 89,
            "total_campaigns": 12,
            "pending_jobs": 5,
            "processing_jobs": 2,
            "failed_jobs": 8,
            "success_logs": 245,
            "failed_logs": 23,
            "scheduled_publications": 42
        }
    """
    total_videos: int = Field(description="Total number of videos in system")
    total_clips: int = Field(description="Total number of clips generated")
    total_jobs: int = Field(description="Total number of jobs created")
    total_campaigns: int = Field(description="Total number of campaigns")
    pending_jobs: int = Field(description="Jobs with status 'pending'")
    processing_jobs: int = Field(description="Jobs with status 'processing'")
    failed_jobs: int = Field(description="Jobs with status 'failed'")
    success_logs: int = Field(description="Successful publication logs")
    failed_logs: int = Field(description="Failed publication logs")
    scheduled_publications: int = Field(description="Publications in queue with status 'pending'")

    class Config:
        json_schema_extra = {
            "example": {
                "total_videos": 150,
                "total_clips": 320,
                "total_jobs": 89,
                "total_campaigns": 12,
                "pending_jobs": 5,
                "processing_jobs": 2,
                "failed_jobs": 8,
                "success_logs": 245,
                "failed_logs": 23,
                "scheduled_publications": 42
            }
        }


class QueueStats(BaseModel):
    """
    Publication queue aggregated statistics.
    
    Example:
        {
            "pending": 15,
            "processing": 3,
            "success": 189,
            "failed": 12,
            "avg_processing_time_ms": 2345.67,
            "oldest_pending_age_seconds": 3600.0
        }
    """
    pending: int = Field(description="Queue items with status 'pending'")
    processing: int = Field(description="Queue items with status 'processing'")
    success: int = Field(description="Queue items with status 'success'")
    failed: int = Field(description="Queue items with status 'failed'")
    avg_processing_time_ms: Optional[float] = Field(None, description="Average processing time in milliseconds")
    oldest_pending_age_seconds: Optional[float] = Field(None, description="Age of oldest pending item in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "pending": 15,
                "processing": 3,
                "success": 189,
                "failed": 12,
                "avg_processing_time_ms": 2345.67,
                "oldest_pending_age_seconds": 3600.0
            }
        }


class OrchestratorStats(BaseModel):
    """
    Orchestrator activity and performance metrics.
    
    Example:
        {
            "last_run_at": "2025-11-22T10:30:00",
            "actions_last_run": 5,
            "actions_last_24h": 87,
            "queue_saturation": 0.35,
            "active_workers": 4
        }
    """
    last_run_at: Optional[datetime] = Field(None, description="Last orchestrator execution timestamp")
    actions_last_run: int = Field(description="Actions taken in last run")
    actions_last_24h: int = Field(description="Actions taken in last 24 hours")
    queue_saturation: float = Field(description="Queue saturation ratio (0.0 - 1.0)")
    active_workers: int = Field(description="Number of active workers")

    class Config:
        json_schema_extra = {
            "example": {
                "last_run_at": "2025-11-22T10:30:00",
                "actions_last_run": 5,
                "actions_last_24h": 87,
                "queue_saturation": 0.35,
                "active_workers": 4
            }
        }


class PlatformBreakdown(BaseModel):
    """
    Statistics for a single platform.
    
    Example:
        {
            "clips_ready": 45,
            "clips_published": 123,
            "avg_score": 0.78,
            "jobs_completed": 89,
            "jobs_failed": 5
        }
    """
    clips_ready: int = Field(description="Clips ready for publication (status='ready')")
    clips_published: int = Field(description="Clips already published")
    avg_score: float = Field(description="Average quality score (0.0 - 1.0)")
    jobs_completed: int = Field(description="Completed jobs for this platform")
    jobs_failed: int = Field(description="Failed jobs for this platform")

    class Config:
        json_schema_extra = {
            "example": {
                "clips_ready": 45,
                "clips_published": 123,
                "avg_score": 0.78,
                "jobs_completed": 89,
                "jobs_failed": 5
            }
        }


class PlatformStats(BaseModel):
    """
    Aggregated statistics by platform.
    
    Example:
        {
            "instagram": {...},
            "tiktok": {...},
            "youtube": {...},
            "other": {...}
        }
    """
    instagram: PlatformBreakdown
    tiktok: PlatformBreakdown
    youtube: PlatformBreakdown
    other: PlatformBreakdown

    class Config:
        json_schema_extra = {
            "example": {
                "instagram": {
                    "clips_ready": 45,
                    "clips_published": 123,
                    "avg_score": 0.78,
                    "jobs_completed": 89,
                    "jobs_failed": 5
                },
                "tiktok": {
                    "clips_ready": 32,
                    "clips_published": 98,
                    "avg_score": 0.82,
                    "jobs_completed": 67,
                    "jobs_failed": 3
                },
                "youtube": {
                    "clips_ready": 18,
                    "clips_published": 56,
                    "avg_score": 0.85,
                    "jobs_completed": 45,
                    "jobs_failed": 2
                },
                "other": {
                    "clips_ready": 5,
                    "clips_published": 12,
                    "avg_score": 0.70,
                    "jobs_completed": 8,
                    "jobs_failed": 1
                }
            }
        }


class CampaignStats(BaseModel):
    """
    Campaign status aggregations.
    
    Example:
        {
            "draft": 3,
            "active": 8,
            "paused": 2,
            "completed": 15,
            "total_budget_spent": 0.0
        }
    """
    draft: int = Field(description="Campaigns with status='draft'")
    active: int = Field(description="Campaigns with status='active'")
    paused: int = Field(description="Campaigns with status='paused'")
    completed: int = Field(description="Campaigns with status='completed'")
    total_budget_spent: float = Field(description="Total budget spent across all campaigns")

    class Config:
        json_schema_extra = {
            "example": {
                "draft": 3,
                "active": 8,
                "paused": 2,
                "completed": 15,
                "total_budget_spent": 0.0
            }
        }
