"""
SPRINT 10 - Global Supervisor Layer
Module __init__.py - Exports

Exporta todos los componentes del supervisor layer para uso fácil.
"""

# Contract and types
from .supervisor_contract import (
    # Enums
    SeverityLevel,
    EngineSource,
    DecisionType,
    RiskType,
    ValidationStatus,
    
    # Data structures
    Decision,
    Action,
    Metrics,
    CostReport,
    Risk,
    Anomaly,
    
    # Input/Output
    SupervisionInput,
    SummaryOutput,
    GPTAnalysis,
    ValidationResult,
    SupervisionOutput,
    
    # Config
    SupervisorConfig,
    
    # Helpers
    create_supervision_input,
    create_default_config,
)

# Summary Generator
from .global_summary_generator import (
    GlobalSummaryGenerator,
    create_summary_generator,
)

# GPT Supervisor
from .gpt_supervisor import (
    GPTSupervisor,
    create_gpt_supervisor,
)

# Gemini Validator
from .gemini_validator import (
    GeminiValidator,
    create_gemini_validator,
)

# Supervisor Orchestrator
from .supervisor_orchestrator import (
    SupervisorOrchestrator,
    create_supervisor_orchestrator,
)


__all__ = [
    # Enums (5)
    "SeverityLevel",
    "EngineSource",
    "DecisionType",
    "RiskType",
    "ValidationStatus",
    
    # Data structures (6)
    "Decision",
    "Action",
    "Metrics",
    "CostReport",
    "Risk",
    "Anomaly",
    
    # Input/Output (5)
    "SupervisionInput",
    "SummaryOutput",
    "GPTAnalysis",
    "ValidationResult",
    "SupervisionOutput",
    
    # Config (1)
    "SupervisorConfig",
    
    # Helpers (2)
    "create_supervision_input",
    "create_default_config",
    
    # Components (4)
    "GlobalSummaryGenerator",
    "GPTSupervisor",
    "GeminiValidator",
    "SupervisorOrchestrator",
    
    # Component helpers (4)
    "create_summary_generator",
    "create_gpt_supervisor",
    "create_gemini_validator",
    "create_supervisor_orchestrator",
]

# Total exports: 27
