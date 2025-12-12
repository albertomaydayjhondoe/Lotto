"""
Brand Aesthetic Extractor - Visual DNA from Real Content (Sprint 4)

Extrae el "ADN visual" del contenido real del artista usando Vision Engine.

Características:
- Usa Vision Engine (YOLO, CLIP, Color Extractor, Scene Classifier) para analizar contenido
- Identifica patrones recurrentes: colores dominantes, escenas frecuentes, objetos característicos
- Calcula consistency scores para coherencia visual
- NO tiene estética predefinida - todo extraído de contenido real
- Genera AestheticDNA data-driven

Output: AestheticDNA con patrones visuales para reglas de marca.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from collections import Counter, defaultdict
import uuid
import statistics

from .models import (
    AestheticDNA,
    AestheticPattern,
)

# Import Vision Engine components (Sprint 3)
try:
    from app.ml.models import ClipMetadata
    from app.ml.yolo_runner import YOLORunner
    from app.ml.scene_classifier import SceneClassifier
    from app.ml.color_extractor import ColorExtractor
    VISION_ENGINE_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Vision Engine not available - aesthetic extraction will be limited")
    VISION_ENGINE_AVAILABLE = False
    # Define stub type for ClipMetadata when Vision Engine not available
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from app.ml.models import ClipMetadata
    else:
        ClipMetadata = Any  # type: ignore

logger = logging.getLogger(__name__)


class BrandAestheticExtractor:
    """
    Extracts visual DNA from artist's real content.
    
    Uses Vision Engine to analyze content and identify recurring patterns.
    NO presets - purely data-driven from actual content.
    """
    
    def __init__(self, use_vision_engine: bool = True):
        """
        Initialize aesthetic extractor.
        
        Args:
            use_vision_engine: Whether to use Vision Engine for analysis (Sprint 3)
        """
        self.use_vision_engine = use_vision_engine and VISION_ENGINE_AVAILABLE
        self.content_metadata: List[ClipMetadata] = []
        
        # Vision Engine components (if available)
        if self.use_vision_engine:
            try:
                self.scene_classifier = SceneClassifier()
                self.color_extractor = ColorExtractor()
                logger.info("Vision Engine components initialized for aesthetic extraction")
            except Exception as e:
                logger.warning(f"Could not initialize Vision Engine: {e}")
                self.use_vision_engine = False
    
    # ========================================
    # Data Loading
    # ========================================
    
    def add_content_metadata(self, metadata: ClipMetadata) -> None:
        """
        Add content metadata for analysis.
        
        Args:
            metadata: ClipMetadata from Vision Engine (Sprint 3)
        """
        self.content_metadata.append(metadata)
        logger.debug(f"Added metadata for content {metadata.clip_id}")
    
    def add_batch_metadata(self, metadata_list: List[ClipMetadata]) -> None:
        """Add multiple content metadata records."""
        self.content_metadata.extend(metadata_list)
        logger.info(f"Added {len(metadata_list)} metadata records. Total: {len(self.content_metadata)}")
    
    def load_from_storage(self, storage_client: Any, artist_id: str, limit: int = 100) -> int:
        """
        Load content metadata from storage.
        
        Args:
            storage_client: Storage client (implementation-specific)
            artist_id: Artist identifier
            limit: Max number of content pieces to analyze
            
        Returns:
            Number of records loaded
        """
        # Placeholder for storage integration
        logger.info(f"Loading content metadata for artist {artist_id} (limit: {limit})")
        
        # TODO: Implement actual storage query
        # Example:
        # metadata_records = storage_client.query_content_metadata(artist_id, limit)
        # self.add_batch_metadata(metadata_records)
        
        return len(self.content_metadata)
    
    # ========================================
    # Color Analysis
    # ========================================
    
    def extract_dominant_colors(self, min_frequency: float = 0.10) -> List[str]:
        """
        Extract dominant color palette from all content.
        
        Args:
            min_frequency: Minimum frequency threshold (0.0 to 1.0)
            
        Returns:
            List of hex colors that appear frequently
        """
        if not self.content_metadata:
            return []
        
        # Collect all colors from all content
        all_colors = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'palette') and metadata.palette:
                # palette is ColorPalette with dominant_colors
                if hasattr(metadata.palette, 'dominant_colors'):
                    all_colors.extend(metadata.palette.dominant_colors)
        
        if not all_colors:
            logger.warning("No color data found in content metadata")
            return []
        
        # Count color frequencies
        color_counter = Counter(all_colors)
        total_colors = len(all_colors)
        
        # Filter by frequency threshold
        dominant_colors = [
            color for color, count in color_counter.items()
            if count / total_colors >= min_frequency
        ]
        
        # Sort by frequency
        dominant_colors.sort(key=lambda c: color_counter[c], reverse=True)
        
        logger.info(f"Extracted {len(dominant_colors)} dominant colors from {len(self.content_metadata)} content pieces")
        
        return dominant_colors
    
    def calculate_color_distribution(self) -> Dict[str, float]:
        """
        Calculate distribution of color families.
        
        Groups similar colors into families (purple, blue, dark, etc.)
        
        Returns:
            Dict mapping color family to percentage
        """
        if not self.content_metadata:
            return {}
        
        # Collect all colors
        all_colors = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'palette') and metadata.palette:
                if hasattr(metadata.palette, 'dominant_colors'):
                    all_colors.extend(metadata.palette.dominant_colors)
        
        if not all_colors:
            return {}
        
        # Group colors into families (simplified heuristic)
        color_families = defaultdict(int)
        
        for color_hex in all_colors:
            family = self._classify_color_family(color_hex)
            color_families[family] += 1
        
        # Convert to percentages
        total = sum(color_families.values())
        distribution = {
            family: round(count / total, 3)
            for family, count in color_families.items()
        }
        
        return distribution
    
    def _classify_color_family(self, hex_color: str) -> str:
        """
        Classify hex color into family.
        
        Args:
            hex_color: Hex color string (e.g., "#8B44FF")
            
        Returns:
            Color family name
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except (ValueError, IndexError):
            return "unknown"
        
        # Calculate brightness
        brightness = (r + g + b) / 3
        
        # Classify
        if brightness < 50:
            return "black"
        elif brightness < 100:
            return "dark"
        elif brightness > 200:
            return "light"
        
        # Color hue detection (simplified)
        if r > g and r > b:
            if b > g:
                return "purple"
            else:
                return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            if r > g:
                return "purple"
            else:
                return "blue"
        else:
            return "neutral"
    
    def calculate_color_consistency(self) -> float:
        """
        Calculate color consistency score.
        
        High score = colors are consistent across content
        Low score = colors vary widely
        
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if len(self.content_metadata) < 2:
            return 0.0
        
        # Get dominant colors from each content
        content_color_sets = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'palette') and metadata.palette:
                if hasattr(metadata.palette, 'dominant_colors'):
                    content_color_sets.append(set(metadata.palette.dominant_colors[:3]))  # Top 3 colors
        
        if len(content_color_sets) < 2:
            return 0.0
        
        # Calculate pairwise similarity
        similarities = []
        for i in range(len(content_color_sets)):
            for j in range(i + 1, len(content_color_sets)):
                set_i = content_color_sets[i]
                set_j = content_color_sets[j]
                
                if not set_i or not set_j:
                    continue
                
                # Jaccard similarity
                intersection = len(set_i & set_j)
                union = len(set_i | set_j)
                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)
        
        # Average similarity = consistency
        consistency = statistics.mean(similarities) if similarities else 0.0
        
        return round(consistency, 3)
    
    # ========================================
    # Scene Analysis
    # ========================================
    
    def extract_recurring_scenes(self, min_frequency: float = 0.15) -> List[Dict[str, Any]]:
        """
        Extract recurring scene types.
        
        Args:
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of scenes with frequency data
        """
        if not self.content_metadata:
            return []
        
        # Collect all scenes
        all_scenes = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'scene') and metadata.scene:
                if hasattr(metadata.scene, 'primary_scene'):
                    all_scenes.append(metadata.scene.primary_scene)
        
        if not all_scenes:
            logger.warning("No scene data found in content metadata")
            return []
        
        # Count frequencies
        scene_counter = Counter(all_scenes)
        total_scenes = len(all_scenes)
        
        # Filter and format
        recurring_scenes = []
        for scene, count in scene_counter.items():
            frequency = count / total_scenes
            if frequency >= min_frequency:
                recurring_scenes.append({
                    "scene": scene,
                    "count": count,
                    "frequency": round(frequency, 3),
                    "examples": self._get_scene_examples(scene, limit=3),
                })
        
        # Sort by frequency
        recurring_scenes.sort(key=lambda x: x["frequency"], reverse=True)
        
        logger.info(f"Extracted {len(recurring_scenes)} recurring scenes")
        
        return recurring_scenes
    
    def _get_scene_examples(self, scene: str, limit: int = 3) -> List[str]:
        """Get example content IDs for a scene."""
        examples = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'scene') and metadata.scene:
                if hasattr(metadata.scene, 'primary_scene') and metadata.scene.primary_scene == scene:
                    examples.append(metadata.clip_id)
                    if len(examples) >= limit:
                        break
        return examples
    
    def calculate_scene_distribution(self) -> Dict[str, float]:
        """
        Calculate distribution of scene types.
        
        Returns:
            Dict mapping scene to percentage
        """
        if not self.content_metadata:
            return {}
        
        all_scenes = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'scene') and metadata.scene:
                if hasattr(metadata.scene, 'primary_scene'):
                    all_scenes.append(metadata.scene.primary_scene)
        
        if not all_scenes:
            return {}
        
        scene_counter = Counter(all_scenes)
        total = len(all_scenes)
        
        distribution = {
            scene: round(count / total, 3)
            for scene, count in scene_counter.items()
        }
        
        return distribution
    
    def calculate_scene_consistency(self) -> float:
        """
        Calculate scene consistency score.
        
        High score = consistent scene types
        Low score = varied scene types
        
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if not self.content_metadata:
            return 0.0
        
        # Get scene distribution
        distribution = self.calculate_scene_distribution()
        
        if not distribution:
            return 0.0
        
        # Calculate entropy (lower entropy = more consistent)
        # Normalize to 0-1 scale
        import math
        
        entropy = -sum(p * math.log2(p) for p in distribution.values() if p > 0)
        max_entropy = math.log2(len(distribution)) if len(distribution) > 1 else 1.0
        
        # Invert so high consistency = high score
        consistency = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        
        return round(consistency, 3)
    
    # ========================================
    # Object Analysis
    # ========================================
    
    def extract_recurring_objects(self, min_frequency: float = 0.10) -> List[Dict[str, Any]]:
        """
        Extract recurring objects detected by YOLO.
        
        Args:
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of objects with frequency data
        """
        if not self.content_metadata:
            return []
        
        # Collect all detected objects
        all_objects = []
        for metadata in self.content_metadata:
            if hasattr(metadata, 'detections') and metadata.detections:
                for detection in metadata.detections:
                    if hasattr(detection, 'class_name'):
                        all_objects.append(detection.class_name)
        
        if not all_objects:
            logger.warning("No object detection data found")
            return []
        
        # Count frequencies
        object_counter = Counter(all_objects)
        total_objects = len(all_objects)
        
        # Filter and format
        recurring_objects = []
        for obj, count in object_counter.items():
            frequency = count / total_objects
            if frequency >= min_frequency:
                recurring_objects.append({
                    "object": obj,
                    "count": count,
                    "frequency": round(frequency, 3),
                })
        
        # Sort by frequency
        recurring_objects.sort(key=lambda x: x["frequency"], reverse=True)
        
        logger.info(f"Extracted {len(recurring_objects)} recurring objects")
        
        return recurring_objects
    
    # ========================================
    # Pattern Detection
    # ========================================
    
    def detect_aesthetic_patterns(self) -> List[AestheticPattern]:
        """
        Detect recurring aesthetic patterns across content.
        
        Combines color, scene, and object data to identify patterns.
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Pattern 1: Dominant color + scene combo
        color_scene_patterns = self._detect_color_scene_patterns()
        patterns.extend(color_scene_patterns)
        
        # Pattern 2: Object + scene combo
        object_scene_patterns = self._detect_object_scene_patterns()
        patterns.extend(object_scene_patterns)
        
        # Pattern 3: Time-of-day patterns (if scene data includes time)
        # ... could add more pattern types
        
        logger.info(f"Detected {len(patterns)} aesthetic patterns")
        
        return patterns
    
    def _detect_color_scene_patterns(self) -> List[AestheticPattern]:
        """Detect patterns of color+scene combinations."""
        patterns = []
        
        # Build color-scene co-occurrence matrix
        color_scene_pairs = []
        for metadata in self.content_metadata:
            scene = None
            colors = []
            
            if hasattr(metadata, 'scene') and metadata.scene:
                if hasattr(metadata.scene, 'primary_scene'):
                    scene = metadata.scene.primary_scene
            
            if hasattr(metadata, 'palette') and metadata.palette:
                if hasattr(metadata.palette, 'dominant_colors'):
                    colors = metadata.palette.dominant_colors[:2]  # Top 2 colors
            
            if scene and colors:
                for color in colors:
                    color_scene_pairs.append((color, scene, metadata.clip_id))
        
        # Find frequent patterns
        pair_counter = Counter((color, scene) for color, scene, _ in color_scene_pairs)
        total_pairs = len(color_scene_pairs)
        
        for (color, scene), count in pair_counter.items():
            frequency = count / total_pairs if total_pairs > 0 else 0.0
            if frequency >= 0.10:  # At least 10% frequency
                # Get examples
                examples = [
                    clip_id for c, s, clip_id in color_scene_pairs
                    if c == color and s == scene
                ][:3]
                
                patterns.append(AestheticPattern(
                    pattern_name=f"{color}_{scene}",
                    frequency=round(frequency, 3),
                    examples=examples,
                    confidence=min(0.95, frequency * 2),  # Simple confidence calculation
                ))
        
        return patterns
    
    def _detect_object_scene_patterns(self) -> List[AestheticPattern]:
        """Detect patterns of object+scene combinations."""
        patterns = []
        
        # Build object-scene pairs
        object_scene_pairs = []
        for metadata in self.content_metadata:
            scene = None
            objects = []
            
            if hasattr(metadata, 'scene') and metadata.scene:
                if hasattr(metadata.scene, 'primary_scene'):
                    scene = metadata.scene.primary_scene
            
            if hasattr(metadata, 'detections') and metadata.detections:
                objects = list(set(d.class_name for d in metadata.detections if hasattr(d, 'class_name')))[:3]
            
            if scene and objects:
                for obj in objects:
                    object_scene_pairs.append((obj, scene, metadata.clip_id))
        
        # Find frequent patterns
        pair_counter = Counter((obj, scene) for obj, scene, _ in object_scene_pairs)
        total_pairs = len(object_scene_pairs)
        
        for (obj, scene), count in pair_counter.items():
            frequency = count / total_pairs if total_pairs > 0 else 0.0
            if frequency >= 0.10:
                examples = [
                    clip_id for o, s, clip_id in object_scene_pairs
                    if o == obj and s == scene
                ][:3]
                
                patterns.append(AestheticPattern(
                    pattern_name=f"{obj}_{scene}",
                    frequency=round(frequency, 3),
                    examples=examples,
                    confidence=min(0.95, frequency * 2),
                ))
        
        return patterns
    
    # ========================================
    # Coherence Scoring
    # ========================================
    
    def calculate_overall_coherence(self) -> float:
        """
        Calculate overall visual coherence score.
        
        Combines color consistency, scene consistency, and pattern strength.
        
        Returns:
            Coherence score (0.0 to 1.0)
        """
        if len(self.content_metadata) < 2:
            return 0.0
        
        color_consistency = self.calculate_color_consistency()
        scene_consistency = self.calculate_scene_consistency()
        
        # Pattern strength (how many strong patterns detected)
        patterns = self.detect_aesthetic_patterns()
        pattern_strength = len([p for p in patterns if p.confidence > 0.7]) / max(len(patterns), 1)
        pattern_strength = min(pattern_strength, 1.0)
        
        # Weighted average
        coherence = (
            color_consistency * 0.35 +
            scene_consistency * 0.35 +
            pattern_strength * 0.30
        )
        
        return round(coherence, 3)
    
    # ========================================
    # DNA Generation
    # ========================================
    
    def generate_aesthetic_dna(self) -> AestheticDNA:
        """
        Generate complete AestheticDNA from all content.
        
        This is the main output - comprehensive visual DNA.
        
        Returns:
            AestheticDNA object
        """
        if not self.content_metadata:
            raise ValueError("Cannot generate DNA without content metadata")
        
        dna_id = f"dna_{uuid.uuid4().hex[:12]}"
        
        logger.info("Generating aesthetic DNA from content...")
        
        # Extract all components
        dominant_colors = self.extract_dominant_colors(min_frequency=0.10)
        color_distribution = self.calculate_color_distribution()
        
        recurring_scenes = self.extract_recurring_scenes(min_frequency=0.15)
        scene_distribution = self.calculate_scene_distribution()
        
        recurring_objects = self.extract_recurring_objects(min_frequency=0.10)
        
        aesthetic_patterns = self.detect_aesthetic_patterns()
        
        # Calculate consistency scores
        color_consistency = self.calculate_color_consistency()
        scene_consistency = self.calculate_scene_consistency()
        overall_coherence = self.calculate_overall_coherence()
        
        # Create DNA
        dna = AestheticDNA(
            dna_id=dna_id,
            dominant_color_palette=dominant_colors,
            color_distribution=color_distribution,
            recurring_scenes=recurring_scenes,
            scene_distribution=scene_distribution,
            recurring_objects=recurring_objects,
            aesthetic_patterns=aesthetic_patterns,
            color_consistency_score=color_consistency,
            scene_consistency_score=scene_consistency,
            overall_coherence_score=overall_coherence,
            analyzed_content_count=len(self.content_metadata),
        )
        
        logger.info(
            f"Generated AestheticDNA {dna_id} from {len(self.content_metadata)} content pieces "
            f"(coherence: {overall_coherence:.2f})"
        )
        
        return dna
    
    # ========================================
    # Utilities
    # ========================================
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get summary of extraction readiness."""
        return {
            "total_content": len(self.content_metadata),
            "vision_engine_enabled": self.use_vision_engine,
            "ready_for_extraction": len(self.content_metadata) > 0,
            "has_color_data": any(
                hasattr(m, 'palette') and m.palette for m in self.content_metadata
            ),
            "has_scene_data": any(
                hasattr(m, 'scene') and m.scene for m in self.content_metadata
            ),
            "has_detection_data": any(
                hasattr(m, 'detections') and m.detections for m in self.content_metadata
            ),
        }
    
    def clear_data(self) -> None:
        """Clear all loaded content metadata."""
        self.content_metadata = []
        logger.info("Cleared all content metadata")
