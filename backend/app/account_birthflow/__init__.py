"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
SPRINT 12.1 - Human-Assisted Warm-Up Scheduler

Sistema completo de ciclo de vida para cuentas satélite.

Módulos Sprint 12:
- account_models: Data models (Account, Metrics, Risk, Profiles)
- account_birthflow: State machine central
- warmup_policy_engine: Warmup humano con gaussian jitter
- account_security_layer: Security checks (proxy, fingerprint, IP)
- account_profile_manager: Identity narratives
- account_metrics_collector: Maturity, risk, readiness scoring
- orchestrator_birthflow_bridge: Permission layer para Orchestrator
- audit_log: Audit log inmutable

Módulos Sprint 12.1:
- human_warmup_scheduler: Generación de tareas diarias humanas
- warmup_task_generator: Diseño adaptativo de acciones
- human_action_verifier: Verificación de completación humana
- warmup_to_autonomy_bridge: Transición warmup → SECURED

Reglas fundamentales:
✔ Creación de cuentas = humana
✔ Warm-up inicial = humano + supervisión
✔ Automatización SOLO desde SECURED
✔ Nunca usar cuentas oficiales
✔ Kill-switch activo
"""

from .account_models import (
    Account,
    AccountState,
    AccountWarmupMetrics,
    AccountRiskProfile,
    AccountRiskLevel,
    AccountLifecycleLog,
    AccountProfileNarrative,
    PlatformType,
    ActionType,
    DAILY_LIMITS_BY_STATE,
    get_daily_limit,
    calculate_total_risk,
    determine_risk_level,
    is_warmup_state,
    can_automate,
    requires_human_action,
)

from .account_birthflow import (
    AccountBirthFlowStateMachine,
    BirthFlowConfig,
    ALLOWED_TRANSITIONS,
    create_test_account,
)

from .warmup_policy_engine import (
    WarmupPolicyEngine,
    WarmupPolicyConfig,
    WarmupActionSchedule,
    WARMUP_SCHEDULES,
    create_warmup_engine,
)

from .account_security_layer import (
    AccountSecurityLayer,
    SecurityLayerConfig,
    SecurityCheckResult,
    create_security_layer,
)

from .account_profile_manager import (
    AccountProfileManager,
    PROFILE_THEMES,
    UNIVERSES,
    PACE_OPTIONS,
    POSTING_STYLES,
    LANGUAGE_BIASES,
    create_profile_manager,
)

from .account_metrics_collector import (
    AccountMetricsCollector,
    MetricsCollectorConfig,
    create_metrics_collector,
)

from .orchestrator_birthflow_bridge import (
    OrchestratorBirthFlowBridge,
    BridgeActionResponse,
    BridgeLimitsResponse,
    create_orchestrator_bridge,
)

from .audit_log import (
    AuditLogger,
    AuditLogConfig,
    AuditLogEntry,
    get_audit_logger,
    set_audit_logger,
    create_audit_logger,
)

# SPRINT 12.1 imports
from .human_warmup_scheduler import (
    HumanWarmupScheduler,
    HumanWarmupSchedulerConfig,
    HumanWarmupTask,
    HumanWarmupAction,
)

from .warmup_task_generator import (
    WarmupTaskGenerator,
    WarmupTaskGeneratorConfig,
)

from .human_action_verifier import (
    HumanActionVerifier,
    HumanActionVerifierConfig,
    VerificationResult,
    create_mock_verification_result,
)

from .warmup_to_autonomy_bridge import (
    WarmupToAutonomyBridge,
    WarmupToAutonomyBridgeConfig,
    TransitionDecision,
)


__all__ = [
    # Models
    "Account",
    "AccountState",
    "AccountWarmupMetrics",
    "AccountRiskProfile",
    "AccountRiskLevel",
    "AccountLifecycleLog",
    "AccountProfileNarrative",
    "PlatformType",
    "ActionType",
    "DAILY_LIMITS_BY_STATE",
    
    # Model helpers
    "get_daily_limit",
    "calculate_total_risk",
    "determine_risk_level",
    "is_warmup_state",
    "can_automate",
    "requires_human_action",
    
    # State machine
    "AccountBirthFlowStateMachine",
    "BirthFlowConfig",
    "ALLOWED_TRANSITIONS",
    "create_test_account",
    
    # Warmup engine
    "WarmupPolicyEngine",
    "WarmupPolicyConfig",
    "WarmupActionSchedule",
    "WARMUP_SCHEDULES",
    "create_warmup_engine",
    
    # Security layer
    "AccountSecurityLayer",
    "SecurityLayerConfig",
    "SecurityCheckResult",
    "create_security_layer",
    
    # Profile manager
    "AccountProfileManager",
    "PROFILE_THEMES",
    "UNIVERSES",
    "PACE_OPTIONS",
    "POSTING_STYLES",
    "LANGUAGE_BIASES",
    "create_profile_manager",
    
    # Metrics collector
    "AccountMetricsCollector",
    "MetricsCollectorConfig",
    "create_metrics_collector",
    
    # Orchestrator bridge
    "OrchestratorBirthFlowBridge",
    "BridgeActionResponse",
    "BridgeLimitsResponse",
    "create_orchestrator_bridge",
    
    # Audit log
    "AuditLogger",
    "AuditLogConfig",
    "AuditLogEntry",
    "get_audit_logger",
    "set_audit_logger",
    "create_audit_logger",
    
    # SPRINT 12.1 - Human Warmup Scheduler
    "HumanWarmupScheduler",
    "HumanWarmupSchedulerConfig",
    "HumanWarmupTask",
    "HumanWarmupAction",
    
    # SPRINT 12.1 - Task Generator
    "WarmupTaskGenerator",
    "WarmupTaskGeneratorConfig",
    
    # SPRINT 12.1 - Action Verifier
    "HumanActionVerifier",
    "HumanActionVerifierConfig",
    "VerificationResult",
    "create_mock_verification_result",
    
    # SPRINT 12.1 - Autonomy Bridge
    "WarmupToAutonomyBridge",
    "WarmupToAutonomyBridgeConfig",
    "TransitionDecision",
]
