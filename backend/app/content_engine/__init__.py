"""
Content Engine - Sprint 1, Módulo 7 + Sprint 3 Integration
Orquestador de generación de contenido inteligente para Stakazo.

Responsabilidades:
- Análisis de video (técnico y de tendencias)
- Generación de hooks y captions vía LLM
- Validación de contenido generado
- Telemetría y cost control
- Integración con Brain/Orchestrator
- Selección inteligente de clips basada en metadata visual (Sprint 3)

Version: 1.1.0
Status: Production-ready
Cost Target: <10€/mes
"""

from .orchestrator import ContentEngineOrchestrator
from .models import (
    ContentAnalysisRequest,
    ContentAnalysisResponse,
    VideoAnalysisResult,
    GeneratedContent,
    ContentMetrics
)
from .config import ContentEngineConfig
from .clip_selector import ClipSelector, create_clip_selector

__version__ = "1.1.0"

__all__ = [
    "ContentEngineOrchestrator",
    "ContentAnalysisRequest",
    "ContentAnalysisResponse",
    "VideoAnalysisResult",
    "GeneratedContent",
    "ContentMetrics",
    "ContentEngineConfig",
    "ClipSelector",
    "create_clip_selector",
]
