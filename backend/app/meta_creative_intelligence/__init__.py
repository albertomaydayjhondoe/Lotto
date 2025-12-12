"""
Meta Creative Intelligence & Lifecycle System (PASO 10.13)

Sistema completo de inteligencia creativa que integra:
1. Creative Intelligence Layer - Análisis visual con YOLO/CV
2. Creative Variant Generator - Generación automática de variantes
3. Publication Winner Engine - Selección de ganadores por performance
4. Thumbnail Generator - Auto-thumbnailing inteligente
5. Creative Lifecycle Manager - Gestión del ciclo de vida y fatigue

Integrado con:
- ROAS Engine (10.5)
- A/B Testing (10.4)
- Targeting Optimizer (10.12)
- Insights Collector (10.7)
- Full Cycle (10.11)
"""

from app.meta_creative_intelligence.models import (
    MetaCreativeAnalysisModel,
    MetaCreativeVariantGenerationModel,
    MetaPublicationWinnerModel,
    MetaThumbnailModel,
    MetaCreativeLifecycleModel,
)
from app.meta_creative_intelligence.orchestrator import MetaCreativeIntelligenceOrchestrator
from app.meta_creative_intelligence.visual_analyzer import VisualAnalyzer
from app.meta_creative_intelligence.variant_generator import VariantGenerator
from app.meta_creative_intelligence.winner_engine import WinnerEngine
from app.meta_creative_intelligence.thumbnail_generator import ThumbnailGenerator
from app.meta_creative_intelligence.lifecycle_manager import LifecycleManager

__all__ = [
    "MetaCreativeAnalysisModel",
    "MetaCreativeVariantGenerationModel",
    "MetaPublicationWinnerModel",
    "MetaThumbnailModel",
    "MetaCreativeLifecycleModel",
    "MetaCreativeIntelligenceOrchestrator",
    "VisualAnalyzer",
    "VariantGenerator",
    "WinnerEngine",
    "ThumbnailGenerator",
    "LifecycleManager",
]
