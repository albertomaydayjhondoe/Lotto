"""Creative Variant Generator (PASO 10.15)"""
import uuid, random
from datetime import datetime
from uuid import UUID
from typing import List
from app.meta_creative_analyzer.schemas import CreativeVariant, VariantChange

class CreativeVariantGenerator:
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def generate_variants(
        self, base_creative_id: UUID, num_variants: int = 5, strategy: str = "balanced"
    ) -> List[CreativeVariant]:
        """Generate creative variants. STUB mode generates synthetic variants."""
        if self.mode == "stub":
            return await self._generate_variants_stub(base_creative_id, num_variants, strategy)
        # TODO LIVE: Integrate with PASO 10.17 for real variant generation
        raise NotImplementedError("LIVE mode requires creative generation API")
    
    async def _generate_variants_stub(
        self, base_creative_id: UUID, num_variants: int, strategy: str
    ) -> List[CreativeVariant]:
        """Stub variant generation."""
        variants = []
        improvement_base = 5 if strategy == "conservative" else 15 if strategy == "aggressive" else 10
        
        for i in range(1, num_variants + 1):
            changes = self._generate_changes_stub(i, strategy)
            est_improvement = improvement_base + random.uniform(-5, 15)
            confidence = 0.6 + random.uniform(0, 0.3)
            
            variants.append(CreativeVariant(
                variant_id=uuid.uuid4(), base_creative_id=base_creative_id,
                variant_number=i, changes=changes, estimated_improvement=est_improvement,
                confidence=confidence, generated_at=datetime.utcnow(), mode="stub"
            ))
        return variants
    
    def _generate_changes_stub(self, variant_num: int, strategy: str) -> List[VariantChange]:
        """Generate synthetic changes for variant."""
        changes = []
        # Copy variations
        if variant_num % 2 == 1:
            changes.append(VariantChange(
                change_type="copy", original="Get 50% OFF today!", 
                modified="Limited time: 50% OFF ends soon!", 
                reasoning="Added urgency and scarcity"
            ))
        # Title variations
        if variant_num % 3 == 0:
            changes.append(VariantChange(
                change_type="title", original="Amazing Product", 
                modified="Transform Your Life with Amazing Product",
                reasoning="Added emotional benefit"
            ))
        # Thumbnail variations (for video)
        if variant_num % 2 == 0:
            changes.append(VariantChange(
                change_type="thumbnail", original="frame_120.jpg",
                modified="frame_180.jpg", reasoning="Selected frame with face"
            ))
        return changes if changes else [VariantChange(
            change_type="copy", original="Base copy", modified="Optimized copy",
            reasoning="General optimization"
        )]
