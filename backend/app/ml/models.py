"""
Pydantic models for Vision Engine (Sprint 3)

All ML outputs are strongly typed for validation and serialization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ========================================
# 1. YOLO Detection Models
# ========================================

class BoundingBox(BaseModel):
    """Bounding box coordinates (normalized 0-1 or absolute pixels)."""
    x: float = Field(..., description="Left X coordinate")
    y: float = Field(..., description="Top Y coordinate")
    w: float = Field(..., description="Width")
    h: float = Field(..., description="Height")
    
    @field_validator('x', 'y', 'w', 'h')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Coordinates must be non-negative")
        return v


class YOLODetection(BaseModel):
    """Single YOLO object detection result."""
    label: str = Field(..., description="COCO class label (e.g., 'car', 'person')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bbox: BoundingBox = Field(..., description="Bounding box")
    class_id: int = Field(..., description="COCO class ID")
    
    model_config = {"json_schema_extra": {
        "example": {
            "label": "car",
            "confidence": 0.87,
            "bbox": {"x": 100, "y": 150, "w": 300, "h": 200},
            "class_id": 2
        }
    }}


class FrameDetections(BaseModel):
    """All detections for a single video frame."""
    frame_id: int = Field(..., description="Frame number (0-indexed)")
    timestamp_ms: float = Field(..., description="Timestamp in video (milliseconds)")
    detections: List[YOLODetection] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Inference time")
    
    model_config = {"json_schema_extra": {
        "example": {
            "frame_id": 120,
            "timestamp_ms": 4000.0,
            "detections": [
                {"label": "person", "confidence": 0.92, "bbox": {"x": 50, "y": 80, "w": 120, "h": 250}, "class_id": 0}
            ],
            "processing_time_ms": 45.3
        }
    }}


# ========================================
# 2. COCO Mapping Models
# ========================================

class COCOMapping(BaseModel):
    """Mapping from COCO label to Stakazo internal semantics."""
    coco_label: str = Field(..., description="Original COCO label")
    stakazo_tags: List[str] = Field(..., description="Internal semantic tags")
    affinity_score: float = Field(0.0, ge=0.0, le=1.0, description="Brand affinity (0-1)")
    virality_score: float = Field(0.0, ge=0.0, le=1.0, description="Virality potential (0-1)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "coco_label": "car",
            "stakazo_tags": ["coche", "asfalto", "velocidad", "trap-street"],
            "affinity_score": 0.85,
            "virality_score": 0.72
        }
    }}


class EnrichedDetection(BaseModel):
    """YOLO detection + COCO semantic enrichment."""
    detection: YOLODetection
    mapping: COCOMapping


# ========================================
# 3. Visual Embeddings Models
# ========================================

class VisualEmbedding(BaseModel):
    """Visual embedding vector from CLIP or Vision Transformer."""
    embedding_id: str = Field(..., description="Unique ID for this embedding")
    vector: List[float] = Field(..., description="Embedding vector (512 or 768 dims)")
    model_name: str = Field(..., description="Model used (e.g., 'clip-vit-base-patch32')")
    frame_id: Optional[int] = Field(None, description="Source frame ID")
    timestamp_ms: Optional[float] = Field(None, description="Source timestamp")
    
    @field_validator('vector')
    @classmethod
    def validate_vector(cls, v: List[float]) -> List[float]:
        if len(v) not in [512, 768, 1024]:
            raise ValueError(f"Invalid embedding dimension: {len(v)}")
        return v
    
    model_config = {"json_schema_extra": {
        "example": {
            "embedding_id": "emb_frame_120",
            "vector": [0.1, 0.2, 0.3],  # truncated for example
            "model_name": "clip-vit-base-patch32",
            "frame_id": 120,
            "timestamp_ms": 4000.0
        }
    }}


class SimilarityResult(BaseModel):
    """Result of FAISS similarity search."""
    query_embedding_id: str
    similar_embeddings: List[Dict[str, Any]] = Field(
        ...,
        description="List of {embedding_id, distance, metadata}"
    )
    search_time_ms: float


# ========================================
# 4. Scene Classification Models
# ========================================

class SceneClassification(BaseModel):
    """Scene category classification result."""
    scene_type: str = Field(..., description="Scene category")
    confidence: float = Field(..., ge=0.0, le=1.0)
    frame_id: int
    timestamp_ms: float
    
    # Valid scene types for Stakazo
    VALID_SCENES = [
        "calle",
        "coche",
        "noche",
        "club",
        "trap_house",
        "costa",
        "rural_galicia",
        "urbano",
        "interior",
        "exterior"
    ]
    
    @field_validator('scene_type')
    @classmethod
    def validate_scene(cls, v: str) -> str:
        if v not in cls.VALID_SCENES:
            raise ValueError(f"Invalid scene type: {v}. Must be one of {cls.VALID_SCENES}")
        return v
    
    model_config = {"json_schema_extra": {
        "example": {
            "scene_type": "coche",
            "confidence": 0.88,
            "frame_id": 120,
            "timestamp_ms": 4000.0
        }
    }}


# ========================================
# 5. Color Extraction Models
# ========================================

class ColorPalette(BaseModel):
    """Dominant color palette extracted from frame/clip."""
    colors_hex: List[str] = Field(..., description="Hex color codes", max_length=10)
    percentages: List[float] = Field(..., description="Percentage of each color")
    purple_score: float = Field(0.0, ge=0.0, le=1.0, description="Purple aesthetic score")
    morado_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Percentage of purple tones")
    dominant_color: str = Field(..., description="Most dominant hex color")
    
    @field_validator('colors_hex')
    @classmethod
    def validate_hex(cls, v: List[str]) -> List[str]:
        for color in v:
            if not color.startswith('#') or len(color) != 7:
                raise ValueError(f"Invalid hex color: {color}")
        return v
    
    @field_validator('percentages')
    @classmethod
    def validate_sum(cls, v: List[float]) -> List[float]:
        total = sum(v)
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Percentages must sum to ~1.0, got {total}")
        return v
    
    model_config = {"json_schema_extra": {
        "example": {
            "colors_hex": ["#8B44FF", "#1A1A2E", "#16213E"],
            "percentages": [0.45, 0.35, 0.20],
            "purple_score": 0.87,
            "morado_ratio": 0.45,
            "dominant_color": "#8B44FF"
        }
    }}


# ========================================
# 6. Clip Metadata (Fusion)
# ========================================

class ClipMetadata(BaseModel):
    """
    Complete visual metadata for a video clip.
    
    Fusion of:
    - YOLO detections
    - COCO semantic mappings
    - Visual embeddings
    - Scene classifications
    - Color palette
    """
    clip_id: str = Field(..., description="Clip UUID")
    video_id: str = Field(..., description="Source video UUID")
    
    # YOLO + COCO
    detections: List[EnrichedDetection] = Field(default_factory=list)
    objects_detected: List[str] = Field(default_factory=list, description="Unique object labels")
    
    # Embeddings
    embeddings: List[VisualEmbedding] = Field(default_factory=list)
    avg_embedding: Optional[List[float]] = Field(None, description="Average embedding for clip")
    
    # Scenes
    scenes: List[SceneClassification] = Field(default_factory=list)
    dominant_scene: Optional[str] = Field(None, description="Most frequent scene")
    
    # Colors
    color_palette: Optional[ColorPalette] = Field(None)
    
    # Scores
    virality_score_visual: float = Field(0.0, ge=0.0, le=1.0, description="Visual virality score")
    brand_affinity_score: float = Field(0.0, ge=0.0, le=1.0, description="Brand affinity score")
    aesthetic_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall aesthetic score")
    
    # Metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_cost_eur: float = Field(0.0, description="Processing cost in EUR")
    
    model_config = {"json_schema_extra": {
        "example": {
            "clip_id": "clip_abc123",
            "video_id": "video_xyz789",
            "objects_detected": ["car", "person", "cell_phone"],
            "dominant_scene": "coche",
            "virality_score_visual": 0.82,
            "brand_affinity_score": 0.76,
            "aesthetic_score": 0.88,
            "processed_at": "2025-12-07T10:30:00Z",
            "processing_cost_eur": 0.0023
        }
    }}


# ========================================
# 7. Processing Configuration
# ========================================

class VisionConfig(BaseModel):
    """Configuration for Vision Engine processing."""
    
    # YOLO
    yolo_model: str = Field("yolov8n.pt", description="YOLO model to use")
    yolo_confidence_threshold: float = Field(0.25, ge=0.0, le=1.0)
    yolo_device: str = Field("cpu", description="'cpu' or 'cuda'")
    
    # Frame sampling
    target_fps: float = Field(1.0, ge=0.1, le=30.0, description="Target FPS for processing")
    max_frames_per_clip: int = Field(30, ge=1, description="Max frames to process per clip")
    
    # Embeddings
    embedding_model: str = Field("clip-vit-base-patch32", description="CLIP model")
    use_faiss: bool = Field(True, description="Enable FAISS similarity search")
    
    # Cost guards
    max_cost_per_clip_eur: float = Field(0.01, description="Max cost per clip")
    enable_e2b_fallback: bool = Field(True, description="Use E2B for heavy inference")
    
    # Telemetry
    enable_telemetry: bool = Field(True)
    
    model_config = {"json_schema_extra": {
        "example": {
            "yolo_model": "yolov8n.pt",
            "yolo_confidence_threshold": 0.3,
            "target_fps": 1.0,
            "embedding_model": "clip-vit-base-patch32",
            "max_cost_per_clip_eur": 0.01
        }
    }}
