"""
Dashboard AI Schemas

Pydantic models for AI analysis, recommendations, and actions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class SystemAnalysis(BaseModel):
    """
    Complete system state analysis.
    
    Example:
        {
            "timestamp": "2025-11-22T10:30:00",
            "queue_health": "good",
            "orchestrator_health": "warning",
            "campaigns_status": "good",
            "publish_success_rate": 0.92,
            "pending_scheduled": 15,
            "best_clip_per_platform": {
                "instagram": {"clip_id": "uuid", "score": 0.95},
                "tiktok": {"clip_id": "uuid", "score": 0.88}
            },
            "issues_detected": [
                {
                    "severity": "warning",
                    "title": "High queue saturation",
                    "description": "Publishing queue is 85% saturated"
                }
            ],
            "metrics": {
                "total_clips_ready": 45,
                "avg_processing_time_ms": 2345.67,
                "platform_distribution": {
                    "instagram": 15,
                    "tiktok": 18,
                    "youtube": 8,
                    "facebook": 4
                }
            }
        }
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    queue_health: Literal["good", "warning", "critical"] = Field(description="Queue health status")
    orchestrator_health: Literal["good", "warning", "critical"] = Field(description="Orchestrator health status")
    campaigns_status: Literal["good", "warning", "critical"] = Field(description="Campaigns status")
    publish_success_rate: float = Field(ge=0.0, le=1.0, description="Overall success rate (0-1)")
    pending_scheduled: int = Field(ge=0, description="Number of pending scheduled publications")
    best_clip_per_platform: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Best clip for each platform")
    issues_detected: List[Dict[str, str]] = Field(default_factory=list, description="List of detected issues")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Additional metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-22T10:30:00",
                "queue_health": "good",
                "orchestrator_health": "warning",
                "campaigns_status": "good",
                "publish_success_rate": 0.92,
                "pending_scheduled": 15,
                "best_clip_per_platform": {
                    "instagram": {"clip_id": "550e8400-e29b-41d4-a716-446655440000", "score": 0.95},
                    "tiktok": {"clip_id": "550e8400-e29b-41d4-a716-446655440001", "score": 0.88}
                },
                "issues_detected": [
                    {
                        "severity": "warning",
                        "title": "High queue saturation",
                        "description": "Publishing queue is 85% saturated"
                    }
                ],
                "metrics": {
                    "total_clips_ready": 45,
                    "avg_processing_time_ms": 2345.67,
                    "platform_distribution": {
                        "instagram": 15,
                        "tiktok": 18,
                        "youtube": 8,
                        "facebook": 4
                    }
                }
            }
        }


class Recommendation(BaseModel):
    """
    AI-generated recommendation with actionable payload.
    
    Example:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Publish high-scoring clip to Instagram",
            "description": "Clip #1234 has a visual score of 0.95 and is optimal for Instagram",
            "severity": "info",
            "action": "publish",
            "payload": {
                "clip_id": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "instagram",
                "account_id": "550e8400-e29b-41d4-a716-446655440002"
            },
            "created_at": "2025-11-22T10:30:00"
        }
    """
    id: UUID = Field(default_factory=uuid4, description="Recommendation unique ID")
    title: str = Field(description="Recommendation title (short)")
    description: str = Field(description="Detailed recommendation description")
    severity: Literal["info", "warning", "critical"] = Field(description="Recommendation severity level")
    action: Literal[
        "publish",
        "reschedule",
        "promote",
        "retry",
        "run_orchestrator",
        "run_scheduler",
        "rebalance_queue",
        "publish_best_clip",
        "clear_failed",
        "optimize_schedule"
    ] = Field(description="Action type to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action-specific payload data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Recommendation creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Publish high-scoring clip to Instagram",
                "description": "Clip #1234 has a visual score of 0.95 and is optimal for Instagram",
                "severity": "info",
                "action": "publish",
                "payload": {
                    "clip_id": "550e8400-e29b-41d4-a716-446655440000",
                    "platform": "instagram",
                    "account_id": "550e8400-e29b-41d4-a716-446655440002"
                },
                "created_at": "2025-11-22T10:30:00"
            }
        }


class ExecuteActionRequest(BaseModel):
    """
    Request to execute an AI recommendation or manual action.
    
    Example:
        {
            "action": "publish",
            "payload": {
                "clip_id": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "instagram",
                "account_id": "550e8400-e29b-41d4-a716-446655440002"
            },
            "recommendation_id": "550e8400-e29b-41d4-a716-446655440001"
        }
    """
    action: str = Field(description="Action type to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action-specific payload")
    recommendation_id: Optional[UUID] = Field(None, description="Related recommendation ID (if applicable)")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "publish",
                "payload": {
                    "clip_id": "550e8400-e29b-41d4-a716-446655440000",
                    "platform": "instagram",
                    "account_id": "550e8400-e29b-41d4-a716-446655440002"
                },
                "recommendation_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class ExecuteActionResponse(BaseModel):
    """
    Response after executing an action.
    
    Example:
        {
            "success": true,
            "action": "publish",
            "message": "Clip published successfully to Instagram",
            "result": {
                "publish_log_id": "550e8400-e29b-41d4-a716-446655440003",
                "scheduled_for": "2025-11-22T14:00:00"
            },
            "executed_at": "2025-11-22T10:30:00"
        }
    """
    success: bool = Field(description="Whether action executed successfully")
    action: str = Field(description="Action type executed")
    message: str = Field(description="Human-readable result message")
    result: Dict[str, Any] = Field(default_factory=dict, description="Action execution result data")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "action": "publish",
                "message": "Clip published successfully to Instagram",
                "result": {
                    "publish_log_id": "550e8400-e29b-41d4-a716-446655440003",
                    "scheduled_for": "2025-11-22T14:00:00"
                },
                "executed_at": "2025-11-22T10:30:00"
            }
        }
