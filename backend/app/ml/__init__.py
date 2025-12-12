"""
Vision Engine - STAKAZO ML Module

Sprint 3: Subsistema completo de visión artificial para análisis de vídeos.

Componentes:
- yolo_runner: Ultralytics YOLOv8/v11 integration
- coco_mapper: COCO semantics → Stakazo internal tags
- visual_embeddings: CLIP/VisionTransformer embeddings + FAISS
- scene_classifier: Scene detection (club, calle, coche, noche, trap-house)
- color_extractor: Dominant palette + purple aesthetic scoring
- clip_tagger: Fusion of all visual metadata
- models: Pydantic models for all ML outputs

Integrations:
- Content Engine (clip_selector uses visual metadata)
- Satellite Engine (visual-based publication selection)
- Orchestrator (feeds visual signals to ML pipeline)
- Rules Engine (visual scoring for virality prediction)

Cost Guards:
- FPS throttling (1 FPS default)
- Frame sampling heuristics
- E2B fallback for heavy inference
- Telemetry for all operations
"""

__version__ = "1.0.0"

from .models import (
    YOLODetection,
    COCOMapping,
    VisualEmbedding,
    SceneClassification,
    ColorPalette,
    ClipMetadata,
)
from .yolo_runner import YOLORunner
from .coco_mapper import COCOMapper
from .visual_embeddings import VisualEmbeddingsEngine
from .scene_classifier import SceneClassifier
from .color_extractor import ColorExtractor
from .clip_tagger import ClipTagger

__all__ = [
    "YOLODetection",
    "COCOMapping",
    "VisualEmbedding",
    "SceneClassification",
    "ColorPalette",
    "ClipMetadata",
    "YOLORunner",
    "COCOMapper",
    "VisualEmbeddingsEngine",
    "SceneClassifier",
    "ColorExtractor",
    "ClipTagger",
]
