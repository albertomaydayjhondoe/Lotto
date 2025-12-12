"""
Meta Real-Time Performance Engine (PASO 10.14)

Motor de detección y respuesta en tiempo real para campañas Meta Ads.
Detecta anomalías, drops y spikes cada 5-15 minutos y dispara acciones automáticas.
"""

from app.meta_rt_engine.detector import RealTimeDetector
from app.meta_rt_engine.decision_engine import RealTimeDecisionEngine
from app.meta_rt_engine.actions import RealTimeActionsLayer
from app.meta_rt_engine.models import (
    MetaRealTimeLogModel,
    MetaPerformanceSnapshotModel,
)
from app.meta_rt_engine.schemas import (
    # Snapshot schemas
    PerformanceSnapshot,
    PerformanceSnapshotCreate,
    PerformanceSnapshotResponse,
    
    # Detection schemas
    AnomalyDetection,
    DriftDetection,
    SpikeDetection,
    DetectionResult,
    
    # Decision schemas
    RealTimeDecision,
    DecisionRule,
    DecisionResponse,
    
    # Action schemas
    ActionRequest,
    ActionResponse,
    ActionType,
    
    # Log schemas
    RTLogEntry,
    RTLogResponse,
    
    # API schemas
    RTRunRequest,
    RTRunResponse,
    RTHealthResponse,
)

__all__ = [
    # Core components
    "RealTimeDetector",
    "RealTimeDecisionEngine",
    "RealTimeActionsLayer",
    
    # Models
    "MetaRealTimeLogModel",
    "MetaPerformanceSnapshotModel",
    
    # Snapshot schemas
    "PerformanceSnapshot",
    "PerformanceSnapshotCreate",
    "PerformanceSnapshotResponse",
    
    # Detection schemas
    "AnomalyDetection",
    "DriftDetection",
    "SpikeDetection",
    "DetectionResult",
    
    # Decision schemas
    "RealTimeDecision",
    "DecisionRule",
    "DecisionResponse",
    
    # Action schemas
    "ActionRequest",
    "ActionResponse",
    "ActionType",
    
    # Log schemas
    "RTLogEntry",
    "RTLogResponse",
    
    # API schemas
    "RTRunRequest",
    "RTRunResponse",
    "RTHealthResponse",
]
