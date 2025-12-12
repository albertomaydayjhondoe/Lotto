"""Audio Quality Scoring Engine

Aggregates results from all analysis engines into unified quality scores.
Provides holistic assessment and improvement recommendations.
"""

import asyncio
from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum


class QualityCategory(str, Enum):
    """Quality assessment categories."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 75-89
    ACCEPTABLE = "acceptable"  # 60-74
    NEEDS_IMPROVEMENT = "needs_improvement"  # 40-59
    POOR = "poor"  # 0-39


class ComponentScore(BaseModel):
    """Individual component score."""
    component: str
    score: float  # 0-100
    weight: float  # Contribution to overall score
    issues: List[str]
    strengths: List[str]


class QualityScore(BaseModel):
    """Complete quality assessment."""
    overall_score: float  # 0-100
    category: QualityCategory
    component_scores: List[ComponentScore]
    recommendations: List[str]
    priority_improvements: List[str]
    metadata: Dict


class ScoringEngine:
    """
    Aggregate audio analysis into unified quality scores.
    
    Combines:
    - Spectral quality (Essentia)
    - Production quality (Demucs stem separation)
    - Pitch accuracy (CREPE)
    - Feature quality (Librosa)
    - Perceptual quality (VGGish)
    - Structure quality (StructureAnalyzer)
    """
    
    # Weights for each component (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "spectral_quality": 0.20,
        "production_quality": 0.25,
        "pitch_accuracy": 0.15,
        "feature_quality": 0.15,
        "perceptual_quality": 0.10,
        "structure_quality": 0.15,
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize scoring engine.
        
        Args:
            weights: Custom component weights (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    async def score(
        self,
        analysis_results: Dict,
        context: Optional[Dict] = None
    ) -> QualityScore:
        """
        Calculate comprehensive quality score.
        
        Args:
            analysis_results: Combined results from all analysis engines
            context: Optional context (genre, target audience, etc.)
            
        Returns:
            QualityScore with overall assessment
        """
        # Simulate aggregation time
        await asyncio.sleep(0.02)
        
        # Score each component
        component_scores = []
        
        # Spectral Quality (from Essentia)
        spectral = self._score_spectral_quality(
            analysis_results.get("essentia", {})
        )
        component_scores.append(spectral)
        
        # Production Quality (from Demucs)
        production = self._score_production_quality(
            analysis_results.get("demucs", {})
        )
        component_scores.append(production)
        
        # Pitch Accuracy (from CREPE)
        pitch = self._score_pitch_accuracy(
            analysis_results.get("crepe", {})
        )
        component_scores.append(pitch)
        
        # Feature Quality (from Librosa)
        features = self._score_feature_quality(
            analysis_results.get("librosa", {})
        )
        component_scores.append(features)
        
        # Perceptual Quality (from VGGish)
        perceptual = self._score_perceptual_quality(
            analysis_results.get("vggish", {})
        )
        component_scores.append(perceptual)
        
        # Structure Quality (from StructureAnalyzer)
        structure = self._score_structure_quality(
            analysis_results.get("structure", {})
        )
        component_scores.append(structure)
        
        # Calculate weighted overall score
        overall = sum(
            cs.score * cs.weight
            for cs in component_scores
        )
        
        # Determine category
        category = self._get_quality_category(overall)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(component_scores, context)
        priority_improvements = self._get_priority_improvements(component_scores)
        
        return QualityScore(
            overall_score=round(overall, 1),
            category=category,
            component_scores=component_scores,
            recommendations=recommendations,
            priority_improvements=priority_improvements,
            metadata={
                "scoring_engine": "audio_quality_scorer_v1",
                "weights_used": self.weights,
                "context_applied": bool(context),
                "stub_mode": True
            }
        )
    
    def _score_spectral_quality(self, essentia_result: Dict) -> ComponentScore:
        """Score spectral quality from Essentia analysis."""
        # Mock scoring based on spectral features
        base_score = 75
        
        # Adjust based on features (simplified)
        spectral = essentia_result.get("spectral", {})
        if isinstance(spectral, dict):
            # Good spectral centroid range
            centroid = spectral.get("spectral_centroid", 2500)
            if 2000 <= centroid <= 4000:
                base_score += 5
            
            # Low spectral flux = stable
            flux = spectral.get("spectral_flux", 0.05)
            if flux < 0.08:
                base_score += 3
        
        return ComponentScore(
            component="spectral_quality",
            score=min(100, base_score),
            weight=self.weights["spectral_quality"],
            issues=[] if base_score >= 80 else ["Spectral balance could be improved"],
            strengths=["Good frequency distribution"] if base_score >= 80 else []
        )
    
    def _score_production_quality(self, demucs_result: Dict) -> ComponentScore:
        """Score production quality from Demucs analysis."""
        base_score = 80
        issues = []
        strengths = []
        
        separated = demucs_result.get("separated", {})
        if isinstance(separated, dict):
            # Check stem isolation
            vocals_iso = separated.get("vocals_isolation", 0.85)
            if vocals_iso >= 0.85:
                strengths.append("Excellent vocal clarity")
            elif vocals_iso < 0.75:
                issues.append("Vocal isolation could be improved")
                base_score -= 5
            
            # Check overall separation quality
            sep_quality = demucs_result.get("separation_quality", 85)
            if sep_quality >= 85:
                base_score += 5
        
        return ComponentScore(
            component="production_quality",
            score=min(100, base_score),
            weight=self.weights["production_quality"],
            issues=issues,
            strengths=strengths or ["Clean production"]
        )
    
    def _score_pitch_accuracy(self, crepe_result: Dict) -> ComponentScore:
        """Score pitch accuracy from CREPE analysis."""
        base_score = 78
        issues = []
        strengths = []
        
        mean_conf = crepe_result.get("mean_confidence", 0.85)
        if mean_conf >= 0.85:
            base_score += 7
            strengths.append("Excellent pitch stability")
        elif mean_conf < 0.75:
            issues.append("Some pitch instability detected")
            base_score -= 5
        
        contour = crepe_result.get("contour", {})
        if isinstance(contour, dict):
            stability = contour.get("pitch_stability", 0.8)
            if stability >= 0.8:
                base_score += 3
        
        return ComponentScore(
            component="pitch_accuracy",
            score=min(100, base_score),
            weight=self.weights["pitch_accuracy"],
            issues=issues,
            strengths=strengths or ["Good pitch control"]
        )
    
    def _score_feature_quality(self, librosa_result: Dict) -> ComponentScore:
        """Score feature quality from Librosa analysis."""
        base_score = 77
        issues = []
        strengths = []
        
        beat_tracking = librosa_result.get("beat_tracking", {})
        if isinstance(beat_tracking, dict):
            tempo_conf = beat_tracking.get("tempo_confidence", 0.85)
            if tempo_conf >= 0.85:
                base_score += 5
                strengths.append("Strong rhythmic consistency")
            elif tempo_conf < 0.75:
                issues.append("Rhythmic timing could be tighter")
                base_score -= 3
        
        return ComponentScore(
            component="feature_quality",
            score=min(100, base_score),
            weight=self.weights["feature_quality"],
            issues=issues,
            strengths=strengths or ["Good feature consistency"]
        )
    
    def _score_perceptual_quality(self, vggish_result: Dict) -> ComponentScore:
        """Score perceptual quality from VGGish analysis."""
        base_score = 82
        
        # VGGish captures perceptual similarity and timbre
        # In STUB, we just provide a baseline score
        
        return ComponentScore(
            component="perceptual_quality",
            score=base_score,
            weight=self.weights["perceptual_quality"],
            issues=[],
            strengths=["Good perceptual characteristics"]
        )
    
    def _score_structure_quality(self, structure_result: Dict) -> ComponentScore:
        """Score structure quality from StructureAnalyzer."""
        base_score = 75
        issues = []
        strengths = []
        
        pattern = structure_result.get("pattern", {})
        if isinstance(pattern, dict):
            commercial = pattern.get("commercial_viability", 0.7)
            if commercial >= 0.8:
                base_score += 10
                strengths.append("Commercial structure")
            elif commercial < 0.6:
                issues.append("Structure could be more conventional")
                base_score -= 5
            
            complexity = pattern.get("complexity_score", 0.5)
            if 0.4 <= complexity <= 0.7:
                base_score += 5
                strengths.append("Good structural balance")
        
        return ComponentScore(
            component="structure_quality",
            score=min(100, base_score),
            weight=self.weights["structure_quality"],
            issues=issues,
            strengths=strengths or ["Adequate structure"]
        )
    
    def _get_quality_category(self, score: float) -> QualityCategory:
        """Map score to quality category."""
        if score >= 90:
            return QualityCategory.EXCELLENT
        elif score >= 75:
            return QualityCategory.GOOD
        elif score >= 60:
            return QualityCategory.ACCEPTABLE
        elif score >= 40:
            return QualityCategory.NEEDS_IMPROVEMENT
        else:
            return QualityCategory.POOR
    
    def _generate_recommendations(
        self,
        component_scores: List[ComponentScore],
        context: Optional[Dict]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Find weakest components
        sorted_components = sorted(component_scores, key=lambda x: x.score)
        
        for comp in sorted_components[:3]:  # Top 3 improvements
            if comp.score < 80:
                if comp.component == "spectral_quality":
                    recommendations.append("Consider EQ adjustments to balance frequency spectrum")
                elif comp.component == "production_quality":
                    recommendations.append("Improve mix clarity and stem separation")
                elif comp.component == "pitch_accuracy":
                    recommendations.append("Review vocal pitch and consider pitch correction")
                elif comp.component == "feature_quality":
                    recommendations.append("Tighten rhythmic timing and tempo consistency")
                elif comp.component == "structure_quality":
                    recommendations.append("Consider restructuring for better flow")
        
        if not recommendations:
            recommendations.append("Quality is strong - focus on fine-tuning details")
        
        return recommendations
    
    def _get_priority_improvements(
        self,
        component_scores: List[ComponentScore]
    ) -> List[str]:
        """Get priority improvement areas."""
        priorities = []
        
        for comp in component_scores:
            if comp.score < 70:
                priorities.append(f"{comp.component}: {comp.score:.1f}/100")
        
        return sorted(priorities, key=lambda x: float(x.split(": ")[1].split("/")[0]))


# Factory function
def get_scoring_engine(weights: Optional[Dict[str, float]] = None) -> ScoringEngine:
    """
    Get scoring engine instance.
    
    Args:
        weights: Optional custom weights
        
    Returns:
        ScoringEngine instance
    """
    return ScoringEngine(weights=weights)
