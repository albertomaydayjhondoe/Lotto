"""
SPRINT 10 - Global Supervisor Layer
Module 1: Supervisor Contract - Interfaces y contratos estándar

Define las interfaces y contratos que usan todos los componentes del supervisor layer.
Esta es la fuente única de verdad para tipos y estructuras de datos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS - Estados y niveles
# ============================================================================

class SeverityLevel(Enum):
    """Nivel de severidad de una acción o decisión"""
    LOW = "low"              # Operación rutinaria, bajo riesgo
    MEDIUM = "medium"        # Requiere atención, riesgo moderado
    HIGH = "high"            # Crítica, alto riesgo
    CRITICAL = "critical"    # Emergencia, máximo riesgo


class EngineSource(Enum):
    """Motor que origina la acción o decisión"""
    ORCHESTRATOR = "orchestrator"
    SATELLITE = "satellite_engine"
    META_ADS = "meta_ads"
    TELEGRAM = "telegram_bot"
    CONTENT = "content_router"
    ML = "ml_learning"
    RULES = "rules_engine"
    SUPERVISOR = "supervisor"


class DecisionType(Enum):
    """Tipo de decisión tomada"""
    PUBLISH_CONTENT = "publish_content"
    SCALE_ADS = "scale_ads"
    ADJUST_BUDGET = "adjust_budget"
    CHANGE_STRATEGY = "change_strategy"
    RETRAIN_MODEL = "retrain_model"
    ALERT_HUMAN = "alert_human"
    PAUSE_CAMPAIGN = "pause_campaign"
    ACTIVATE_ACCOUNT = "activate_account"
    DEACTIVATE_ACCOUNT = "deactivate_account"


class RiskType(Enum):
    """Tipo de riesgo detectado"""
    BUDGET_EXCEEDED = "budget_exceeded"
    PATTERN_REPETITION = "pattern_repetition"
    IDENTITY_CORRELATION = "identity_correlation"
    TIMING_SIMILARITY = "timing_similarity"
    SHADOWBAN_SIGNAL = "shadowban_signal"
    ANOMALY_DETECTED = "anomaly_detected"
    COGNITIVE_INCOHERENCE = "cognitive_incoherence"
    LLM_HALLUCINATION = "llm_hallucination"


class ValidationStatus(Enum):
    """Estado de validación"""
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_ADJUSTMENT = "requires_adjustment"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


# ============================================================================
# DATA STRUCTURES - Decisiones y acciones
# ============================================================================

@dataclass
class Decision:
    """Decisión tomada por el sistema"""
    type: DecisionType
    description: str
    engine_source: EngineSource
    timestamp: datetime
    reasoning: str
    alternatives_considered: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Acción ejecutada por el sistema"""
    action_id: str
    type: str
    engine_source: EngineSource
    timestamp: datetime
    target: str  # Cuenta, campaña, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class Metrics:
    """Métricas clave del sistema"""
    # Engagement
    avg_retention: float = 0.0
    engagement_velocity: float = 0.0
    avg_ctr: float = 0.0
    
    # Ads (Meta)
    avg_cpm: float = 0.0
    avg_cpc: float = 0.0
    total_impressions: int = 0
    total_clicks: int = 0
    
    # Risk signals
    shadowban_signals: int = 0
    correlation_signals: int = 0
    
    # ML confidence
    ml_confidence: float = 0.0
    
    # Timestamp
    measured_at: datetime = field(default_factory=datetime.now)
    
    # Additional metrics
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostReport:
    """Reporte de costes del sistema"""
    today: float = 0.0
    week_accumulated: float = 0.0
    month_accumulated: float = 0.0
    budget_remaining: float = 0.0
    budget_total: float = 0.0
    
    # Breakdown por motor
    satellite_costs: float = 0.0
    meta_ads_costs: float = 0.0
    telegram_costs: float = 0.0
    other_costs: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Risk:
    """Riesgo detectado"""
    type: RiskType
    severity: SeverityLevel
    description: str
    score: float  # 0-1
    detected_at: datetime
    affected_targets: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Anomalía detectada"""
    anomaly_id: str
    type: str
    description: str
    severity: SeverityLevel
    detected_at: datetime
    value_expected: Optional[Any] = None
    value_actual: Optional[Any] = None
    affected_component: Optional[str] = None
    requires_investigation: bool = False


# ============================================================================
# SUPERVISION INPUT - Lo que recibe el supervisor
# ============================================================================

@dataclass
class SupervisionInput:
    """Input completo para el supervisor layer"""
    
    # Identificación
    supervision_id: str
    timestamp: datetime
    
    # Contexto
    engine_source: EngineSource
    severity: SeverityLevel
    
    # Datos core
    decisions: List[Decision] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    metrics: Optional[Metrics] = None
    costs: Optional[CostReport] = None
    risks: List[Risk] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)
    
    # Contexto adicional
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SUMMARY OUTPUT - Lo que produce el Summary Generator
# ============================================================================

@dataclass
class SummaryOutput:
    """Output del Summary Generator (E2B)"""
    
    # Identificación
    summary_id: str
    timestamp: datetime
    
    # JSON estructurado
    structured_data: Dict[str, Any]
    
    # Texto natural
    natural_language_summary: str
    
    # Estadísticas
    total_decisions: int = 0
    total_actions: int = 0
    total_risks: int = 0
    total_anomalies: int = 0
    
    # Flags
    requires_attention: bool = False
    critical_issues: List[str] = field(default_factory=list)


# ============================================================================
# GPT OUTPUT - Lo que produce el GPT Supervisor
# ============================================================================

@dataclass
class GPTAnalysis:
    """Output del GPT Cognitive Analyzer"""
    
    # Identificación
    analysis_id: str
    timestamp: datetime
    
    # Análisis
    observations: List[str] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)
    strategic_suggestions: List[str] = field(default_factory=list)
    risk_signals: List[str] = field(default_factory=list)
    recommended_adjustments: List[str] = field(default_factory=list)
    
    # Confianza
    confidence: float = 0.0  # 0-1
    
    # Metadata
    model_used: str = "gpt-4"
    reasoning: str = ""


# ============================================================================
# GEMINI OUTPUT - Lo que produce el Gemini Validator
# ============================================================================

@dataclass
class ValidationResult:
    """Output del Gemini 3.0 Hard Validator"""
    
    # Identificación
    validation_id: str
    timestamp: datetime
    
    # Decision
    approved: bool
    status: ValidationStatus
    reason: str
    
    # Risk assessment
    risk_score: float  # 0-1
    risk_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Adjustments
    required_adjustments: List[str] = field(default_factory=list)
    
    # Reglas violadas
    violated_rules: List[str] = field(default_factory=list)
    
    # Metadata
    model_used: str = "gemini-3.0"
    validation_rules_applied: List[str] = field(default_factory=list)


# ============================================================================
# SUPERVISION OUTPUT - Lo que retorna el supervisor completo
# ============================================================================

@dataclass
class SupervisionOutput:
    """Output completo del supervisor layer"""
    
    # Identificación
    supervision_id: str
    timestamp: datetime
    
    # Componentes
    summary: SummaryOutput
    gpt_analysis: GPTAnalysis
    gemini_validation: ValidationResult
    
    # Decisión final
    final_decision: ValidationStatus
    final_approval: bool
    
    # Explicación
    explanation: str
    
    # Telemetría
    processing_time_ms: float = 0.0
    components_executed: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CONFIGURATION - Configuración del supervisor
# ============================================================================

@dataclass
class SupervisorConfig:
    """Configuración del supervisor layer"""
    
    # Thresholds de riesgo
    risk_threshold_low: float = 0.3
    risk_threshold_medium: float = 0.6
    risk_threshold_high: float = 0.8
    
    # Presupuestos
    daily_budget_limit: float = 50.0
    monthly_budget_limit: float = 1000.0
    
    # Pattern detection
    pattern_similarity_threshold: float = 0.7
    timing_similarity_threshold: float = 0.65
    identity_correlation_threshold: float = 0.75
    
    # LLM configs
    gpt_model: str = "gpt-4"
    gpt_temperature: float = 0.3
    gemini_model: str = "gemini-3.0"
    
    # Timeouts
    summary_timeout_seconds: int = 10
    gpt_timeout_seconds: int = 15
    gemini_timeout_seconds: int = 10
    
    # Fallback behavior
    enable_fallback: bool = True
    fallback_strategy: str = "conservative"  # conservative, permissive, reject_all
    
    # Logging
    log_all_decisions: bool = True
    log_rejections: bool = True
    log_adjustments: bool = True
    
    # Human oversight
    require_human_for_critical: bool = True
    alert_threshold: float = 0.85


# ============================================================================
# HELPER FUNCTIONS - Utilidades
# ============================================================================

def create_supervision_input(
    engine_source: EngineSource,
    severity: SeverityLevel,
    decisions: List[Decision] = None,
    actions: List[Action] = None,
    context_summary: str = ""
) -> SupervisionInput:
    """Helper para crear un SupervisionInput"""
    import uuid
    
    return SupervisionInput(
        supervision_id=f"sup_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(),
        engine_source=engine_source,
        severity=severity,
        decisions=decisions or [],
        actions=actions or [],
        context_summary=context_summary
    )


def create_default_config() -> SupervisorConfig:
    """Crea configuración por defecto del supervisor"""
    return SupervisorConfig()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "SeverityLevel",
    "EngineSource",
    "DecisionType",
    "RiskType",
    "ValidationStatus",
    
    # Data structures
    "Decision",
    "Action",
    "Metrics",
    "CostReport",
    "Risk",
    "Anomaly",
    
    # Input/Output
    "SupervisionInput",
    "SummaryOutput",
    "GPTAnalysis",
    "ValidationResult",
    "SupervisionOutput",
    
    # Config
    "SupervisorConfig",
    
    # Helpers
    "create_supervision_input",
    "create_default_config",
]
