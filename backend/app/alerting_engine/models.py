"""
Alerting Engine Models

Defines alert types, severities, and data structures.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts that can be generated."""
    QUEUE_SATURATION = "queue_saturation"
    SCHEDULER_BACKLOG = "scheduler_backlog"
    ORCHESTRATOR_INACTIVE = "orchestrator_inactive"
    PUBLISH_FAILURES_SPIKE = "publish_failures_spike"
    OAUTH_EXPIRING_SOON = "oauth_expiring_soon"
    WORKER_CRASH_DETECTED = "worker_crash_detected"
    CAMPAIGN_BLOCKED = "campaign_blocked"
    SYSTEM_HEALTH_DEGRADED = "system_health_degraded"


class Alert(BaseModel):
    """Alert data structure."""
    id: UUID = Field(default_factory=uuid4)
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "alert_type": "queue_saturation",
                "severity": "critical",
                "message": "Queue is critically saturated with 75 pending items",
                "metadata": {
                    "pending_count": 75,
                    "threshold": 50,
                    "queue_total": 100
                },
                "created_at": "2025-11-22T10:30:00Z",
                "read": False
            }
        }


class AlertCreate(BaseModel):
    """Schema for creating alerts."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertResponse(Alert):
    """Alert response with all fields."""
    pass


class AlertsListResponse(BaseModel):
    """Response for listing alerts."""
    alerts: list[AlertResponse]
    total: int
    unread_count: int
