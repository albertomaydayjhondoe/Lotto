"""
SPRINT 11 - Satellite Intelligence Optimization

Sistema de inteligencia para cuentas satélite que decide QUÉ contenido
priorizar, DÓNDE publicarlo y con QUÉ variantes.

Módulos:
- sat_intel_contracts: Estructuras de datos y contratos
- identity_aware_clip_scoring: Scoring de clips con identidad de cuenta
- timing_optimizer: Optimización de timing con gaussian jitter
- universe_profile_manager: Gestión de perfiles de cuentas
- sound_test_recommender: Planificación de A/B tests de audio
- variant_generator_bridge: Generación de variantes de contenido
- proposal_evaluator: Evaluación y filtrado de propuestas
- sat_intel_api: API principal orquestadora

Integrations:
- Sprint 10 Supervisor: Validación de propuestas
- Sprint 8 Satellite Engine: Ejecución de acciones
- Vision Engine: Metadata visual
- Content Engine: Metadata de audio
- ML Persistence: Predicciones de viralidad
- Rules Engine: Constraints de policy
"""

# ============================================================================
# CONTRACTS & DATA STRUCTURES
# ============================================================================

from .sat_intel_contracts import (
    # Enums
    ProposalStatus,
    ProposalPriority,
    ContentType,
    RiskLevel,
    
    # Content & Scoring
    ContentMetadata,
    ClipScore,
    
    # Variants & Timing
    ContentVariant,
    TimingWindow,
    
    # Proposals
    ContentProposal,
    ProposalBatch,
    
    # Evaluation
    ProposalEvaluation,
    
    # Sound Testing
    SoundTestRecommendation,
    
    # Profile Management
    AccountProfile,
    
    # API Models
    GenerateProposalRequest,
    GenerateProposalResponse,
    EvaluateProposalRequest,
    EvaluateProposalResponse,
    
    # Helpers
    calculate_risk_level,
    calculate_priority,
)

# ============================================================================
# CORE MODULES
# ============================================================================

from .identity_aware_clip_scoring import (
    ScoringConfig,
    IdentityAwareClipScorer,
    score_clip_simple,
)

from .timing_optimizer import (
    TimingConfig,
    TimingOptimizer,
    calculate_time_series_entropy,
    find_next_optimal_time,
)

from .universe_profile_manager import (
    ProfileManagerConfig,
    UniverseProfileManager,
)

from .sound_test_recommender import (
    SoundTestConfig,
    SoundTestRecommender,
    analyze_test_results,
)

from .variant_generator_bridge import (
    VariantConfig,
    VariantGeneratorBridge,
    generate_simple_variant,
)

from .proposal_evaluator import (
    EvaluatorConfig,
    ProposalEvaluator,
)

# ============================================================================
# MAIN API
# ============================================================================

from .sat_intel_api import (
    SatIntelConfig,
    SatelliteIntelligenceAPI,
    generate_proposals_simple,
)

# ============================================================================
# VERSION
# ============================================================================

__version__ = "11.0.0"
__sprint__ = "SPRINT_11"

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Contracts
    "ProposalStatus",
    "ProposalPriority",
    "ContentType",
    "RiskLevel",
    "ContentMetadata",
    "ClipScore",
    "ContentVariant",
    "TimingWindow",
    "ContentProposal",
    "ProposalBatch",
    "ProposalEvaluation",
    "SoundTestRecommendation",
    "AccountProfile",
    "GenerateProposalRequest",
    "GenerateProposalResponse",
    "EvaluateProposalRequest",
    "EvaluateProposalResponse",
    "calculate_risk_level",
    "calculate_priority",
    
    # Clip Scoring
    "ScoringConfig",
    "IdentityAwareClipScorer",
    "score_clip_simple",
    
    # Timing Optimizer
    "TimingConfig",
    "TimingOptimizer",
    "calculate_time_series_entropy",
    "find_next_optimal_time",
    
    # Profile Manager
    "ProfileManagerConfig",
    "UniverseProfileManager",
    
    # Sound Test Recommender
    "SoundTestConfig",
    "SoundTestRecommender",
    "analyze_test_results",
    
    # Variant Generator
    "VariantConfig",
    "VariantGeneratorBridge",
    "generate_simple_variant",
    
    # Proposal Evaluator
    "EvaluatorConfig",
    "ProposalEvaluator",
    
    # Main API
    "SatIntelConfig",
    "SatelliteIntelligenceAPI",
    "generate_proposals_simple",
    
    # Metadata
    "__version__",
    "__sprint__",
]
