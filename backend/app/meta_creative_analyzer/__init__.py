"""
Meta Creative Analyzer (PASO 10.15)

Sistema autónomo de análisis de creativos que detecta fatiga,
recombina variantes y ofrece sugerencias automáticas de mejora.
"""

from app.meta_creative_analyzer.models import (
    MetaCreativeAnalysisModel,
    MetaCreativeVariantModel,
    MetaCreativeHealthLogModel,
)

from app.meta_creative_analyzer.core import CreativeIntelligenceCore
from app.meta_creative_analyzer.variant_generator import CreativeVariantGenerator
from app.meta_creative_analyzer.recombination import CreativeRecombinationEngine
from app.meta_creative_analyzer.fatigue import FatigueDetector

__all__ = [
    # Models
    "MetaCreativeAnalysisModel",
    "MetaCreativeVariantModel",
    "MetaCreativeHealthLogModel",
    # Core components
    "CreativeIntelligenceCore",
    "CreativeVariantGenerator",
    "CreativeRecombinationEngine",
    "FatigueDetector",
]
