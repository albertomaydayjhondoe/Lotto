"""Autonomous Variant Generator (PASO 10.17)"""
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID, uuid4
import random

from app.meta_creative_production.schemas import (
    CreativeProductionRequest, VariantGenerationConfig, GeneratedVariant,
    VariantGenerationResult, VariantType, NarrativeStructure
)

class AutonomousVariantGenerator:
    """
    Generates 5-15 creative variants per master creative.
    
    Features:
    - Fragment reordering based on performance (10.15)
    - Caption optimization using insights (10.7, 10.12)
    - Dynamic hashtags within approved rules
    - 3 duration variants: 5-7s (short), 8-12s (medium), 13-18s (long)
    - Multiple narrative structures
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
        
    async def generate_variants(
        self,
        request: CreativeProductionRequest,
        config: VariantGenerationConfig
    ) -> VariantGenerationResult:
        """Generate 5-15 variants for master creative"""
        start_time = datetime.utcnow()
        
        # Determine number of variants (5-15)
        num_variants = random.randint(config.min_variants, config.max_variants)
        
        variants: List[GeneratedVariant] = []
        fragment_ids = [f.fragment_id for f in request.fragments]
        
        for i in range(1, num_variants + 1):
            variant = await self._generate_single_variant(
                variant_number=i,
                master=request.master_creative,
                fragment_ids=fragment_ids,
                style_guide=request.style_guide,
                config=config
            )
            variants.append(variant)
        
        elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        if elapsed == 0:
            elapsed = 1  # Ensure non-zero for fast operations
        
        return VariantGenerationResult(
            master_creative_id=uuid4(),  # Would be from DB
            variants_generated=len(variants),
            variants=variants,
            generation_time_ms=elapsed,
            summary=f"Generated {len(variants)} variants with diverse structures"
        )
    
    async def _generate_single_variant(
        self,
        variant_number: int,
        master: Any,
        fragment_ids: List[UUID],
        style_guide: Any,
        config: VariantGenerationConfig
    ) -> GeneratedVariant:
        """Generate a single variant"""
        
        # Choose variant type
        variant_types = []
        if config.enable_fragment_reorder:
            variant_types.append(VariantType.FRAGMENT_REORDER)
        if config.enable_caption_optimization:
            variant_types.append(VariantType.CAPTION_OPTIMIZED)
        if config.enable_hashtag_variants:
            variant_types.append(VariantType.HASHTAG_VARIANT)
        
        # Duration variants
        if config.enable_short_duration and variant_number % 3 == 1:
            variant_types.append(VariantType.DURATION_SHORT)
        elif config.enable_medium_duration and variant_number % 3 == 2:
            variant_types.append(VariantType.DURATION_MEDIUM)
        elif config.enable_long_duration and variant_number % 3 == 0:
            variant_types.append(VariantType.DURATION_LONG)
        
        variant_type = random.choice(variant_types) if variant_types else VariantType.FRAGMENT_REORDER
        
        # Choose narrative structure
        structures = [
            NarrativeStructure.HOOK_BODY_CTA,
            NarrativeStructure.HOOK_INVERTED,
            NarrativeStructure.CTA_FORWARD
        ]
        narrative_structure = random.choice(structures)
        
        # Reorder fragments based on structure
        fragments_order = await self._reorder_fragments(fragment_ids, narrative_structure)
        
        # Generate duration based on variant type
        if variant_type == VariantType.DURATION_SHORT:
            duration = random.uniform(5, 7)
            duration_cat = "short"
        elif variant_type == VariantType.DURATION_MEDIUM:
            duration = random.uniform(8, 12)
            duration_cat = "medium"
        elif variant_type == VariantType.DURATION_LONG:
            duration = random.uniform(13, 18)
            duration_cat = "long"
        else:
            duration = master.duration_seconds
            duration_cat = "medium"
        
        # Generate caption
        caption = await self._generate_caption(master, style_guide, narrative_structure)
        
        # Generate hashtags
        hashtags = await self._generate_hashtags(master, style_guide)
        
        # Estimate score (would use 10.15 data in LIVE mode)
        estimated_score = random.uniform(60, 95)
        confidence = random.uniform(0.7, 0.95)
        
        return GeneratedVariant(
            variant_id=uuid4(),
            parent_id=uuid4(),
            variant_type=variant_type,
            narrative_structure=narrative_structure,
            fragments_order=fragments_order,
            caption=caption,
            hashtags=hashtags,
            text_overlay=None,
            duration_seconds=duration,
            color_lut="standard" if not config.enable_color_luts else random.choice(["standard", "warm", "cool", "vibrant"]),
            estimated_score=estimated_score,
            confidence=confidence,
            generated_at=datetime.utcnow(),
            mode=self.mode
        )
    
    async def _reorder_fragments(
        self,
        fragment_ids: List[UUID],
        structure: NarrativeStructure
    ) -> List[UUID]:
        """Reorder fragments based on narrative structure"""
        if self.mode == "stub":
            # STUB: Random reordering
            shuffled = fragment_ids.copy()
            random.shuffle(shuffled)
            return shuffled
        
        # LIVE: Query 10.15 for best performing fragments per structure
        # TODO: Implement query to MetaCreativeAnalyzer
        return fragment_ids
    
    async def _generate_caption(
        self,
        master: Any,
        style_guide: Any,
        structure: NarrativeStructure
    ) -> str:
        """Generate optimized caption"""
        if self.mode == "stub":
            # STUB: Template-based captions
            templates = [
                f"🔥 {master.title} - {style_guide.tone} vibes! Check it out ��",
                f"Transform your {master.genre} game with this! {' '.join(style_guide.vibes[:2])}",
                f"Don't miss out! {master.title} - {style_guide.aesthetic_reference}",
            ]
            return random.choice(templates)
        
        # LIVE: Query 10.7 (Insights) and 10.12 (Targeting) for best performing captions
        # TODO: Implement caption optimization using historical data
        return f"{master.title} - {style_guide.tone}"
    
    async def _generate_hashtags(
        self,
        master: Any,
        style_guide: Any
    ) -> List[str]:
        """Generate dynamic hashtags within approved rules"""
        if self.mode == "stub":
            # STUB: Genre + vibe based hashtags
            base_tags = [
                f"#{master.genre.lower()}",
                "#viral",
                "#trending"
            ]
            
            # Add vibe hashtags
            vibe_tags = [f"#{vibe.lower().replace(' ', '')}" for vibe in style_guide.vibes[:3]]
            
            return base_tags + vibe_tags
        
        # LIVE: Query approved hashtag rules from DB
        # TODO: Implement hashtag rule validation
        return [f"#{master.genre}"]
