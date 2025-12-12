"""
Brand Engine - STAKAZO Sprint 4

Sistema de aprendizaje automático de identidad artística oficial.

El Brand Engine NO tiene presets ni estética predefinida.
TODO se aprende exclusivamente de:
1. Interrogatorio al artista (Brand Interrogator)
2. Métricas reales de contenido (Brand Metrics Analyzer)
3. Análisis visual de contenido real (Brand Aesthetic Extractor)
4. Feedback final del artista

Output: BRAND_STATIC_RULES.json (reglas oficiales del canal principal)

Importante:
- CANAL OFICIAL: Sigue estrictamente BRAND_STATIC_RULES.json
- CUENTAS SATÉLITE: NO siguen estas reglas (experimentación/ML/viralización)
"""

__version__ = "1.0.0"

from .models import (
    BrandProfile,
    MetricInsights,
    AestheticDNA,
    BrandStaticRules,
    InterrogationQuestion,
    InterrogationResponse,
)
from .brand_interrogator import BrandInterrogator
from .brand_metrics import BrandMetricsAnalyzer
from .brand_aesthetic_extractor import BrandAestheticExtractor
from .brand_rules_builder import BrandRulesBuilder

__all__ = [
    "BrandProfile",
    "MetricInsights",
    "AestheticDNA",
    "BrandStaticRules",
    "InterrogationQuestion",
    "InterrogationResponse",
    "BrandInterrogator",
    "BrandMetricsAnalyzer",
    "BrandAestheticExtractor",
    "BrandRulesBuilder",
]
