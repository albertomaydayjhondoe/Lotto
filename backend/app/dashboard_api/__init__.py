"""
Dashboard API Module

Internal API layer for administrative panel backend.
Provides aggregated statistics and metrics endpoints.

This module does NOT include frontend/UI (that's PASO 6.2).
"""

from .router import router as dashboard_router
from .schemas import (
    OverviewStats,
    QueueStats,
    OrchestratorStats,
    PlatformStats,
    PlatformBreakdown,
    CampaignStats
)

__all__ = [
    "dashboard_router",
    "OverviewStats",
    "QueueStats",
    "OrchestratorStats",
    "PlatformStats",
    "PlatformBreakdown",
    "CampaignStats"
]
