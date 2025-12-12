"""
Clip Selector - Visual Intelligence Integration

Sprint 3: Content Engine + Vision Engine Integration

Uses visual metadata from Vision Engine to:
- Select best clips for publication
- Score clips based on visual features
- Filter clips by aesthetic criteria
- Rank clips by virality potential
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..ml.models import ClipMetadata
from ..ml.clip_tagger import ClipTagger

logger = logging.getLogger(__name__)


class ClipSelector:
    """
    Intelligent clip selection using visual metadata.
    
    Integrates Vision Engine outputs to make data-driven decisions about:
    - Which clips to publish
    - Which clips have highest viral potential
    - Which clips best align with brand aesthetic
    """
    
    def __init__(self, vision_tagger: Optional[ClipTagger] = None):
        """
        Initialize clip selector.
        
        Args:
            vision_tagger: Optional ClipTagger instance. If None, creates new one.
        """
        self.vision_tagger = vision_tagger
        logger.info("ClipSelector initialized")
    
    def score_clip(
        self,
        metadata: ClipMetadata,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall score for a clip based on visual metadata.
        
        Args:
            metadata: ClipMetadata from Vision Engine
            weights: Optional custom weights for scoring components
        
        Returns:
            Overall score (0-1)
        """
        # Default weights
        if weights is None:
            weights = {
                "virality": 0.35,
                "brand_affinity": 0.30,
                "aesthetic": 0.25,
                "scene_bonus": 0.10
            }
        
        # Base score components
        virality_component = metadata.virality_score_visual * weights["virality"]
        brand_component = metadata.brand_affinity_score * weights["brand_affinity"]
        aesthetic_component = metadata.aesthetic_score * weights["aesthetic"]
        
        # Scene bonus (prefer certain scenes)
        scene_bonus = 0.0
        if metadata.dominant_scene in ["coche", "club", "calle"]:
            scene_bonus = 1.0 * weights["scene_bonus"]
        elif metadata.dominant_scene in ["costa", "urbano"]:
            scene_bonus = 0.7 * weights["scene_bonus"]
        
        total_score = (
            virality_component +
            brand_component +
            aesthetic_component +
            scene_bonus
        )
        
        return min(1.0, total_score)
    
    def select_best_clips(
        self,
        clips_metadata: List[ClipMetadata],
        top_k: int = 5,
        min_score: float = 0.6,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ClipMetadata]:
        """
        Select the best clips from a list based on visual scores.
        
        Args:
            clips_metadata: List of ClipMetadata
            top_k: Number of clips to return
            min_score: Minimum score threshold
            filters: Optional filters (e.g., {"dominant_scene": "coche"})
        
        Returns:
            List of best clips (sorted by score)
        """
        # Apply filters
        filtered_clips = clips_metadata
        
        if filters:
            for key, value in filters.items():
                if key == "dominant_scene":
                    filtered_clips = [
                        c for c in filtered_clips
                        if c.dominant_scene == value
                    ]
                elif key == "min_purple_score":
                    filtered_clips = [
                        c for c in filtered_clips
                        if c.color_palette and c.color_palette.purple_score >= value
                    ]
                elif key == "required_objects":
                    # Must contain at least one of the required objects
                    required = value if isinstance(value, list) else [value]
                    filtered_clips = [
                        c for c in filtered_clips
                        if any(obj in c.objects_detected for obj in required)
                    ]
        
        # Score clips
        scored_clips = [
            (clip, self.score_clip(clip))
            for clip in filtered_clips
        ]
        
        # Filter by minimum score
        scored_clips = [
            (clip, score)
            for clip, score in scored_clips
            if score >= min_score
        ]
        
        # Sort by score (descending)
        scored_clips.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K
        best_clips = [clip for clip, score in scored_clips[:top_k]]
        
        logger.info(
            f"Selected {len(best_clips)} clips from {len(clips_metadata)} total "
            f"(min_score={min_score}, top_k={top_k})"
        )
        
        return best_clips
    
    def get_publication_recommendation(
        self,
        metadata: ClipMetadata,
        platform: str = "instagram"
    ) -> Dict[str, Any]:
        """
        Get publication recommendation for a clip.
        
        Args:
            metadata: ClipMetadata
            platform: Target platform ("instagram", "tiktok", "youtube")
        
        Returns:
            Dict with recommendation
        """
        score = self.score_clip(metadata)
        
        # Platform-specific adjustments
        if platform == "instagram":
            # Instagram prefers purple aesthetic + urban scenes
            if metadata.color_palette and metadata.color_palette.purple_score > 0.6:
                score *= 1.1
            if metadata.dominant_scene in ["urbano", "calle"]:
                score *= 1.05
        
        elif platform == "tiktok":
            # TikTok prefers high-energy scenes
            if metadata.dominant_scene in ["coche", "club"]:
                score *= 1.15
        
        elif platform == "youtube":
            # YouTube prefers longer, narrative content
            if metadata.dominant_scene in ["coche", "costa"]:
                score *= 1.1
        
        # Clamp score
        score = min(1.0, score)
        
        # Recommendation
        if score >= 0.8:
            recommendation = "publish_immediately"
            priority = "high"
        elif score >= 0.6:
            recommendation = "publish_scheduled"
            priority = "medium"
        else:
            recommendation = "hold_for_review"
            priority = "low"
        
        return {
            "clip_id": metadata.clip_id,
            "platform": platform,
            "score": score,
            "recommendation": recommendation,
            "priority": priority,
            "reasoning": {
                "virality_score": metadata.virality_score_visual,
                "brand_affinity": metadata.brand_affinity_score,
                "aesthetic_score": metadata.aesthetic_score,
                "dominant_scene": metadata.dominant_scene,
                "purple_aesthetic": metadata.color_palette.purple_score if metadata.color_palette else 0.0
            }
        }
    
    def compare_clips(
        self,
        clip_a: ClipMetadata,
        clip_b: ClipMetadata
    ) -> Dict[str, Any]:
        """
        Compare two clips and recommend which is better.
        
        Args:
            clip_a: First clip metadata
            clip_b: Second clip metadata
        
        Returns:
            Comparison result
        """
        score_a = self.score_clip(clip_a)
        score_b = self.score_clip(clip_b)
        
        winner = clip_a if score_a > score_b else clip_b
        
        return {
            "winner_clip_id": winner.clip_id,
            "scores": {
                clip_a.clip_id: score_a,
                clip_b.clip_id: score_b
            },
            "score_difference": abs(score_a - score_b),
            "comparison": {
                "virality": {
                    clip_a.clip_id: clip_a.virality_score_visual,
                    clip_b.clip_id: clip_b.virality_score_visual
                },
                "aesthetic": {
                    clip_a.clip_id: clip_a.aesthetic_score,
                    clip_b.clip_id: clip_b.aesthetic_score
                },
                "scene": {
                    clip_a.clip_id: clip_a.dominant_scene,
                    clip_b.clip_id: clip_b.dominant_scene
                }
            }
        }
    
    def filter_by_aesthetic(
        self,
        clips_metadata: List[ClipMetadata],
        aesthetic_type: str = "morado_dominante",
        min_threshold: float = 0.5
    ) -> List[ClipMetadata]:
        """
        Filter clips by aesthetic criteria.
        
        Args:
            clips_metadata: List of ClipMetadata
            aesthetic_type: Type of aesthetic to filter for
            min_threshold: Minimum aesthetic score
        
        Returns:
            Filtered clips
        """
        filtered = []
        
        for clip in clips_metadata:
            if not clip.color_palette:
                continue
            
            if aesthetic_type == "morado_dominante":
                if clip.color_palette.purple_score >= min_threshold:
                    filtered.append(clip)
            
            elif aesthetic_type == "oscuro":
                # Check if dominant color is dark
                # (simplified: check if purple_score is low and brightness is low)
                if clip.color_palette.purple_score < 0.3:
                    filtered.append(clip)
            
            elif aesthetic_type == "luminoso":
                # Bright aesthetic (inverse of oscuro)
                if clip.color_palette.purple_score > 0.7 or clip.aesthetic_score > 0.7:
                    filtered.append(clip)
        
        logger.info(
            f"Filtered {len(filtered)} clips with aesthetic_type={aesthetic_type} "
            f"from {len(clips_metadata)} total"
        )
        
        return filtered


# Factory function for easy integration
def create_clip_selector(initialize_vision: bool = False) -> ClipSelector:
    """
    Create a ClipSelector instance.
    
    Args:
        initialize_vision: If True, initializes Vision Engine (loads models)
    
    Returns:
        ClipSelector instance
    """
    vision_tagger = None
    
    if initialize_vision:
        from ..ml.clip_tagger import ClipTagger
        vision_tagger = ClipTagger()
        vision_tagger.initialize()
        logger.info("Vision Engine initialized for ClipSelector")
    
    return ClipSelector(vision_tagger=vision_tagger)
