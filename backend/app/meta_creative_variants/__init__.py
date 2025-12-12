"""
Meta Ads Creative Variants Engine (PASO 10.10)

Sistema automático para generar variantes creativas de anuncios en Meta Ads.
Genera combinaciones de video, texto, thumbnails y CTA para A/B testing.

Componentes:
- schemas.py: Pydantic models para requests/responses
- models.py: SQLAlchemy models para DB persistence
- extractor.py: Extrae material creativo de clips/videos
- generator.py: Genera variantes (video/text/thumbnail)
- uploader.py: Sube creatives a Meta Ads API
- engine.py: Lógica completa de generación
- scheduler.py: Background job (cada 6h)
- router.py: REST API endpoints con RBAC

Uso:
    from app.meta_creative_variants import CreativeVariantsEngine
    
    engine = CreativeVariantsEngine(db)
    variants = await engine.generate_variants(
        clip_id="clip_123",
        campaign_id="23847656789012340",
        num_variants=10
    )
"""

from app.meta_creative_variants.schemas import (
    VideoVariant,
    TextVariant,
    ThumbnailVariant,
    CreativeVariant,
    GenerateVariantsRequest,
    GenerateVariantsResponse,
    VariantStatus,
    CropRatio,
)

from app.meta_creative_variants.engine import CreativeVariantsEngine

__all__ = [
    "CreativeVariantsEngine",
    "VideoVariant",
    "TextVariant",
    "ThumbnailVariant",
    "CreativeVariant",
    "GenerateVariantsRequest",
    "GenerateVariantsResponse",
    "VariantStatus",
    "CropRatio",
]
