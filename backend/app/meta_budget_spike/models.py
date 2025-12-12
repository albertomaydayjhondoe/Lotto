"""
Modelos de datos para Meta Budget SPIKE Manager.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


# ==================== SQLAlchemy Model ====================


class MetaBudgetSpikeLogModel(Base):
    """
    Registro histórico de spikes detectados y escalados aplicados.
    """

    __tablename__ = "meta_budget_spike_log"

    id = Column(Integer, primary_key=True, index=True)
    adset_id = Column(String(128), nullable=False, index=True)
    adset_name = Column(String(255), nullable=True)
    campaign_id = Column(String(128), nullable=True, index=True)
    
    old_daily_budget = Column(Float, nullable=False)
    new_daily_budget = Column(Float, nullable=False)
    
    spike_type = Column(String(32), nullable=False)  # positive, negative, risk
    risk_level = Column(String(16), nullable=False)  # low, medium, high
    
    reason = Column(Text, nullable=True)
    metrics_snapshot = Column(JSON, nullable=True)
    
    risk_score = Column(Float, nullable=True)  # 0-100
    stability_score = Column(Float, nullable=True)  # 0-100
    
    applied = Column(String(16), nullable=False, default="pending")  # pending, applied, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    applied_at = Column(DateTime, nullable=True)


# ==================== Enums ====================


class SpikeType(str, Enum):
    """Tipo de spike detectado."""
    POSITIVE = "positive"  # Métricas mejorando → escalar up
    NEGATIVE = "negative"  # Métricas empeorando → escalar down o pausar
    RISK = "risk"  # Gasto alto pero métricas malas → pausar


class RiskLevel(str, Enum):
    """Nivel de riesgo."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScaleAction(str, Enum):
    """Acción de escalado."""
    SCALE_UP_10 = "scale_up_10"
    SCALE_UP_20 = "scale_up_20"
    SCALE_UP_30 = "scale_up_30"
    SCALE_UP_50 = "scale_up_50"
    MAINTAIN = "maintain"
    SCALE_DOWN_10 = "scale_down_10"
    SCALE_DOWN_20 = "scale_down_20"
    SCALE_DOWN_40 = "scale_down_40"
    PAUSE = "pause"


# ==================== Pydantic Schemas ====================


class MetricsSnapshot(BaseModel):
    """Snapshot de métricas en el momento del spike."""
    cpm: float | None = None
    cpc: float | None = None
    ctr: float | None = None
    roas: float | None = None
    conversion_rate: float | None = None
    frequency: float | None = None
    spend_rate: float | None = None
    impressions: int | None = None
    clicks: int | None = None
    conversions: int | None = None
    spend: float | None = None
    revenue: float | None = None


class SpikeDetectionResult(BaseModel):
    """Resultado de detección de spike."""
    adset_id: str
    adset_name: str | None = None
    campaign_id: str | None = None
    
    spike_detected: bool
    spike_type: SpikeType | None = None
    risk_level: RiskLevel
    
    current_metrics: MetricsSnapshot
    historical_avg: MetricsSnapshot | None = None
    
    z_scores: dict[str, float] = Field(default_factory=dict)
    percentiles: dict[str, float] = Field(default_factory=dict)
    
    risk_score: float = Field(ge=0, le=100)
    stability_score: float = Field(ge=0, le=100)
    
    reason: str
    recommended_action: ScaleAction


class BudgetScaleRequest(BaseModel):
    """Request para escalar presupuesto de un adset."""
    adset_id: str
    action: ScaleAction
    reason: str | None = None
    force: bool = False  # Si true, ignora checks de seguridad


class BudgetScaleResponse(BaseModel):
    """Response de escalado de presupuesto."""
    adset_id: str
    old_budget: float
    new_budget: float
    action_applied: ScaleAction
    success: bool
    message: str
    spike_log_id: int | None = None


class SpikeLogResponse(BaseModel):
    """Response con detalles de un log de spike."""
    id: int
    adset_id: str
    adset_name: str | None
    campaign_id: str | None
    
    old_daily_budget: float
    new_daily_budget: float
    
    spike_type: str
    risk_level: str
    
    reason: str | None
    metrics_snapshot: dict[str, Any] | None
    
    risk_score: float | None
    stability_score: float | None
    
    applied: str
    error_message: str | None
    
    created_at: datetime
    applied_at: datetime | None

    class Config:
        from_attributes = True


class AutoRunRequest(BaseModel):
    """Request para ejecución automática completa."""
    campaign_ids: list[str] | None = None  # Si None, analiza todas
    dry_run: bool = False  # Si true, solo detecta pero no aplica
    min_spend_threshold: float = 50.0  # Mínimo gasto diario para analizar


class AutoRunResponse(BaseModel):
    """Response de ejecución automática."""
    total_adsets_analyzed: int
    spikes_detected: int
    scales_applied: int
    scales_failed: int
    dry_run: bool
    
    spike_results: list[SpikeDetectionResult]
    scale_results: list[BudgetScaleResponse]
    
    execution_time_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
