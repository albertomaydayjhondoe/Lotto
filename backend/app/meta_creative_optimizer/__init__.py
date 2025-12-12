"""
Meta Creative Optimizer (PASO 10.16)

Full integration layer that connects:
- Creative Analyzer (PASO 10.15)
- Targeting Optimizer (PASO 10.12)
- ROAS Engine (PASO 10.5)
- Spike Manager (PASO 10.9)
- Meta Orchestrator (PASO 10.3)
- Insights Collector (PASO 10.7)

Autonomous creative optimization with winner selection, role assignment,
recombination decisions, and budget scaling.
"""

from app.meta_creative_optimizer.models import (
    MetaCreativeDecisionModel,
    MetaCreativeWinnerLogModel,
    MetaCreativeOptimizationAuditModel,
)

__all__ = [
    "MetaCreativeDecisionModel",
    "MetaCreativeWinnerLogModel",
    "MetaCreativeOptimizationAuditModel",
]
