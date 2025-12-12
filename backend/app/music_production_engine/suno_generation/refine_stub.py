"""Suno Refinement Stub

Mock implementation of iterative music refinement using Suno API.
Simulates improvement cycles without real generation.
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from .generator_stub import GenerationResult, SunoGeneratorStub


class RefineParams(BaseModel):
    """Parameters for refinement request."""
    base_generation_id: str
    improvements: List[str]  # Specific changes to make
    context: Optional[Dict] = None  # Analysis results, feedback, etc.
    preserve_structure: bool = True
    iteration_number: int = 1


class RefinementHistory(BaseModel):
    """History entry for refinement chain."""
    iteration: int
    generation_id: str
    improvements_requested: List[str]
    quality_score: float
    timestamp: datetime


class SunoRefineStub:
    """
    Mock Suno refinement engine.
    
    Simulates iterative improvement workflow:
    - Takes previous generation + improvement requests
    - Returns new generation with incremental quality boost
    - Maintains refinement history
    - Calculates quality scores
    """
    
    def __init__(self, generator: Optional[SunoGeneratorStub] = None):
        """
        Initialize refiner.
        
        Args:
            generator: SunoGeneratorStub instance (created if not provided)
        """
        self.generator = generator or SunoGeneratorStub()
        self._refinement_chains: Dict[str, List[RefinementHistory]] = {}
    
    async def refine(self, params: RefineParams) -> GenerationResult:
        """
        Refine existing generation with improvements.
        
        Args:
            params: Refinement parameters
            
        Returns:
            New GenerationResult representing refined version
        """
        # Simulate refinement processing time (30-50ms)
        await asyncio.sleep(0.04)
        
        # Generate new ID for refined version
        refinement_hash = hashlib.md5(
            f"{params.base_generation_id}_iter{params.iteration_number}".encode()
        ).hexdigest()[:12]
        refined_id = f"suno_refined_{refinement_hash}"
        
        # Calculate quality improvement (STUB: +2-5 points per iteration, max 95)
        base_quality = self._get_base_quality(params.base_generation_id)
        improvement = min(3, 95 - base_quality)  # Diminishing returns
        new_quality = min(95, base_quality + improvement)
        
        # Build metadata
        metadata = {
            "base_generation_id": params.base_generation_id,
            "iteration_number": params.iteration_number,
            "improvements_applied": params.improvements,
            "quality_score": new_quality,
            "refinement_date": datetime.utcnow().isoformat(),
            "context_used": bool(params.context),
        }
        
        # Add context insights if provided
        if params.context:
            metadata["context_summary"] = {
                "audio_score": params.context.get("audio_analysis", {}).get("overall_score", 0),
                "lyric_issues": len(params.context.get("lyric_analysis", {}).get("issues", [])),
                "flow_score": params.context.get("flow_analysis", {}).get("complexity_score", 0),
            }
        
        # Store refinement history
        self._add_to_history(
            base_id=params.base_generation_id,
            refined_id=refined_id,
            params=params,
            quality=new_quality
        )
        
        # Generate result
        result = GenerationResult(
            id=refined_id,
            status="complete",
            audio_url=f"https://cdn1.suno.ai/audio/{refined_id}.mp3",
            video_url=f"https://cdn1.suno.ai/video/{refined_id}.mp4",
            metadata=metadata,
            duration_seconds=180,
            created_at=datetime.utcnow()
        )
        
        return result
    
    def get_refinement_history(self, base_id: str) -> List[RefinementHistory]:
        """
        Get full refinement chain for a base generation.
        
        Args:
            base_id: Original generation ID
            
        Returns:
            List of RefinementHistory entries
        """
        return self._refinement_chains.get(base_id, [])
    
    def get_quality_progression(self, base_id: str) -> List[float]:
        """
        Get quality scores across all iterations.
        
        Args:
            base_id: Original generation ID
            
        Returns:
            List of quality scores in order
        """
        history = self.get_refinement_history(base_id)
        return [entry.quality_score for entry in history]
    
    def should_continue_refining(
        self,
        base_id: str,
        target_quality: float = 85.0,
        max_iterations: int = 5
    ) -> bool:
        """
        Determine if more refinement iterations are recommended.
        
        Args:
            base_id: Base generation ID
            target_quality: Target quality threshold
            max_iterations: Maximum allowed iterations
            
        Returns:
            True if should continue, False if should stop
        """
        history = self.get_refinement_history(base_id)
        
        if not history:
            return True  # No iterations yet
        
        if len(history) >= max_iterations:
            return False  # Hit max iterations
        
        latest_quality = history[-1].quality_score
        if latest_quality >= target_quality:
            return False  # Reached target quality
        
        # Check for diminishing returns (< 1 point improvement in last 2 iterations)
        if len(history) >= 3:
            recent_scores = [h.quality_score for h in history[-3:]]
            if recent_scores[-1] - recent_scores[0] < 2.0:
                return False  # Plateaued
        
        return True
    
    async def refine_batch(
        self,
        base_ids: List[str],
        improvements: List[str],
        iteration_number: int
    ) -> List[GenerationResult]:
        """
        Refine multiple generations in parallel.
        
        Args:
            base_ids: List of base generation IDs
            improvements: Common improvements to apply
            iteration_number: Current iteration
            
        Returns:
            List of refined GenerationResults
        """
        tasks = [
            self.refine(RefineParams(
                base_generation_id=base_id,
                improvements=improvements,
                iteration_number=iteration_number
            ))
            for base_id in base_ids
        ]
        
        return await asyncio.gather(*tasks)
    
    def _get_base_quality(self, generation_id: str) -> float:
        """
        Get quality score for generation.
        
        In STUB mode, derives from ID hash for consistency.
        
        Args:
            generation_id: Generation ID
            
        Returns:
            Quality score (70-80 for base, higher for refined)
        """
        # Check if this is a refined version
        history = self.get_refinement_history(generation_id)
        if history:
            return history[-1].quality_score
        
        # Base generation: 70-80 range
        id_hash = hash(generation_id)
        return 70 + (id_hash % 11)
    
    def _add_to_history(
        self,
        base_id: str,
        refined_id: str,
        params: RefineParams,
        quality: float
    ) -> None:
        """Add entry to refinement history."""
        if base_id not in self._refinement_chains:
            self._refinement_chains[base_id] = []
        
        entry = RefinementHistory(
            iteration=params.iteration_number,
            generation_id=refined_id,
            improvements_requested=params.improvements,
            quality_score=quality,
            timestamp=datetime.utcnow()
        )
        
        self._refinement_chains[base_id].append(entry)
    
    def get_stats(self) -> Dict:
        """Get refinement statistics."""
        total_chains = len(self._refinement_chains)
        total_refinements = sum(len(chain) for chain in self._refinement_chains.values())
        
        avg_iterations = (
            total_refinements / total_chains
            if total_chains > 0
            else 0
        )
        
        return {
            "total_refinement_chains": total_chains,
            "total_refinements": total_refinements,
            "avg_iterations_per_chain": round(avg_iterations, 2),
            "stub_mode": True
        }


# Factory function
def get_suno_refiner(generator: Optional[SunoGeneratorStub] = None) -> SunoRefineStub:
    """
    Get Suno refiner instance.
    
    Args:
        generator: Optional SunoGeneratorStub instance
        
    Returns:
        SunoRefineStub instance
    """
    return SunoRefineStub(generator=generator)
