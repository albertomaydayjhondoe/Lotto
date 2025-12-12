"""
Satellite Engine Package
Sistema de publicación multi-plataforma con scheduling y metrics.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
Version: 1.0.0
"""

from app.satellites.config import SatelliteConfig
from app.satellites.models import (
    UploadRequest,
    UploadResponse,
    PlatformMetrics,
    SatelliteAccount,
    ScheduledPost,
    MetricsSnapshot,
)
from app.satellites.scheduler import UploadScheduler
from app.satellites.metrics_collector import MetricsCollector
from app.satellites.account_management import AccountManager

# Platform clients
from app.satellites.platforms import (
    BasePlatformClient,
    TikTokClient,
    InstagramClient,
    YouTubeClient,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "SatelliteConfig",
    
    # Models
    "UploadRequest",
    "UploadResponse",
    "PlatformMetrics",
    "SatelliteAccount",
    "ScheduledPost",
    "MetricsSnapshot",
    
    # Core components
    "UploadScheduler",
    "MetricsCollector",
    "AccountManager",
    
    # Platform clients
    "BasePlatformClient",
    "TikTokClient",
    "InstagramClient",
    "YouTubeClient",
]
