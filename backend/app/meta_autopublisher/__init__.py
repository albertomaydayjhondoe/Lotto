"""
Meta Campaigns Auto-Pilot (AutoPublisher) - PASO 10.8

Automatiza la creación, testeo A/B, selección de ganador, escalado de presupuesto
y publicación final de campañas en Meta (Instagram/Facebook).

Integra:
- PASO 10.1: Meta Models
- PASO 10.2: MetaAdsClient
- PASO 10.3: Orchestrator
- PASO 10.4/10.5: A/B Testing + ROAS Engine
- PASO 10.7: Meta Insights Collector
- Publishing Queue + Worker + Ledger + RBAC
"""

from .orchestrator import AutoPublisherOrchestrator
from .models import (
    AutoPublisherRunRequest,
    AutoPublisherRunResponse,
    ABTestConfig,
    WinnerSelection,
    RunStatus
)

__all__ = [
    "AutoPublisherOrchestrator",
    "AutoPublisherRunRequest",
    "AutoPublisherRunResponse",
    "ABTestConfig",
    "WinnerSelection",
    "RunStatus"
]
