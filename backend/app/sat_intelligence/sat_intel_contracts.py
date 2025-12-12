"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Satellite Intelligence Contracts

Define estructuras de datos, enums y contratos para el sistema de inteligencia
de cuentas satélite.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class ProposalStatus(Enum):
    """Estado de una propuesta"""
    DRAFT = "draft"
    PENDING_EVALUATION = "pending_evaluation"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ProposalPriority(Enum):
    """Prioridad de una propuesta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(Enum):
    """Tipo de contenido"""
    VIDEO_CLIP = "video_clip"
    SCENE_EXTRACT = "scene_extract"
    AI_GENERATED = "ai_generated"
    MIXED_MEDIA = "mixed_media"


class RiskLevel(Enum):
    """Nivel de riesgo de una propuesta"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# DATA STRUCTURES - Content & Scoring
# ============================================================================

@dataclass
class ContentMetadata:
    """Metadata de contenido enriquecida"""
    content_id: str
    content_type: ContentType
    duration_seconds: float
    
    # Vision metadata
    visual_tags: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    scene_types: List[str] = field(default_factory=list)
    motion_intensity: float = 0.0
    
    # Audio metadata
    audio_track_id: Optional[str] = None
    bpm: Optional[int] = None
    energy: float = 0.0
    valence: float = 0.0
    
    # Performance metrics (si existen)
    avg_retention: Optional[float] = None
    avg_virality_score: Optional[float] = None
    
    # Additional
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClipScore:
    """Score de un clip para una cuenta específica"""
    content_id: str
    account_id: str
    
    # Score total (0-1)
    total_score: float
    
    # Breakdown por factores
    niche_match_score: float  # Qué tan bien match con el nicho de la cuenta
    virality_score: float  # Predicción de viralidad
    timing_score: float  # Qué tan bueno es el timing
    uniqueness_score: float  # Qué tan único/no usado es
    audio_match_score: float  # Match audio con estilo cuenta
    
    # Metadata
    confidence: float = 0.0
    scored_at: datetime = field(default_factory=datetime.now)
    reasoning: str = ""


# ============================================================================
# DATA STRUCTURES - Variants & Timing
# ============================================================================

@dataclass
class ContentVariant:
    """Variante de contenido (caption, hashtags, etc.)"""
    variant_id: str
    
    # Content variations
    caption: str
    hashtags: List[str]
    thumbnail_index: Optional[int] = None
    
    # Audio variation
    audio_track_id: Optional[str] = None
    audio_start_offset: float = 0.0
    
    # Metadata
    template_used: Optional[str] = None
    randomization_seed: Optional[int] = None


@dataclass
class TimingWindow:
    """Ventana de tiempo óptima para publicar"""
    start_time: datetime
    end_time: datetime
    
    # Scores
    optimal_score: float  # 0-1, qué tan óptima es esta ventana
    competition_score: float  # 0-1, cuánta competencia hay
    audience_score: float  # 0-1, cuánta audiencia esperada
    
    # Jitter aplicado
    jitter_minutes: float = 0.0
    
    # Reasoning
    reasoning: str = ""


# ============================================================================
# DATA STRUCTURES - Proposals
# ============================================================================

@dataclass
class ContentProposal:
    """Propuesta de publicación de contenido"""
    
    # Identificación
    proposal_id: str
    created_at: datetime
    
    # Content & Account
    content_id: str
    account_id: str
    niche_id: str
    
    # Variant & Timing
    variant: ContentVariant
    timing_window: TimingWindow
    
    # Scores & Priority
    clip_score: ClipScore
    priority: ProposalPriority
    risk_level: RiskLevel
    risk_score: float  # 0-1
    
    # Decision support
    rationale: str  # Por qué esta propuesta
    alternatives_considered: List[str] = field(default_factory=list)
    constraints_applied: List[str] = field(default_factory=list)
    
    # Status
    status: ProposalStatus = ProposalStatus.DRAFT
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposalBatch:
    """Batch de propuestas para múltiples cuentas"""
    batch_id: str
    created_at: datetime
    
    proposals: List[ContentProposal]
    
    # Batch metadata
    total_accounts: int
    content_pool_size: int
    
    # Batch statistics
    avg_clip_score: float = 0.0
    avg_risk_score: float = 0.0
    high_priority_count: int = 0
    
    # Constraints
    max_simultaneous_posts: int = 3
    pattern_similarity_threshold: float = 0.7


# ============================================================================
# DATA STRUCTURES - Evaluation
# ============================================================================

@dataclass
class ProposalEvaluation:
    """Evaluación de una propuesta"""
    proposal_id: str
    evaluated_at: datetime
    
    # Decision
    approved: bool
    rejection_reason: Optional[str] = None
    
    # Scores
    safety_score: float = 1.0  # 1.0 = seguro
    policy_compliance_score: float = 1.0
    timing_quality_score: float = 0.0
    content_quality_score: float = 0.0
    
    # Flags
    requires_human_review: bool = False
    has_official_assets: bool = False
    exceeds_sync_limit: bool = False
    
    # Recommendations
    recommended_adjustments: List[str] = field(default_factory=list)
    
    # Evaluator
    evaluator_id: str = "auto"


# ============================================================================
# DATA STRUCTURES - Sound Testing
# ============================================================================

@dataclass
class SoundTestRecommendation:
    """Recomendación de A/B test de sonidos"""
    recommendation_id: str
    created_at: datetime
    
    # Tracks a testear
    track_a_id: str
    track_b_id: str
    
    # Recommended configuration
    accounts_per_track: int
    posts_per_account: int
    test_duration_hours: int
    
    # Justification
    rationale: str
    expected_insights: List[str]
    
    # Performance data (si existe)
    track_a_historical_performance: Optional[Dict[str, float]] = None
    track_b_historical_performance: Optional[Dict[str, float]] = None


# ============================================================================
# DATA STRUCTURES - Profile Management
# ============================================================================

@dataclass
class AccountProfile:
    """Perfil completo de una cuenta satélite"""
    account_id: str
    
    # Identity
    niche_id: str
    niche_name: str
    
    # State
    is_active: bool = False
    warmup_completed: bool = False
    warmup_day: int = 0
    
    # Statistics
    total_posts: int = 0
    last_post_at: Optional[datetime] = None
    avg_retention: float = 0.0
    avg_engagement: float = 0.0
    
    # Posting history (últimos 30 días)
    recent_content_ids: List[str] = field(default_factory=list)
    recent_audio_ids: List[str] = field(default_factory=list)
    
    # Optimal timing (ML learned)
    optimal_hours: List[int] = field(default_factory=list)
    optimal_days: List[int] = field(default_factory=list)
    
    # Risk signals
    shadowban_signals: int = 0
    correlation_signals: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

@dataclass
class GenerateProposalRequest:
    """Request para generar propuestas"""
    
    # Content pool
    content_ids: List[str]
    
    # Target accounts
    account_ids: Optional[List[str]] = None  # None = todas las cuentas activas
    
    # Constraints
    max_proposals: int = 100
    min_clip_score: float = 0.5
    max_risk_score: float = 0.7
    
    # Timing
    target_timeframe_hours: int = 24
    
    # Options
    include_alternatives: bool = True
    simulate_only: bool = False


@dataclass
class GenerateProposalResponse:
    """Response de generación de propuestas"""
    batch_id: str
    generated_at: datetime
    
    # Proposals
    proposals: List[ContentProposal]
    
    # Statistics
    total_generated: int
    high_priority_count: int
    approved_count: int
    rejected_count: int
    
    # Metadata
    processing_time_ms: float
    errors: List[str] = field(default_factory=list)


@dataclass
class EvaluateProposalRequest:
    """Request para evaluar propuestas"""
    proposal_ids: List[str]
    
    # Options
    strict_mode: bool = False
    require_supervisor_approval: bool = True


@dataclass
class EvaluateProposalResponse:
    """Response de evaluación"""
    evaluated_at: datetime
    
    evaluations: List[ProposalEvaluation]
    
    # Summary
    total_evaluated: int
    approved_count: int
    rejected_count: int
    requires_human_review_count: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_risk_level(risk_score: float) -> RiskLevel:
    """Calcula risk level basado en risk score"""
    if risk_score < 0.2:
        return RiskLevel.VERY_LOW
    elif risk_score < 0.4:
        return RiskLevel.LOW
    elif risk_score < 0.6:
        return RiskLevel.MEDIUM
    elif risk_score < 0.8:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH


def calculate_priority(clip_score: ClipScore, timing_score: float, risk_score: float) -> ProposalPriority:
    """Calcula prioridad de propuesta"""
    # Prioridad basada en score total y riesgo
    combined_score = (clip_score.total_score * 0.6 + timing_score * 0.3 - risk_score * 0.1)
    
    if combined_score >= 0.8:
        return ProposalPriority.CRITICAL
    elif combined_score >= 0.65:
        return ProposalPriority.HIGH
    elif combined_score >= 0.45:
        return ProposalPriority.MEDIUM
    else:
        return ProposalPriority.LOW


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "ProposalStatus",
    "ProposalPriority",
    "ContentType",
    "RiskLevel",
    
    # Content & Scoring
    "ContentMetadata",
    "ClipScore",
    
    # Variants & Timing
    "ContentVariant",
    "TimingWindow",
    
    # Proposals
    "ContentProposal",
    "ProposalBatch",
    
    # Evaluation
    "ProposalEvaluation",
    
    # Sound Testing
    "SoundTestRecommendation",
    
    # Profile Management
    "AccountProfile",
    
    # API Models
    "GenerateProposalRequest",
    "GenerateProposalResponse",
    "EvaluateProposalRequest",
    "EvaluateProposalResponse",
    
    # Helpers
    "calculate_risk_level",
    "calculate_priority",
]
