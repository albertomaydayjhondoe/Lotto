"""
AI Global Worker Module

Autonomous AI worker that:
- Collects comprehensive system state
- Generates AI-powered summaries and insights
- Creates prioritized recommendations
- Proposes action plans
- Runs continuously in background

This module integrates LLM reasoning with system observability.
"""

from .router import router as ai_global_router
from .runner import start_ai_worker_loop, stop_ai_worker_loop, get_last_reasoning

__all__ = [
    "ai_global_router",
    "start_ai_worker_loop",
    "stop_ai_worker_loop",
    "get_last_reasoning",
]
