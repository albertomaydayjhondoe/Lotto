"""Generation Cycle Manager

Orchestrates complete generation → analysis → refinement cycles.
Manages iteration limits, quality thresholds, and decision logic.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

from .generator_stub import GenerationParams, GenerationResult, SunoGeneratorStub
from .refine_stub import RefineParams, SunoRefineStub


class CycleStatus(str, Enum):
    """Status of generation cycle."""
    INITIALIZING = "initializing"
    GENERATING = "generating"
    ANALYZING = "analyzing"
    REFINING = "refining"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CycleConfig(BaseModel):
    """Configuration for generation cycle."""
    max_iterations: int = 5
    target_quality: float = 85.0
    min_improvement_threshold: float = 2.0
    auto_refine: bool = True
    quality_gates: Dict[str, float] = {
        "audio_analysis": 75.0,
        "lyric_quality": 70.0,
        "flow_complexity": 65.0,
    }


class CycleResult(BaseModel):
    """Complete cycle result."""
    cycle_id: str
    status: CycleStatus
    iterations_completed: int
    final_generation: Optional[GenerationResult] = None
    final_quality_score: float
    all_versions: List[str]  # Generation IDs
    analysis_results: List[Dict]
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict


class GenerationCycleManager:
    """
    Manages complete generation lifecycle.
    
    Flow:
    1. Initial generation from prompt
    2. Multi-engine analysis
    3. Quality assessment
    4. Refinement decision
    5. Iterative improvement
    6. Finalization
    """
    
    def __init__(
        self,
        generator: Optional[SunoGeneratorStub] = None,
        refiner: Optional[SunoRefineStub] = None,
        config: Optional[CycleConfig] = None
    ):
        """
        Initialize cycle manager.
        
        Args:
            generator: SunoGeneratorStub instance
            refiner: SunoRefineStub instance
            config: Cycle configuration
        """
        self.generator = generator or SunoGeneratorStub()
        self.refiner = refiner or SunoRefineStub(self.generator)
        self.config = config or CycleConfig()
        
        self._active_cycles: Dict[str, CycleResult] = {}
    
    async def run_cycle(
        self,
        initial_prompt: str,
        generation_params: Optional[GenerationParams] = None,
        context: Optional[Dict] = None
    ) -> CycleResult:
        """
        Execute complete generation cycle.
        
        Args:
            initial_prompt: Text prompt for initial generation
            generation_params: Optional generation parameters
            context: Optional context (user preferences, session data, etc.)
            
        Returns:
            CycleResult with all iterations and final output
        """
        # Initialize cycle
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        cycle = CycleResult(
            cycle_id=cycle_id,
            status=CycleStatus.INITIALIZING,
            iterations_completed=0,
            final_quality_score=0.0,
            all_versions=[],
            analysis_results=[],
            started_at=datetime.utcnow(),
            metadata={"initial_prompt": initial_prompt}
        )
        
        self._active_cycles[cycle_id] = cycle
        
        try:
            # Phase 1: Initial Generation
            cycle.status = CycleStatus.GENERATING
            
            if not generation_params:
                generation_params = GenerationParams(prompt=initial_prompt)
            
            current_generation = await self.generator.generate(generation_params)
            cycle.all_versions.append(current_generation.id)
            cycle.final_generation = current_generation
            
            # Phase 2: Analysis Loop
            for iteration in range(1, self.config.max_iterations + 1):
                cycle.status = CycleStatus.ANALYZING
                cycle.iterations_completed = iteration
                
                # Mock analysis (in real system, calls audio_analysis, lyric_flow_engine, etc.)
                analysis = await self._analyze_generation(current_generation, context)
                cycle.analysis_results.append(analysis)
                
                quality_score = analysis["overall_score"]
                cycle.final_quality_score = quality_score
                
                # Check if we should continue
                should_continue = self._should_continue_iteration(
                    quality_score=quality_score,
                    iteration=iteration,
                    analysis=analysis
                )
                
                if not should_continue:
                    cycle.status = CycleStatus.COMPLETE
                    cycle.completed_at = datetime.utcnow()
                    break
                
                # Phase 3: Refinement
                if self.config.auto_refine:
                    cycle.status = CycleStatus.REFINING
                    
                    improvements = self._extract_improvements(analysis)
                    
                    refine_params = RefineParams(
                        base_generation_id=current_generation.id,
                        improvements=improvements,
                        context={"analysis": analysis, "user_context": context},
                        iteration_number=iteration + 1
                    )
                    
                    current_generation = await self.refiner.refine(refine_params)
                    cycle.all_versions.append(current_generation.id)
                    cycle.final_generation = current_generation
            
            # Finalize
            if cycle.status != CycleStatus.COMPLETE:
                cycle.status = CycleStatus.COMPLETE
                cycle.completed_at = datetime.utcnow()
            
        except Exception as e:
            cycle.status = CycleStatus.FAILED
            cycle.completed_at = datetime.utcnow()
            cycle.metadata["error"] = str(e)
        
        return cycle
    
    def get_cycle(self, cycle_id: str) -> Optional[CycleResult]:
        """Retrieve cycle by ID."""
        return self._active_cycles.get(cycle_id)
    
    async def cancel_cycle(self, cycle_id: str) -> bool:
        """
        Cancel active cycle.
        
        Args:
            cycle_id: Cycle to cancel
            
        Returns:
            True if cancelled, False if not found/already complete
        """
        cycle = self._active_cycles.get(cycle_id)
        if not cycle or cycle.status in [CycleStatus.COMPLETE, CycleStatus.FAILED]:
            return False
        
        cycle.status = CycleStatus.CANCELLED
        cycle.completed_at = datetime.utcnow()
        return True
    
    async def _analyze_generation(
        self,
        generation: GenerationResult,
        context: Optional[Dict]
    ) -> Dict:
        """
        Run all analysis engines on generation.
        
        In STUB mode, returns mock analysis results.
        In production, orchestrates: audio_analysis, lyric_flow_engine,
        hit_decision_engine, etc.
        
        Args:
            generation: Generation to analyze
            context: Optional context
            
        Returns:
            Combined analysis results
        """
        await asyncio.sleep(0.02)  # Simulate analysis time
        
        # Mock analysis scores (deterministic based on generation ID)
        id_hash = hash(generation.id)
        
        audio_score = 70 + (id_hash % 20)
        lyric_score = 65 + (id_hash % 25)
        flow_score = 68 + (id_hash % 22)
        
        # Overall score is weighted average
        overall = (audio_score * 0.4 + lyric_score * 0.3 + flow_score * 0.3)
        
        return {
            "generation_id": generation.id,
            "audio_analysis": {
                "overall_score": audio_score,
                "clarity": audio_score + 2,
                "energy": audio_score - 3,
                "production_quality": audio_score + 1,
            },
            "lyric_analysis": {
                "quality_score": lyric_score,
                "issues": [] if lyric_score > 80 else ["Minor rhyme inconsistency"],
                "strengths": ["Strong metaphors", "Good rhythm"],
            },
            "flow_analysis": {
                "complexity_score": flow_score,
                "syllable_density": 4.2,
                "variation": 7.5,
            },
            "overall_score": round(overall, 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _should_continue_iteration(
        self,
        quality_score: float,
        iteration: int,
        analysis: Dict
    ) -> bool:
        """
        Decide if another iteration is warranted.
        
        Args:
            quality_score: Current overall quality
            iteration: Current iteration number
            analysis: Latest analysis results
            
        Returns:
            True if should continue, False if should finalize
        """
        # Hit max iterations
        if iteration >= self.config.max_iterations:
            return False
        
        # Hit target quality
        if quality_score >= self.config.target_quality:
            return False
        
        # Check quality gates
        audio_score = analysis.get("audio_analysis", {}).get("overall_score", 0)
        if audio_score < self.config.quality_gates["audio_analysis"]:
            return True  # Audio needs work
        
        lyric_score = analysis.get("lyric_analysis", {}).get("quality_score", 0)
        if lyric_score < self.config.quality_gates["lyric_quality"]:
            return True  # Lyrics need work
        
        # All gates passed but below target - one more iteration
        return iteration < 3
    
    def _extract_improvements(self, analysis: Dict) -> List[str]:
        """
        Extract actionable improvements from analysis.
        
        Args:
            analysis: Analysis results
            
        Returns:
            List of improvement instructions
        """
        improvements = []
        
        audio_score = analysis.get("audio_analysis", {}).get("overall_score", 100)
        if audio_score < 80:
            improvements.append("Improve audio clarity and production quality")
        
        lyric_issues = analysis.get("lyric_analysis", {}).get("issues", [])
        if lyric_issues:
            improvements.extend([f"Fix: {issue}" for issue in lyric_issues])
        
        flow_score = analysis.get("flow_analysis", {}).get("complexity_score", 100)
        if flow_score < 70:
            improvements.append("Enhance flow complexity and variation")
        
        if not improvements:
            improvements.append("Polish overall production and performance")
        
        return improvements
    
    def get_cycle_stats(self) -> Dict:
        """Get statistics across all cycles."""
        total_cycles = len(self._active_cycles)
        
        if total_cycles == 0:
            return {
                "total_cycles": 0,
                "avg_iterations": 0,
                "avg_quality": 0,
                "completion_rate": 0,
            }
        
        completed = [c for c in self._active_cycles.values() if c.status == CycleStatus.COMPLETE]
        
        avg_iterations = (
            sum(c.iterations_completed for c in completed) / len(completed)
            if completed else 0
        )
        
        avg_quality = (
            sum(c.final_quality_score for c in completed) / len(completed)
            if completed else 0
        )
        
        return {
            "total_cycles": total_cycles,
            "completed_cycles": len(completed),
            "avg_iterations": round(avg_iterations, 2),
            "avg_quality": round(avg_quality, 2),
            "completion_rate": round(len(completed) / total_cycles * 100, 1),
        }


# Factory function
def get_cycle_manager(config: Optional[CycleConfig] = None) -> GenerationCycleManager:
    """
    Get cycle manager instance.
    
    Args:
        config: Optional cycle configuration
        
    Returns:
        GenerationCycleManager instance
    """
    return GenerationCycleManager(config=config)
