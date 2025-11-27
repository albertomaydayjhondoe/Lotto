"""
Meta Ads Full Autonomous Creative Production Engine (PASO 10.17)

Complete autonomous creative generation system with:
- Variant generation (5-15 per creative)
- Fragment recombination (Hook→Body→CTA structures)
- Auto-upload to Meta Ads
- Fatigue monitoring and refresh
- Continuous production loop (12h cycle)

Integrates with: 10.2, 10.3, 10.5, 10.7, 10.9, 10.12, 10.15, 10.16
"""

from app.meta_creative_production.models import (
    MetaCreativeProductionModel,
    MetaCreativeVariantModel,
    MetaCreativeFragmentModel,
    MetaCreativePromotionLogModel,
)

__all__ = [
    "MetaCreativeProductionModel",
    "MetaCreativeVariantModel",
    "MetaCreativeFragmentModel",
    "MetaCreativePromotionLogModel",
]
