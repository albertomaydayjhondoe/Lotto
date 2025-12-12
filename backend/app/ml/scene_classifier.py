"""
Scene Classifier - Contextual Scene Detection

Sprint 3: Vision Engine

Classifies video frames/clips into scene categories relevant to Stakazo brand:
- Calle (street)
- Coche (car/driving)
- Noche (nighttime)
- Club (nightclub/party)
- Trap House (interior trap aesthetic)
- Costa (coastal/beach - Galicia)
- Rural Galicia (countryside)
- Urbano (urban environment)
"""

import logging
from typing import List, Optional, Dict, Any
from collections import Counter
import numpy as np

from .models import SceneClassification, YOLODetection, ColorPalette

logger = logging.getLogger(__name__)


class SceneClassifier:
    """
    Rule-based and heuristic scene classification.
    
    Uses:
    - Object detections (YOLO)
    - Color palette analysis
    - Temporal patterns (frame sequences)
    - Context clues
    """
    
    # Scene detection rules based on objects
    SCENE_RULES: Dict[str, Dict] = {
        "coche": {
            "required_objects": ["car"],
            "bonus_objects": ["road", "traffic light", "motorcycle"],
            "color_hints": ["asphalt_gray", "metallic"],
            "confidence_base": 0.75
        },
        "club": {
            "required_objects": ["person", "bottle"],
            "bonus_objects": ["wine glass", "cup"],
            "color_hints": ["neon", "dark", "purple", "blue", "red"],
            "confidence_base": 0.70,
            "scene_hints": ["nightlife", "fiesta", "club"]
        },
        "calle": {
            "required_objects": ["person"],
            "bonus_objects": ["car", "bicycle", "traffic light", "bench", "backpack"],
            "color_hints": ["urban_gray", "concrete"],
            "confidence_base": 0.65,
            "scene_hints": ["urbano", "callejero", "street"]
        },
        "noche": {
            "required_objects": [],
            "bonus_objects": ["person", "car", "cell phone"],
            "color_hints": ["dark", "low_brightness"],
            "confidence_base": 0.60,
            "brightness_threshold": 0.3  # Low brightness indicator
        },
        "trap_house": {
            "required_objects": ["couch"],
            "bonus_objects": ["person", "tv", "laptop", "cell phone"],
            "color_hints": ["interior", "warm"],
            "confidence_base": 0.65,
            "scene_hints": ["interior", "relajado"]
        },
        "costa": {
            "required_objects": ["person"],
            "bonus_objects": ["surfboard", "boat", "bird"],
            "color_hints": ["blue", "cyan", "water"],
            "confidence_base": 0.70,
            "scene_hints": ["playa", "costa", "surf"]
        },
        "rural_galicia": {
            "required_objects": [],
            "bonus_objects": ["horse", "cow", "sheep", "tree", "bench"],
            "color_hints": ["green", "natural"],
            "confidence_base": 0.60,
            "scene_hints": ["rural", "naturaleza", "gallego"]
        },
        "urbano": {
            "required_objects": ["person"],
            "bonus_objects": ["car", "bus", "traffic light", "cell phone"],
            "color_hints": ["concrete", "urban_gray"],
            "confidence_base": 0.60,
            "scene_hints": ["urbano", "ciudad"]
        }
    }
    
    def __init__(self):
        """Initialize scene classifier."""
        logger.info(f"SceneClassifier initialized with {len(self.SCENE_RULES)} scene types")
    
    def classify_frame(
        self,
        detections: List[YOLODetection],
        color_palette: Optional[ColorPalette] = None,
        frame_id: int = 0,
        timestamp_ms: float = 0.0,
        semantic_tags: Optional[List[str]] = None
    ) -> List[SceneClassification]:
        """
        Classify a single frame into scene categories.
        
        Can return multiple scenes with confidence scores.
        
        Args:
            detections: List of YOLODetections for the frame
            color_palette: Optional ColorPalette for additional hints
            frame_id: Frame index
            timestamp_ms: Timestamp
            semantic_tags: Optional semantic tags from COCOMapper
        
        Returns:
            List of SceneClassifications (sorted by confidence)
        """
        object_labels = [d.label for d in detections]
        
        scene_scores = []
        
        for scene_type, rules in self.SCENE_RULES.items():
            confidence = self._calculate_scene_confidence(
                scene_type=scene_type,
                rules=rules,
                object_labels=object_labels,
                color_palette=color_palette,
                semantic_tags=semantic_tags
            )
            
            if confidence > 0.4:  # Minimum threshold
                scene_scores.append(
                    SceneClassification(
                        scene_type=scene_type,
                        confidence=confidence,
                        frame_id=frame_id,
                        timestamp_ms=timestamp_ms
                    )
                )
        
        # Sort by confidence
        scene_scores.sort(key=lambda x: x.confidence, reverse=True)
        
        return scene_scores
    
    def _calculate_scene_confidence(
        self,
        scene_type: str,
        rules: Dict,
        object_labels: List[str],
        color_palette: Optional[ColorPalette],
        semantic_tags: Optional[List[str]]
    ) -> float:
        """
        Calculate confidence score for a scene type.
        
        Args:
            scene_type: Scene type name
            rules: Scene rules dict
            object_labels: Detected object labels
            color_palette: Optional color palette
            semantic_tags: Optional semantic tags
        
        Returns:
            Confidence score (0-1)
        """
        score = 0.0
        
        # 1. Required objects check
        required = rules.get("required_objects", [])
        if required:
            has_required = all(obj in object_labels for obj in required)
            if not has_required:
                return 0.0  # Missing required objects = no match
            score += rules.get("confidence_base", 0.5)
        else:
            score += rules.get("confidence_base", 0.5) * 0.7  # Lower base if no required
        
        # 2. Bonus objects
        bonus_objects = rules.get("bonus_objects", [])
        if bonus_objects:
            bonus_count = sum(1 for obj in bonus_objects if obj in object_labels)
            bonus_score = min(0.25, bonus_count * 0.05)
            score += bonus_score
        
        # 3. Semantic tag hints
        scene_hints = rules.get("scene_hints", [])
        if scene_hints and semantic_tags:
            tag_matches = sum(1 for hint in scene_hints if hint in semantic_tags)
            if tag_matches > 0:
                score += min(0.15, tag_matches * 0.05)
        
        # 4. Color hints
        if color_palette and rules.get("color_hints"):
            color_score = self._evaluate_color_hints(
                color_palette,
                rules["color_hints"]
            )
            score += color_score * 0.10
        
        # 5. Special rules
        if "brightness_threshold" in rules:
            # Noche detection based on low brightness
            if color_palette:
                avg_brightness = self._calculate_brightness(color_palette)
                if avg_brightness < rules["brightness_threshold"]:
                    score += 0.20
        
        return min(1.0, score)
    
    def _evaluate_color_hints(
        self,
        color_palette: ColorPalette,
        color_hints: List[str]
    ) -> float:
        """
        Evaluate color hints against palette.
        
        Args:
            color_palette: ColorPalette
            color_hints: List of color hint keywords
        
        Returns:
            Match score (0-1)
        """
        score = 0.0
        
        # Check purple/morado
        if "purple" in color_hints and color_palette.purple_score > 0.5:
            score += 0.3
        
        # Check darkness (low brightness)
        if "dark" in color_hints:
            avg_brightness = self._calculate_brightness(color_palette)
            if avg_brightness < 0.4:
                score += 0.3
        
        # Check blue tones (costa/water)
        if "blue" in color_hints or "cyan" in color_hints:
            blue_ratio = self._calculate_blue_ratio(color_palette)
            if blue_ratio > 0.3:
                score += 0.3
        
        # Check green (rural/natural)
        if "green" in color_hints or "natural" in color_hints:
            green_ratio = self._calculate_green_ratio(color_palette)
            if green_ratio > 0.3:
                score += 0.3
        
        return min(1.0, score)
    
    def _calculate_brightness(self, color_palette: ColorPalette) -> float:
        """
        Calculate average brightness from color palette.
        
        Args:
            color_palette: ColorPalette
        
        Returns:
            Average brightness (0-1)
        """
        brightnesses = []
        
        for hex_color in color_palette.colors_hex:
            # Parse hex to RGB
            r = int(hex_color[1:3], 16) / 255.0
            g = int(hex_color[3:5], 16) / 255.0
            b = int(hex_color[5:7], 16) / 255.0
            
            # Relative luminance
            brightness = 0.299 * r + 0.587 * g + 0.114 * b
            brightnesses.append(brightness)
        
        return sum(brightnesses) / len(brightnesses) if brightnesses else 0.5
    
    def _calculate_blue_ratio(self, color_palette: ColorPalette) -> float:
        """Calculate ratio of blue tones in palette."""
        blue_count = 0
        
        for hex_color in color_palette.colors_hex:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Blue dominant
            if b > r and b > g:
                blue_count += 1
        
        return blue_count / len(color_palette.colors_hex) if color_palette.colors_hex else 0.0
    
    def _calculate_green_ratio(self, color_palette: ColorPalette) -> float:
        """Calculate ratio of green tones in palette."""
        green_count = 0
        
        for hex_color in color_palette.colors_hex:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Green dominant
            if g > r and g > b:
                green_count += 1
        
        return green_count / len(color_palette.colors_hex) if color_palette.colors_hex else 0.0
    
    def classify_clip(
        self,
        frame_scenes: List[List[SceneClassification]]
    ) -> Optional[str]:
        """
        Determine dominant scene for entire clip based on frame classifications.
        
        Args:
            frame_scenes: List of scene classifications per frame
        
        Returns:
            Dominant scene type or None
        """
        if not frame_scenes:
            return None
        
        # Flatten all scene classifications
        all_scenes = []
        for scenes in frame_scenes:
            if scenes:
                # Take top scene from each frame
                all_scenes.append(scenes[0].scene_type)
        
        if not all_scenes:
            return None
        
        # Most common scene
        scene_counter = Counter(all_scenes)
        dominant_scene, count = scene_counter.most_common(1)[0]
        
        logger.debug(f"Dominant scene: {dominant_scene} ({count}/{len(all_scenes)} frames)")
        
        return dominant_scene
    
    def get_scene_distribution(
        self,
        frame_scenes: List[List[SceneClassification]]
    ) -> Dict[str, float]:
        """
        Get distribution of scenes across all frames.
        
        Args:
            frame_scenes: List of scene classifications per frame
        
        Returns:
            Dict mapping scene_type -> percentage
        """
        all_scenes = []
        for scenes in frame_scenes:
            if scenes:
                all_scenes.append(scenes[0].scene_type)
        
        if not all_scenes:
            return {}
        
        scene_counter = Counter(all_scenes)
        total = len(all_scenes)
        
        distribution = {
            scene: count / total
            for scene, count in scene_counter.items()
        }
        
        return distribution
