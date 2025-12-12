"""Creative Recombination Engine (PASO 10.15)"""
import uuid, random
from datetime import datetime
from uuid import UUID
from typing import List, Dict
from app.meta_creative_analyzer.schemas import (
    RecombinationResult, CreativeVariant, CreativeFragment, VariantChange
)

class CreativeRecombinationEngine:
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def recombine(
        self, creative_ids: List[UUID], num_variants: int = 5, strategy: str = "balanced"
    ) -> RecombinationResult:
        """Recombine fragments from multiple creatives to generate new variants."""
        start_time = datetime.utcnow()
        
        # Extract best fragments
        best_fragments = await self._extract_best_fragments(creative_ids)
        
        # Generate variants
        variants = await self._generate_recombined_variants(
            creative_ids, best_fragments, num_variants, strategy
        )
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return RecombinationResult(
            recombination_id=uuid.uuid4(), base_creative_ids=creative_ids,
            generated_variants=variants, best_fragments=best_fragments,
            recombination_strategy=strategy, total_variants=len(variants),
            processing_time_ms=processing_time
        )
    
    async def _extract_best_fragments(self, creative_ids: List[UUID]) -> Dict[str, CreativeFragment]:
        """Extract best performing fragments (STUB mode)."""
        return {
            "intro": CreativeFragment(
                fragment_type="intro", content="Attention-grabbing intro",
                performance_score=85.0, usage_count=5
            ),
            "body": CreativeFragment(
                fragment_type="body", content="Value proposition body",
                performance_score=78.0, usage_count=8
            ),
            "cta": CreativeFragment(
                fragment_type="cta", content="Shop Now - Limited Time!",
                performance_score=92.0, usage_count=12
            ),
        }
    
    async def _generate_recombined_variants(
        self, base_ids: List[UUID], fragments: Dict[str, CreativeFragment],
        num_variants: int, strategy: str
    ) -> List[CreativeVariant]:
        """Generate variants by recombining fragments."""
        variants = []
        for i in range(1, num_variants + 1):
            changes = [VariantChange(
                change_type="fragment_order",
                original="intro→body→cta",
                modified=f"intro({fragments['intro'].content[:20]})→body→cta({fragments['cta'].content[:20]})",
                reasoning="Recombined top-performing fragments"
            )]
            variants.append(CreativeVariant(
                variant_id=uuid.uuid4(), base_creative_id=base_ids[0],
                variant_number=i, changes=changes,
                estimated_improvement=10.0 + random.uniform(0, 20),
                confidence=0.7 + random.uniform(0, 0.2),
                generated_at=datetime.utcnow(), mode="stub"
            ))
        return variants
