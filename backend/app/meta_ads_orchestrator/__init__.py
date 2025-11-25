"""
Meta Ads Orchestration Layer

This module provides high-level orchestration for Meta Ads campaigns,
managing the full lifecycle from campaign creation to insights collection.
"""

from .orchestrator import MetaAdsOrchestrator
from .models import (
    OrchestrationRequest,
    OrchestrationResult,
    CampaignCreationResult,
    InsightsSyncResult,
)

__all__ = [
    "MetaAdsOrchestrator",
    "OrchestrationRequest",
    "OrchestrationResult",
    "CampaignCreationResult",
    "InsightsSyncResult",
]
