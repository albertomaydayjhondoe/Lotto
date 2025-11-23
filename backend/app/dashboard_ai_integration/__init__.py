"""
Dashboard AI Integration Module.

Provides dashboard-specific endpoints for AI Global Worker integration.
Part of PASO 8.0 implementation.
"""

from app.dashboard_ai_integration.router import router as dashboard_ai_integration_router

__all__ = ["dashboard_ai_integration_router"]
