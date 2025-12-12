"""
Meta Ads Budget SPIKE Manager
Detecta picos de rendimiento/gasto y escala presupuestos automáticamente.
"""

from app.meta_budget_spike.models import (
    SpikeType,
    RiskLevel,
    SpikeDetectionResult,
    BudgetScaleRequest,
    BudgetScaleResponse,
    SpikeLogResponse,
    AutoRunResponse,
)
from app.meta_budget_spike.spike_detector import SpikeDetector
from app.meta_budget_spike.scaler import BudgetScaler
from app.meta_budget_spike.scheduler import spike_scheduler_task

__all__ = [
    "SpikeType",
    "RiskLevel",
    "SpikeDetectionResult",
    "BudgetScaleRequest",
    "BudgetScaleResponse",
    "SpikeLogResponse",
    "AutoRunResponse",
    "SpikeDetector",
    "BudgetScaler",
    "spike_scheduler_task",
]
