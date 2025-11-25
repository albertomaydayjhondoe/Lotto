"""
Meta Optimization Loop Module

Automated optimization system that reads ROAS/pixel outcomes and produces
optimization actions (scale up/down, pause, reallocate budget).

Supports two modes:
- suggest: Creates optimization actions for manual review (default)
- auto: Executes safe actions automatically with guard rails

Components:
- OptimizationRunner: Background worker that runs optimization loop
- OptimizationService: Business logic for evaluation and action execution
- router: FastAPI endpoints for manual control and monitoring
"""

from .runner import OptimizationRunner
from .service import OptimizationService
from .routes import router

__all__ = ["OptimizationRunner", "OptimizationService", "router"]
