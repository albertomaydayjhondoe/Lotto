# backend/app/meta_autopublisher/models.py

"""
Pydantic models y schemas para AutoPublisher.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


class RunStatus(str, Enum):
    """Estado de un AutoPublisher run"""
    PENDING = "pending"
    CREATING_CAMPAIGNS = "creating_campaigns"
    AB_TESTING = "ab_testing"
    ANALYZING_RESULTS = "analyzing_results"
    SELECTING_WINNER = "selecting_winner"
    SCALING_BUDGET = "scaling_budget"
    PUBLISHING_FINAL = "publishing_final"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class ABTestStrategy(str, Enum):
    """Estrategia de A/B testing"""
    CREATIVE_SPLIT = "creative_split"  # Testear diferentes creativos
    AUDIENCE_SPLIT = "audience_split"  # Testear diferentes audiencias
    BUDGET_SPLIT = "budget_split"      # Testear diferentes presupuestos
    COPY_SPLIT = "copy_split"          # Testear diferentes copys
    FULL_FACTORIAL = "full_factorial"  # Combinar múltiples variables


class WinnerSelectionCriteria(str, Enum):
    """Criterio para seleccionar ganador"""
    ROAS = "roas"
    CPA = "cpa"
    CTR = "ctr"
    ENGAGEMENT = "engagement"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ABTestConfig(BaseModel):
    """Configuración de A/B testing"""
    strategy: ABTestStrategy = Field(default=ABTestStrategy.CREATIVE_SPLIT)
    variants_count: int = Field(default=2, ge=2, le=10)
    test_budget_per_variant: float = Field(default=50.0, ge=10.0)
    test_duration_hours: int = Field(default=24, ge=6, le=168)
    min_spend_threshold: float = Field(default=30.0, ge=10.0)
    statistical_significance_level: float = Field(default=0.95, ge=0.8, le=0.99)
    winner_criteria: WinnerSelectionCriteria = Field(default=WinnerSelectionCriteria.ROAS)
    embargo_hours: int = Field(default=6, ge=0, le=48)  # Horas de embargo antes de analizar
    
    class Config:
        use_enum_values = True


class TargetingConfig(BaseModel):
    """Configuración de targeting para campaigns"""
    countries: List[str] = Field(default=["ES"])
    age_min: int = Field(default=18, ge=13, le=65)
    age_max: int = Field(default=65, ge=18, le=65)
    gender: str = Field(default="all")  # "male", "female", "all"
    interests: Optional[List[str]] = None
    placements: List[str] = Field(default=["instagram_feed", "instagram_stories"])
    languages: Optional[List[str]] = None


class BudgetConfig(BaseModel):
    """Configuración de presupuesto"""
    total_budget: float = Field(..., ge=100.0)
    daily_budget: Optional[float] = None
    scaling_factor: float = Field(default=2.0, ge=1.1, le=10.0)
    max_daily_budget: Optional[float] = None
    currency: str = Field(default="USD")


class AutoPublisherRunRequest(BaseModel):
    """Request para iniciar un AutoPublisher run"""
    meta_account_id: UUID
    campaign_name: str = Field(..., min_length=1, max_length=255)
    objective: str = Field(default="CONVERSIONS")
    
    # Configuraciones
    ab_test_config: ABTestConfig = Field(default_factory=ABTestConfig)
    targeting_config: TargetingConfig = Field(default_factory=TargetingConfig)
    budget_config: BudgetConfig
    
    # Creativos (pueden ser IDs de clips o URLs)
    creative_ids: List[UUID] = Field(..., min_items=1)
    
    # Copy variants
    headlines: List[str] = Field(..., min_items=1, max_items=10)
    primary_texts: List[str] = Field(..., min_items=1, max_items=10)
    call_to_actions: List[str] = Field(default=["LEARN_MORE"])
    
    # Control
    require_human_approval: bool = Field(default=True)
    auto_scale_winner: bool = Field(default=False)
    schedule_datetime: Optional[datetime] = None
    
    # Metadata
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class VariantMetrics(BaseModel):
    """Métricas de una variante A/B"""
    variant_id: str
    variant_name: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    roas: float
    ctr: float
    cpc: float
    cpa: float
    confidence_interval: Optional[Dict[str, float]] = None
    is_statistically_significant: bool = False


class WinnerSelection(BaseModel):
    """Resultado de selección de ganador"""
    winner_variant_id: str
    winner_name: str
    winner_metrics: VariantMetrics
    runner_up_variant_id: Optional[str] = None
    runner_up_metrics: Optional[VariantMetrics] = None
    improvement_percentage: float
    confidence_level: float
    selection_reason: str
    all_variants: List[VariantMetrics]


class AutoPublisherRunResponse(BaseModel):
    """Response de un AutoPublisher run"""
    run_id: UUID
    status: RunStatus
    meta_account_id: UUID
    campaign_name: str
    
    # IDs de entidades creadas
    campaign_ids: List[UUID] = Field(default_factory=list)
    adset_ids: List[UUID] = Field(default_factory=list)
    ad_ids: List[UUID] = Field(default_factory=list)
    
    # Resultados
    ab_test_results: Optional[Dict[str, Any]] = None
    winner_selection: Optional[WinnerSelection] = None
    final_campaign_id: Optional[UUID] = None
    
    # Métricas agregadas
    total_spend: float = 0.0
    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_revenue: float = 0.0
    overall_roas: float = 0.0
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Logs y errores
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ScheduleAutoPilotRequest(BaseModel):
    """Request para programar un autopilot run"""
    run_request: AutoPublisherRunRequest
    schedule_datetime: datetime
    recurrence: Optional[str] = None  # "daily", "weekly", "monthly"
    timezone: str = Field(default="UTC")


class PublishWinnerRequest(BaseModel):
    """Request para forzar publicación del ganador"""
    run_id: UUID
    override_approval: bool = Field(default=False)
    final_budget: Optional[float] = None
    notes: Optional[str] = None


# ============================================================================
# INTERNAL MODELS
# ============================================================================

class CampaignVariant(BaseModel):
    """Representa una variante de campaña en A/B test"""
    variant_id: str
    variant_name: str
    campaign_id: Optional[UUID] = None
    adset_id: Optional[UUID] = None
    ad_id: Optional[UUID] = None
    creative_id: UUID
    headline: str
    primary_text: str
    call_to_action: str
    budget: float
    targeting: TargetingConfig
    status: str = "pending"


class RunSnapshot(BaseModel):
    """Snapshot de estado del run en un momento dado"""
    timestamp: datetime
    status: RunStatus
    metrics: Dict[str, Any]
    variants_status: List[Dict[str, Any]]
    decisions_made: List[str]


class OptimizationDecision(BaseModel):
    """Decisión de optimización tomada por el engine"""
    timestamp: datetime
    decision_type: str  # "scale_up", "scale_down", "pause", "reallocate"
    variant_id: str
    previous_budget: float
    new_budget: float
    reason: str
    confidence: float
    applied: bool = False
