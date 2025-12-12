"""
Dashboard Actions Module

Action execution layer for dashboard operations.
"""

from .router import router
from .executor import execute_action

__all__ = ["router", "execute_action"]
