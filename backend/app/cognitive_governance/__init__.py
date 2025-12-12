"""
SPRINT 14 - Cognitive Governance & Risk Intelligence Layer

Capa transversal de gobernanza cognitiva responsable de:
- Supervisión anticipada del riesgo operativo
- Explicabilidad completa de decisiones
- Simulación previa ligera antes de cada acción crítica
- Control de agresividad del sistema
- Narrativa humana y trazabilidad cognitiva
- Clasificación formal de decisiones

Esta capa NO ejecuta acciones.
NO publica, NO postea, NO escala.
GOBIERNA, VALIDA y PROTEGE al sistema completo.

Integración con:
- Orchestrator (decisiones)
- Supervisor Layer Sprint 10 (GPT + Gemini 3.0)
- Satellite Intelligence Sprint 11 (contexto)
- Account BirthFlow Sprint 12 (lifecycle)
- Observability Layer Sprint 13 (visualización)

Módulos:
- decision_ledger: Registro inmutable de decisiones
- risk_simulation_engine: Simulación de riesgo previa
- aggressiveness_monitor: Control de agresividad global
- narrative_observability: Narrativa humana
- decision_classifier: Clasificador de decisiones (MICRO/STANDARD/CRITICAL/STRUCTURAL)

Arquitectura:
[ Engines ] → [ ORCHESTRATOR ] → [ COGNITIVE GOVERNANCE ← Sprint 14 ] → [ SUPERVISOR ← Sprint 10 ]

Principios:
✔ Toda decisión crítica es explicable
✔ Riesgo anticipado y reversible
✔ No hay loops ni patrones repetitivos
✔ El sistema se autorregula
✔ El humano entiende qué pasa y por qué
"""

from .decision_ledger import (
    DecisionRecord,
    DecisionType,
    DecisionLedger,
)

from .risk_simulation_engine import (
    ActionType,
    SimulationResult,
    RiskSimulationEngine,
)

from .aggressiveness_monitor import (
    AggressivenessLevel,
    AggressivenessScore,
    AggressivenessMonitor,
)

from .narrative_observability import (
    NarrativeReport,
    DecisionExplanation,
    NarrativeObservability,
)

from .decision_classifier import (
    DecisionLevel,
    ClassificationResult,
    DecisionClassifier,
)

from .governance_bridge import (
    DecisionOutcome,
    GovernanceEvaluation,
    CognitiveGovernanceBridge,
)

__all__ = [
    # Decision Ledger
    "DecisionRecord",
    "DecisionType",
    "DecisionLedger",
    # Risk Simulation
    "ActionType",
    "SimulationResult",
    "RiskSimulationEngine",
    # Aggressiveness Monitor
    "AggressivenessLevel",
    "AggressivenessScore",
    "AggressivenessMonitor",
    # Narrative Observability
    "NarrativeReport",
    "DecisionExplanation",
    "NarrativeObservability",
    # Decision Classifier
    "DecisionLevel",
    "ClassificationResult",
    "DecisionClassifier",
    # Governance Bridge (Main Integration Point)
    "DecisionOutcome",
    "GovernanceEvaluation",
    "CognitiveGovernanceBridge",
]

__version__ = "1.0.0"
__sprint__ = "14"
