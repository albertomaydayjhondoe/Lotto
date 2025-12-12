"""
Alerting Engine

Sistema de alertas en tiempo real para el Dashboard del Orquestador.
"""

from .router import router
from .websocket import alert_manager

__all__ = ["router", "alert_manager"]
