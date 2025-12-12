"""
Meta Ads Orchestration Layer

This module provides high-level orchestration for Meta Ads campaigns,
managing the full lifecycle from campaign creation to insights collection,
including A/B testing and winner publishing.
"""

from .orchestrator import MetaAdsOrchestrator
from .models import (
    OrchestrationRequest,
    OrchestrationResult,
    CampaignCreationResult,
    InsightsSyncResult,
)
from .ab_test import (
    create_ab_test,
    evaluate_ab_test,
    archive_ab_test,
    publish_winner,
    ABTestEvaluator,
)

__all__ = [
    # Orchestrator
    "MetaAdsOrchestrator",
    # Models
    "OrchestrationRequest",
    "OrchestrationResult",
    "CampaignCreationResult",
    "InsightsSyncResult",
    # A/B Testing
    "create_ab_test",
    "evaluate_ab_test",
    "archive_ab_test",
    "publish_winner",
    "ABTestEvaluator",
]
