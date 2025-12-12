"""
Satellite Engine 2.0 - Sprint 8
Sistema Multicuenta Viral con Anti-Detección + ML Optimization

Sistema capaz de:
- Gestionar 100+ cuentas satélite
- Comportamiento humano simulado (horarios aleatorios, jitter, pauses)
- 1 cuenta → 1 nicho (Shameless, GTA, Stranger Things, etc.)
- Warm-up dinámico y personalizado
- Publicación multi-plataforma (TikTok, Instagram, YouTube)
- Identidades aisladas (VPN+Proxy+Fingerprint)
- ML Learning cada 48h (horarios óptimos, micro-momentos virales)
- Prueba de sonidos A/B testing
"""

from app.satellite_engine.behavior_engine import (
    SatelliteBehaviorEngine,
    AccountSchedule,
    BehaviorPattern,
    AntiCorrelationValidator
)

from app.satellite_engine.niche_engine import (
    SatelliteNicheEngine,
    Niche,
    NicheProfile,
    StyleBook,
    VisualLibrary
)

from app.satellite_engine.content_router import (
    SatelliteContentRouter,
    ContentCandidate,
    ContentType,
    ViralityScore,
    ViralityLevel,
    RoutingDecision
)

from app.satellite_engine.warmup_engine import (
    SatelliteWarmupEngine,
    WarmupPlan,
    WarmupPhase,
    WarmupSchedule
)

from app.satellite_engine.publishing_engine import (
    SatellitePublishingEngine,
    PublishingTask,
    PublishingResult,
    PublishStatus,
    IdentityIsolation,
    Platform
)

from app.satellite_engine.ml_learning import (
    SatelliteMLLearning,
    PerformanceMetrics,
    OptimalTiming,
    MicroMoment,
    LearningCycle,
    LearningPhase
)

from app.satellite_engine.sound_testing import (
    SoundTestingEngine,
    SoundTest,
    SoundMetrics,
    ABTestResult,
    ABTestConfig,
    TestStatus
)

__all__ = [
    # Behavior Engine
    "SatelliteBehaviorEngine",
    "AccountSchedule",
    "BehaviorPattern",
    "AntiCorrelationValidator",
    # Niche Engine
    "SatelliteNicheEngine",
    "Niche",
    "NicheProfile",
    "StyleBook",
    "VisualLibrary",
    # Content Router
    "SatelliteContentRouter",
    "ContentCandidate",
    "ContentType",
    "ViralityScore",
    "ViralityLevel",
    "RoutingDecision",
    # Warmup Engine
    "SatelliteWarmupEngine",
    "WarmupPlan",
    "WarmupPhase",
    "WarmupSchedule",
    # Publishing Engine
    "SatellitePublishingEngine",
    "PublishingTask",
    "PublishingResult",
    "PublishStatus",
    "IdentityIsolation",
    "Platform",
    # ML Learning
    "SatelliteMLLearning",
    "PerformanceMetrics",
    "OptimalTiming",
    "MicroMoment",
    "LearningCycle",
    "LearningPhase",
    # Sound Testing
    "SoundTestingEngine",
    "SoundTest",
    "SoundMetrics",
    "ABTestResult",
    "ABTestConfig",
    "TestStatus",
]

__version__ = "2.0.0"
__sprint__ = "8"
