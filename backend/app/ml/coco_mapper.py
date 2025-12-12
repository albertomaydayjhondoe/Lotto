"""
COCO Mapper - Semantic Enrichment for Stakazo

Sprint 3: Vision Engine

Translates COCO's 80 object categories into Stakazo's internal semantic space.

Features:
- 80 COCO classes → rich semantic tags
- Brand affinity scoring (Stakas + Lendas Daría aesthetic)
- Virality prediction based on visual elements
- Cultural context (Galicia, trap, street, club)
"""

import logging
from typing import List, Dict, Optional
from .models import COCOMapping, YOLODetection, EnrichedDetection

logger = logging.getLogger(__name__)


class COCOMapper:
    """
    Maps COCO object labels to Stakazo internal semantics.
    
    Provides:
    - Semantic tags aligned with Stakazo brand
    - Brand affinity scores
    - Virality potential scores
    - Cultural/scene context
    """
    
    # Comprehensive COCO → Stakazo semantic mapping
    SEMANTIC_MAPPINGS: Dict[str, Dict] = {
        # Vehicles → High affinity for trap/street aesthetic
        "car": {
            "tags": ["coche", "asfalto", "velocidad", "trap-street", "movimiento", "urbano"],
            "affinity": 0.85,
            "virality": 0.72
        },
        "motorcycle": {
            "tags": ["moto", "velocidad", "adrenalina", "calle", "rebelde", "urbano"],
            "affinity": 0.78,
            "virality": 0.68
        },
        "bicycle": {
            "tags": ["bici", "deportivo", "street", "urbano"],
            "affinity": 0.45,
            "virality": 0.40
        },
        "truck": {
            "tags": ["camion", "industrial", "calle"],
            "affinity": 0.50,
            "virality": 0.35
        },
        "bus": {
            "tags": ["bus", "transporte", "urbano"],
            "affinity": 0.40,
            "virality": 0.30
        },
        
        # People → Essential for storytelling
        "person": {
            "tags": ["callejero", "urbano", "flow", "presencia", "storytelling"],
            "affinity": 0.92,
            "virality": 0.88
        },
        
        # Electronics → Modern, viral content
        "cell phone": {
            "tags": ["moderno", "selfie", "viral", "conectado", "social-media"],
            "affinity": 0.88,
            "virality": 0.85
        },
        "laptop": {
            "tags": ["tech", "trabajo", "digital", "creativo"],
            "affinity": 0.70,
            "virality": 0.55
        },
        "tv": {
            "tags": ["pantalla", "interior", "entretenimiento"],
            "affinity": 0.50,
            "virality": 0.45
        },
        "remote": {
            "tags": ["control", "tech"],
            "affinity": 0.30,
            "virality": 0.25
        },
        "keyboard": {
            "tags": ["tech", "produccion", "digital"],
            "affinity": 0.60,
            "virality": 0.50
        },
        "mouse": {
            "tags": ["tech", "digital"],
            "affinity": 0.55,
            "virality": 0.45
        },
        
        # Nightlife & Party → Core brand identity
        "bottle": {
            "tags": ["club", "fiesta", "noche", "celebracion", "nightlife"],
            "affinity": 0.90,
            "virality": 0.75
        },
        "wine glass": {
            "tags": ["elegante", "celebracion", "noche"],
            "affinity": 0.75,
            "virality": 0.65
        },
        "cup": {
            "tags": ["bebida", "social", "casual"],
            "affinity": 0.60,
            "virality": 0.50
        },
        
        # Fashion & Accessories
        "handbag": {
            "tags": ["moda", "estilo", "urbano", "fashion"],
            "affinity": 0.70,
            "virality": 0.60
        },
        "backpack": {
            "tags": ["casual", "urbano", "street"],
            "affinity": 0.65,
            "virality": 0.55
        },
        "tie": {
            "tags": ["formal", "elegante"],
            "affinity": 0.40,
            "virality": 0.30
        },
        "umbrella": {
            "tags": ["clima", "gallego", "lluvia"],
            "affinity": 0.55,
            "virality": 0.45
        },
        
        # Sports & Action
        "sports ball": {
            "tags": ["deporte", "accion", "dinamico"],
            "affinity": 0.68,
            "virality": 0.70
        },
        "skateboard": {
            "tags": ["street", "urbano", "skate-culture", "rebelde"],
            "affinity": 0.80,
            "virality": 0.75
        },
        "surfboard": {
            "tags": ["playa", "costa", "galicia", "surf", "verano"],
            "affinity": 0.82,
            "virality": 0.78
        },
        
        # Animals → Context-dependent
        "dog": {
            "tags": ["mascota", "compañia", "callejero"],
            "affinity": 0.65,
            "virality": 0.72
        },
        "cat": {
            "tags": ["mascota", "interior"],
            "affinity": 0.60,
            "virality": 0.68
        },
        "bird": {
            "tags": ["naturaleza", "exterior"],
            "affinity": 0.50,
            "virality": 0.45
        },
        "horse": {
            "tags": ["rural", "galicia", "naturaleza"],
            "affinity": 0.58,
            "virality": 0.50
        },
        
        # Food & Dining
        "pizza": {
            "tags": ["comida", "social", "casual"],
            "affinity": 0.70,
            "virality": 0.65
        },
        "hot dog": {
            "tags": ["comida", "street-food", "casual"],
            "affinity": 0.65,
            "virality": 0.60
        },
        "sandwich": {
            "tags": ["comida", "casual"],
            "affinity": 0.55,
            "virality": 0.50
        },
        "donut": {
            "tags": ["dulce", "comida", "viral"],
            "affinity": 0.62,
            "virality": 0.68
        },
        "cake": {
            "tags": ["celebracion", "dulce", "fiesta"],
            "affinity": 0.68,
            "virality": 0.70
        },
        
        # Indoor Furniture
        "chair": {
            "tags": ["interior", "mueble"],
            "affinity": 0.35,
            "virality": 0.25
        },
        "couch": {
            "tags": ["interior", "relajado", "trap-house"],
            "affinity": 0.62,
            "virality": 0.55
        },
        "bed": {
            "tags": ["interior", "intimo", "lifestyle"],
            "affinity": 0.58,
            "virality": 0.60
        },
        "dining table": {
            "tags": ["interior", "social", "comida"],
            "affinity": 0.50,
            "virality": 0.45
        },
        
        # Urban Elements
        "traffic light": {
            "tags": ["urbano", "calle", "ciudad"],
            "affinity": 0.60,
            "virality": 0.50
        },
        "stop sign": {
            "tags": ["urbano", "calle", "señalizacion"],
            "affinity": 0.55,
            "virality": 0.48
        },
        "parking meter": {
            "tags": ["urbano", "calle"],
            "affinity": 0.45,
            "virality": 0.40
        },
        "bench": {
            "tags": ["urbano", "publico", "exterior"],
            "affinity": 0.50,
            "virality": 0.45
        },
        
        # Books & Education
        "book": {
            "tags": ["cultura", "educacion", "intelectual"],
            "affinity": 0.55,
            "virality": 0.50
        },
        
        # Clocks & Time
        "clock": {
            "tags": ["tiempo", "puntual"],
            "affinity": 0.45,
            "virality": 0.40
        },
        
        # Decor
        "vase": {
            "tags": ["decoracion", "interior", "estetica"],
            "affinity": 0.52,
            "virality": 0.48
        },
        "potted plant": {
            "tags": ["naturaleza", "interior", "decoracion"],
            "affinity": 0.55,
            "virality": 0.50
        },
    }
    
    # Default mapping for unmapped classes
    DEFAULT_MAPPING = {
        "tags": ["generico", "objeto"],
        "affinity": 0.30,
        "virality": 0.25
    }
    
    def __init__(self):
        """Initialize COCO mapper."""
        logger.info(
            f"COCOMapper initialized with {len(self.SEMANTIC_MAPPINGS)} mapped classes"
        )
    
    def map_detection(self, detection: YOLODetection) -> COCOMapping:
        """
        Map a single YOLO detection to Stakazo semantics.
        
        Args:
            detection: YOLODetection from YOLO runner
        
        Returns:
            COCOMapping with semantic enrichment
        """
        label = detection.label
        
        # Get mapping or use default
        mapping_data = self.SEMANTIC_MAPPINGS.get(label, self.DEFAULT_MAPPING)
        
        return COCOMapping(
            coco_label=label,
            stakazo_tags=mapping_data["tags"],
            affinity_score=mapping_data["affinity"],
            virality_score=mapping_data["virality"]
        )
    
    def enrich_detection(self, detection: YOLODetection) -> EnrichedDetection:
        """
        Enrich a YOLO detection with semantic mapping.
        
        Args:
            detection: YOLODetection from YOLO runner
        
        Returns:
            EnrichedDetection with detection + mapping
        """
        mapping = self.map_detection(detection)
        
        return EnrichedDetection(
            detection=detection,
            mapping=mapping
        )
    
    def enrich_all(self, detections: List[YOLODetection]) -> List[EnrichedDetection]:
        """
        Enrich multiple detections.
        
        Args:
            detections: List of YOLODetections
        
        Returns:
            List of EnrichedDetections
        """
        return [self.enrich_detection(d) for d in detections]
    
    def get_unique_tags(self, detections: List[YOLODetection]) -> List[str]:
        """
        Get all unique semantic tags from a list of detections.
        
        Args:
            detections: List of YOLODetections
        
        Returns:
            List of unique semantic tags
        """
        all_tags = set()
        
        for detection in detections:
            mapping = self.map_detection(detection)
            all_tags.update(mapping.stakazo_tags)
        
        return sorted(list(all_tags))
    
    def calculate_aggregate_scores(
        self,
        detections: List[YOLODetection]
    ) -> Dict[str, float]:
        """
        Calculate aggregate scores for a set of detections.
        
        Useful for clip-level scoring.
        
        Args:
            detections: List of YOLODetections
        
        Returns:
            Dict with aggregate scores
        """
        if not detections:
            return {
                "avg_affinity": 0.0,
                "avg_virality": 0.0,
                "max_affinity": 0.0,
                "max_virality": 0.0,
                "num_high_affinity": 0  # > 0.7
            }
        
        affinities = []
        viralities = []
        
        for detection in detections:
            mapping = self.map_detection(detection)
            affinities.append(mapping.affinity_score)
            viralities.append(mapping.virality_score)
        
        return {
            "avg_affinity": sum(affinities) / len(affinities),
            "avg_virality": sum(viralities) / len(viralities),
            "max_affinity": max(affinities),
            "max_virality": max(viralities),
            "num_high_affinity": sum(1 for a in affinities if a > 0.7)
        }
    
    def get_scene_hints(self, detections: List[YOLODetection]) -> List[str]:
        """
        Infer possible scenes based on detected objects.
        
        Args:
            detections: List of YOLODetections
        
        Returns:
            List of scene hints
        """
        tags = self.get_unique_tags(detections)
        
        scenes = []
        
        # Scene inference rules
        if any(t in tags for t in ["coche", "asfalto", "velocidad"]):
            scenes.append("coche")
        if any(t in tags for t in ["club", "fiesta", "noche", "nightlife"]):
            scenes.append("club")
        if any(t in tags for t in ["calle", "urbano", "callejero"]):
            scenes.append("calle")
        if any(t in tags for t in ["trap-house", "relajado", "interior"]):
            scenes.append("trap_house")
        if any(t in tags for t in ["costa", "playa", "surf"]):
            scenes.append("costa")
        if any(t in tags for t in ["rural", "naturaleza", "gallego"]):
            scenes.append("rural_galicia")
        
        return scenes
