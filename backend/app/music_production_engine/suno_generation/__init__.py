"""Suno Generation Module

Mock implementation of Suno API for music generation.
Provides realistic stub behavior for testing and development.
"""

from .generator_stub import SunoGeneratorStub, GenerationParams
from .refine_stub import SunoRefineStub, RefineParams
from .cycle_manager import GenerationCycleManager, CycleStatus

__all__ = [
    "SunoGeneratorStub",
    "GenerationParams",
    "SunoRefineStub",
    "RefineParams",
    "GenerationCycleManager",
    "CycleStatus",
]


def get_suno_status() -> dict:
    """Get status of Suno generation module."""
    return {
        "module": "suno_generation",
        "status": "STUB",
        "api_mode": "mock",
        "features": [
            "text-to-music generation",
            "iterative refinement",
            "cycle management",
            "quality scoring"
        ],
        "note": "Using mock Suno API - no real generation or billing"
    }
