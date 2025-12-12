"""Creative Recombination Engine (PASO 10.17)"""
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import random

from app.meta_creative_production.schemas import (
    RecombinationRequest, RecombinationResult, RecombinedCreative,
    NarrativeStructure
)

class CreativeRecombinationEngine:
    """
    Extracts best fragments and tests narrative structures.
    
    Structures:
    - Hook → Body → CTA (standard)
    - Hook invertido (CTA first)
    - CTA adelantado (CTA at beginning)
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def recombine_fragments(
        self,
        request: RecombinationRequest
    ) -> RecombinationResult:
        """Create recombined variants using best fragments"""
        start_time = datetime.utcnow()
        
        # Get best fragments (from 10.15 in LIVE mode)
        best_fragments = await self._extract_best_fragments(request.master_creative_id)
        
        recombinations: List[RecombinedCreative] = []
        
        for structure in request.narrative_structures:
            for i in range(request.min_recombinations):
                recombined = await self._create_recombination(
                    parent_id=request.master_creative_id,
                    fragments=best_fragments,
                    structure=structure
                )
                recombinations.append(recombined)
        
        # Detect best structure
        best_structure = await self._detect_best_structure(recombinations)
        
        elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        if elapsed == 0:
            elapsed = 1  # Ensure non-zero
        
        return RecombinationResult(
            master_creative_id=request.master_creative_id,
            recombinations_created=len(recombinations),
            recombinations=recombinations,
            best_structure=best_structure,
            processing_time_ms=elapsed
        )
    
    async def _extract_best_fragments(
        self,
        master_id: UUID
    ) -> Dict[str, List[UUID]]:
        """Extract best performing fragments from 10.15"""
        if self.mode == "stub":
            # STUB: Generate synthetic fragments
            return {
                "hook": [uuid4(), uuid4()],
                "body": [uuid4(), uuid4(), uuid4()],
                "cta": [uuid4(), uuid4()],
                "outro": [uuid4()]
            }
        
        # LIVE: Query MetaCreativeAnalyzer (10.15) for top fragments
        # TODO: Implement query to get fragments sorted by performance_score
        return {}
    
    async def _create_recombination(
        self,
        parent_id: UUID,
        fragments: Dict[str, List[UUID]],
        structure: NarrativeStructure
    ) -> RecombinedCreative:
        """Create a single recombination"""
        
        # Select fragments based on structure
        if structure == NarrativeStructure.HOOK_BODY_CTA:
            # Standard: Hook → Body → CTA
            fragments_used = [
                random.choice(fragments.get("hook", [uuid4()])),
                *random.sample(fragments.get("body", [uuid4()]), min(2, len(fragments.get("body", [uuid4()])))),
                random.choice(fragments.get("cta", [uuid4()]))
            ]
        elif structure == NarrativeStructure.HOOK_INVERTED:
            # Inverted: CTA → Body → Hook
            fragments_used = [
                random.choice(fragments.get("cta", [uuid4()])),
                *random.sample(fragments.get("body", [uuid4()]), min(2, len(fragments.get("body", [uuid4()])))),
                random.choice(fragments.get("hook", [uuid4()]))
            ]
        else:  # CTA_FORWARD
            # CTA forward: CTA → Hook → Body
            fragments_used = [
                random.choice(fragments.get("cta", [uuid4()])),
                random.choice(fragments.get("hook", [uuid4()])),
                *random.sample(fragments.get("body", [uuid4()]), min(2, len(fragments.get("body", [uuid4()])))),
            ]
        
        # Estimate improvement (would use 10.16 data in LIVE mode)
        estimated_improvement = random.uniform(10, 40)  # % improvement
        confidence = random.uniform(0.65, 0.90)
        
        return RecombinedCreative(
            recombined_id=uuid4(),
            parent_id=parent_id,
            narrative_structure=structure,
            fragments_used=fragments_used,
            hook_fragment_id=fragments_used[0] if structure == NarrativeStructure.HOOK_BODY_CTA else None,
            body_fragments=[fragments_used[1], fragments_used[2]] if len(fragments_used) > 2 else [],
            cta_fragment_id=fragments_used[-1] if structure == NarrativeStructure.HOOK_BODY_CTA else None,
            estimated_improvement=estimated_improvement,
            confidence=confidence,
            caption=f"Recombined with {structure.value} structure",
            hashtags=["#recombined", f"#{structure.value}"],
            duration_seconds=random.uniform(8, 15),
            recombined_at=datetime.utcnow()
        )
    
    async def _detect_best_structure(
        self,
        recombinations: List[RecombinedCreative]
    ) -> NarrativeStructure:
        """Detect best performing narrative structure"""
        if self.mode == "stub":
            # STUB: Random selection
            return random.choice(list(NarrativeStructure))
        
        # LIVE: Query 10.16 (Creative Optimizer) for structure performance
        # TODO: Analyze performance by structure from MetaCreativeOptimizer
        return NarrativeStructure.HOOK_BODY_CTA
