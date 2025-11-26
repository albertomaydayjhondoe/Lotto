"""
Meta Autonomous System Layer (PASO 10.7)

Unified autonomous control layer that orchestrates:
- ROAS Engine (PASO 10.5)
- Optimization Loop (PASO 10.6)
- Meta Ads Orchestrator (PASO 10.3)
- Policy Engine (business rules)
- Safety Engine (guardrails)

Operates in two modes:
- suggest: Generate recommendations for human approval
- auto: Execute approved actions automatically
"""

from .policy_engine import PolicyEngine
from .safety import SafetyEngine
from .auto_worker import MetaAutoWorker
from .routes import router

__all__ = ["PolicyEngine", "SafetyEngine", "MetaAutoWorker", "router"]
