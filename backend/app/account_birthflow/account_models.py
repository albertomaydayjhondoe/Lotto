"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Account Models

Modelos de datos para el sistema completo de ciclo de vida de cuentas satélite.
Incluye estados, métricas de warmup, perfiles de riesgo y logs de lifecycle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class AccountState(Enum):
    """
    Estados del ciclo de vida de una cuenta.
    
    Flujo normal:
    CREATED → W1_3 → W4_7 → W8_14 → SECURED → ACTIVE → SCALING
    
    Estados especiales:
    COOLDOWN: Enfriamiento temporal por señales de riesgo
    PAUSED: Pausada manualmente o por violación
    RETIRED: Retirada permanentemente
    """
    CREATED = "created"          # Recién creada, no operativa
    W1_3 = "w1_3"                # Warmup días 1-3: view + 1-2 likes
    W4_7 = "w4_7"                # Warmup días 4-7: 2-4 likes + 1 comment
    W8_14 = "w8_14"              # Warmup días 8-14: 1 post ocasional
    SECURED = "secured"          # Warmup completo, identidad establecida
    ACTIVE = "active"            # Operación normal, automatización permitida
    SCALING = "scaling"          # Escalado de actividad
    COOLDOWN = "cooldown"        # Enfriamiento temporal
    PAUSED = "paused"            # Pausada (manual o violación)
    RETIRED = "retired"          # Retirada permanentemente


class PlatformType(Enum):
    """Plataforma de la cuenta"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"


class AccountRiskLevel(Enum):
    """Nivel de riesgo de la cuenta"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """Tipos de acciones permitidas por estado"""
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    POST = "post"
    SHARE = "share"
    SAVE = "save"


# ============================================================================
# DAILY LIMITS BY STATE
# ============================================================================

DAILY_LIMITS_BY_STATE = {
    AccountState.CREATED: {
        # No actions allowed until W1_3
        ActionType.VIEW: 0,
        ActionType.LIKE: 0,
        ActionType.COMMENT: 0,
        ActionType.FOLLOW: 0,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 0,
    },
    AccountState.W1_3: {
        # Conservative warmup: view + minimal likes
        ActionType.VIEW: 20,
        ActionType.LIKE: 2,
        ActionType.COMMENT: 0,
        ActionType.FOLLOW: 0,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 1,
    },
    AccountState.W4_7: {
        # Gradual increase: more likes + first comment
        ActionType.VIEW: 40,
        ActionType.LIKE: 4,
        ActionType.COMMENT: 1,
        ActionType.FOLLOW: 1,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 2,
    },
    AccountState.W8_14: {
        # Maturing: occasional posts
        ActionType.VIEW: 60,
        ActionType.LIKE: 6,
        ActionType.COMMENT: 2,
        ActionType.FOLLOW: 2,
        ActionType.POST: 1,
        ActionType.SHARE: 1,
        ActionType.SAVE: 3,
    },
    AccountState.SECURED: {
        # Identity established: normal activity
        ActionType.VIEW: 100,
        ActionType.LIKE: 10,
        ActionType.COMMENT: 4,
        ActionType.FOLLOW: 3,
        ActionType.POST: 2,
        ActionType.SHARE: 2,
        ActionType.SAVE: 5,
    },
    AccountState.ACTIVE: {
        # Full automation allowed
        ActionType.VIEW: 200,
        ActionType.LIKE: 20,
        ActionType.COMMENT: 8,
        ActionType.FOLLOW: 5,
        ActionType.POST: 3,
        ActionType.SHARE: 4,
        ActionType.SAVE: 10,
    },
    AccountState.SCALING: {
        # Increased activity
        ActionType.VIEW: 300,
        ActionType.LIKE: 30,
        ActionType.COMMENT: 12,
        ActionType.FOLLOW: 8,
        ActionType.POST: 5,
        ActionType.SHARE: 6,
        ActionType.SAVE: 15,
    },
    AccountState.COOLDOWN: {
        # Reduced activity during cooldown
        ActionType.VIEW: 30,
        ActionType.LIKE: 3,
        ActionType.COMMENT: 1,
        ActionType.FOLLOW: 0,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 2,
    },
    AccountState.PAUSED: {
        # No actions while paused
        ActionType.VIEW: 0,
        ActionType.LIKE: 0,
        ActionType.COMMENT: 0,
        ActionType.FOLLOW: 0,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 0,
    },
    AccountState.RETIRED: {
        # No actions for retired accounts
        ActionType.VIEW: 0,
        ActionType.LIKE: 0,
        ActionType.COMMENT: 0,
        ActionType.FOLLOW: 0,
        ActionType.POST: 0,
        ActionType.SHARE: 0,
        ActionType.SAVE: 0,
    },
}


# ============================================================================
# CORE MODELS
# ============================================================================

@dataclass
class Account:
    """
    Modelo principal de cuenta satélite.
    
    Representa una cuenta en su ciclo de vida completo.
    """
    account_id: str
    platform: PlatformType
    
    # State & lifecycle
    current_state: AccountState
    state_entered_at: datetime
    warmup_day: int = 0
    
    # Identity & profile
    username: Optional[str] = None
    theme: Optional[str] = None
    universe: Optional[str] = None
    niche_id: Optional[str] = None
    
    # Security
    proxy_id: Optional[str] = None
    fingerprint_id: Optional[str] = None
    session_token: Optional[str] = None
    
    # Metrics
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    
    # Risk tracking
    shadowban_signals: int = 0
    correlation_signals: int = 0
    behavioral_anomalies: int = 0
    
    # Lifecycle timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_action_at: Optional[datetime] = None
    secured_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
    
    # Flags
    is_active: bool = True
    is_official: bool = False  # Never use official accounts
    requires_manual_review: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountWarmupMetrics:
    """
    Métricas de warmup y maduración de una cuenta.
    
    Trackea el progreso durante las fases de warmup.
    """
    account_id: str
    
    # Warmup progress
    warmup_day: int
    warmup_phase: AccountState
    warmup_completed: bool = False
    
    # Activity metrics (actions performed)
    views_performed: int = 0
    likes_performed: int = 0
    comments_performed: int = 0
    follows_performed: int = 0
    posts_performed: int = 0
    shares_performed: int = 0
    saves_performed: int = 0
    
    # Engagement received
    impressions_received: int = 0
    likes_received: int = 0
    comments_received: int = 0
    follows_received: int = 0
    shares_received: int = 0
    
    # Quality metrics
    follow_view_ratio: float = 0.0
    block_view_ratio: float = 0.0
    comment_realism_score: float = 0.0
    session_stability_score: float = 0.0
    
    # Maturity scores
    maturity_score: float = 0.0  # 0-1
    readiness_level: float = 0.0  # 0-1
    
    # Timestamps
    first_action_at: Optional[datetime] = None
    last_action_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountRiskProfile:
    """
    Perfil de riesgo de una cuenta.
    
    Trackea señales de riesgo y calcula score global.
    """
    account_id: str
    
    # Risk scores (0-1)
    shadowban_risk: float = 0.0
    correlation_risk: float = 0.0
    fingerprint_risk: float = 0.0
    behavioral_risk: float = 0.0
    timing_risk: float = 0.0
    
    # Risk signals count
    shadowban_signals: int = 0
    correlation_signals: int = 0
    fingerprint_reuse_signals: int = 0
    timing_similarity_signals: int = 0
    behavioral_anomaly_signals: int = 0
    
    # Global risk
    total_risk_score: float = 0.0  # Weighted average
    risk_level: AccountRiskLevel = AccountRiskLevel.VERY_LOW
    
    # Thresholds
    cooldown_threshold: float = 0.6
    pause_threshold: float = 0.8
    
    # Actions taken
    cooldowns_triggered: int = 0
    pauses_triggered: int = 0
    
    # Timestamps
    last_risk_check_at: datetime = field(default_factory=datetime.now)
    last_incident_at: Optional[datetime] = None
    
    # Notes
    risk_notes: List[str] = field(default_factory=list)


@dataclass
class AccountLifecycleLog:
    """
    Log entry para auditoría del ciclo de vida.
    
    Registro inmutable de cada acción/transición.
    """
    log_id: str
    account_id: str
    timestamp: datetime
    
    # Event type
    event_type: str  # "state_transition", "action", "risk_event", "manual_intervention"
    
    # State info
    from_state: Optional[AccountState] = None
    to_state: Optional[AccountState] = None
    
    # Action info
    action_type: Optional[ActionType] = None
    action_success: Optional[bool] = None
    
    # Context
    reason: str = ""
    risk_score: float = 0.0
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # User/system
    triggered_by: str = "system"  # "system", "manual", "policy"
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PROFILE OBJECT
# ============================================================================

@dataclass
class AccountProfileNarrative:
    """
    Identidad narrativa de una cuenta.
    
    Define el 'personaje' y comportamiento único de la cuenta.
    """
    account_id: str
    
    # Identity
    theme: str  # e.g., "music_discovery", "cooking_simple", "tech_tips"
    universe: str  # e.g., "indie_music", "quick_meals", "productivity_hacks"
    
    # Behavior
    pace: str  # "slow", "medium", "fast"
    posting_style: str  # "consistent", "burst", "organic"
    
    # Risk & strategy
    risk_tolerance: float = 0.3  # 0-1
    automation_level: float = 0.5  # 0-1 (0=manual, 1=full auto)
    
    # Content preferences
    language_bias: List[str] = field(default_factory=lambda: ["en"])
    content_themes: List[str] = field(default_factory=list)
    hashtag_strategy: str = "niche"  # "niche", "trending", "mixed"
    
    # Platform specifics
    platform: PlatformType = PlatformType.TIKTOK
    
    # Timing preferences
    preferred_hours: List[int] = field(default_factory=list)
    preferred_days: List[int] = field(default_factory=list)
    
    # Created
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_daily_limit(state: AccountState, action: ActionType) -> int:
    """Get daily limit for action in given state"""
    return DAILY_LIMITS_BY_STATE.get(state, {}).get(action, 0)


def calculate_total_risk(risk_profile: AccountRiskProfile) -> float:
    """
    Calculate total risk score from individual components.
    
    Weighted average:
    - Shadowban: 30%
    - Correlation: 30%
    - Fingerprint: 15%
    - Behavioral: 15%
    - Timing: 10%
    """
    total = (
        risk_profile.shadowban_risk * 0.30 +
        risk_profile.correlation_risk * 0.30 +
        risk_profile.fingerprint_risk * 0.15 +
        risk_profile.behavioral_risk * 0.15 +
        risk_profile.timing_risk * 0.10
    )
    return min(total, 1.0)


def determine_risk_level(risk_score: float) -> AccountRiskLevel:
    """Determine risk level from score"""
    if risk_score < 0.2:
        return AccountRiskLevel.VERY_LOW
    elif risk_score < 0.4:
        return AccountRiskLevel.LOW
    elif risk_score < 0.6:
        return AccountRiskLevel.MEDIUM
    elif risk_score < 0.8:
        return AccountRiskLevel.HIGH
    else:
        return AccountRiskLevel.CRITICAL


def is_warmup_state(state: AccountState) -> bool:
    """Check if state is a warmup phase"""
    return state in [AccountState.W1_3, AccountState.W4_7, AccountState.W8_14]


def can_automate(state: AccountState) -> bool:
    """Check if automation is allowed in this state"""
    return state in [AccountState.SECURED, AccountState.ACTIVE, AccountState.SCALING]


def requires_human_action(state: AccountState) -> bool:
    """Check if human action is required"""
    return state in [AccountState.CREATED, AccountState.W1_3, AccountState.W4_7]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "AccountState",
    "PlatformType",
    "AccountRiskLevel",
    "ActionType",
    
    # Constants
    "DAILY_LIMITS_BY_STATE",
    
    # Models
    "Account",
    "AccountWarmupMetrics",
    "AccountRiskProfile",
    "AccountLifecycleLog",
    "AccountProfileNarrative",
    
    # Helpers
    "get_daily_limit",
    "calculate_total_risk",
    "determine_risk_level",
    "is_warmup_state",
    "can_automate",
    "requires_human_action",
]
