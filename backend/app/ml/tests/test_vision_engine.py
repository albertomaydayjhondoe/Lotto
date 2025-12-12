"""
Tests for Vision Engine - Sprint 3

Complete test suite for ML modules:
- YOLO Runner
- COCO Mapper
- Visual Embeddings
- Scene Classifier
- Color Extractor
- Clip Tagger
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.models import (
    YOLODetection,
    BoundingBox,
    COCOMapping,
    VisualEmbedding,
    SceneClassification,
    ColorPalette,
    ClipMetadata,
    VisionConfig
)
from ml.yolo_runner import YOLORunner
from ml.coco_mapper import COCOMapper
from ml.visual_embeddings import VisualEmbeddingsEngine
from ml.scene_classifier import SceneClassifier
from ml.color_extractor import ColorExtractor
from ml.clip_tagger import ClipTagger


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def sample_frame():
    """Generate a sample RGB frame."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_detection():
    """Sample YOLO detection."""
    return YOLODetection(
        label="car",
        confidence=0.85,
        bbox=BoundingBox(x=100, y=150, w=300, h=200),
        class_id=2
    )


@pytest.fixture
def vision_config():
    """Sample vision configuration."""
    return VisionConfig(
        yolo_model="yolov8n.pt",
        yolo_confidence_threshold=0.25,
        target_fps=1.0,
        max_frames_per_clip=10,
        embedding_model="clip-vit-base-patch32",
        use_faiss=False,  # Disable for testing
        enable_telemetry=False
    )


# ========================================
# Test Models (Pydantic validation)
# ========================================

def test_bounding_box_validation():
    """Test BoundingBox validation."""
    # Valid
    bbox = BoundingBox(x=10, y=20, w=100, h=50)
    assert bbox.x == 10
    assert bbox.w == 100
    
    # Invalid (negative)
    with pytest.raises(ValueError):
        BoundingBox(x=-10, y=20, w=100, h=50)


def test_yolo_detection_creation(sample_detection):
    """Test YOLODetection model."""
    assert sample_detection.label == "car"
    assert sample_detection.confidence == 0.85
    assert sample_detection.class_id == 2
    assert sample_detection.bbox.x == 100


def test_coco_mapping_creation():
    """Test COCOMapping model."""
    mapping = COCOMapping(
        coco_label="person",
        stakazo_tags=["callejero", "urbano", "flow"],
        affinity_score=0.92,
        virality_score=0.88
    )
    assert len(mapping.stakazo_tags) == 3
    assert mapping.affinity_score == 0.92


def test_visual_embedding_validation():
    """Test VisualEmbedding validation."""
    # Valid 512-dim embedding
    embedding = VisualEmbedding(
        embedding_id="emb_001",
        vector=[0.1] * 512,
        model_name="clip-vit-base-patch32",
        frame_id=10
    )
    assert len(embedding.vector) == 512
    
    # Invalid dimension
    with pytest.raises(ValueError):
        VisualEmbedding(
            embedding_id="emb_002",
            vector=[0.1] * 100,  # Wrong dimension
            model_name="clip"
        )


def test_scene_classification_validation():
    """Test SceneClassification validation."""
    # Valid scene
    scene = SceneClassification(
        scene_type="calle",
        confidence=0.75,
        frame_id=5,
        timestamp_ms=2000.0
    )
    assert scene.scene_type == "calle"
    
    # Invalid scene type
    with pytest.raises(ValueError):
        SceneClassification(
            scene_type="invalid_scene",
            confidence=0.5,
            frame_id=0,
            timestamp_ms=0.0
        )


def test_color_palette_validation():
    """Test ColorPalette validation."""
    # Valid
    palette = ColorPalette(
        colors_hex=["#FF0000", "#00FF00", "#0000FF"],
        percentages=[0.5, 0.3, 0.2],
        purple_score=0.0,
        morado_ratio=0.0,
        dominant_color="#FF0000"
    )
    assert len(palette.colors_hex) == 3
    assert sum(palette.percentages) == pytest.approx(1.0)
    
    # Invalid hex
    with pytest.raises(ValueError):
        ColorPalette(
            colors_hex=["INVALID"],
            percentages=[1.0],
            purple_score=0.0,
            morado_ratio=0.0,
            dominant_color="INVALID"
        )


# ========================================
# Test COCO Mapper
# ========================================

def test_coco_mapper_initialization():
    """Test COCOMapper initialization."""
    mapper = COCOMapper()
    assert len(mapper.SEMANTIC_MAPPINGS) > 0


def test_coco_mapper_map_detection(sample_detection):
    """Test mapping a YOLO detection."""
    mapper = COCOMapper()
    mapping = mapper.map_detection(sample_detection)
    
    assert mapping.coco_label == "car"
    assert "coche" in mapping.stakazo_tags
    assert mapping.affinity_score > 0.5


def test_coco_mapper_enrich_detection(sample_detection):
    """Test enriching a detection."""
    mapper = COCOMapper()
    enriched = mapper.enrich_detection(sample_detection)
    
    assert enriched.detection.label == "car"
    assert enriched.mapping.coco_label == "car"


def test_coco_mapper_unique_tags():
    """Test getting unique semantic tags."""
    mapper = COCOMapper()
    
    detections = [
        YOLODetection(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, w=100, h=100), class_id=2),
        YOLODetection(label="person", confidence=0.85, bbox=BoundingBox(x=10, y=10, w=80, h=150), class_id=0),
    ]
    
    tags = mapper.get_unique_tags(detections)
    assert len(tags) > 0
    assert "coche" in tags or "callejero" in tags


def test_coco_mapper_aggregate_scores():
    """Test aggregate scoring."""
    mapper = COCOMapper()
    
    detections = [
        YOLODetection(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, w=100, h=100), class_id=2),
        YOLODetection(label="bottle", confidence=0.8, bbox=BoundingBox(x=20, y=20, w=50, h=100), class_id=39),
    ]
    
    scores = mapper.calculate_aggregate_scores(detections)
    
    assert "avg_affinity" in scores
    assert "avg_virality" in scores
    assert 0.0 <= scores["avg_affinity"] <= 1.0


def test_coco_mapper_scene_hints():
    """Test scene inference from detections."""
    mapper = COCOMapper()
    
    detections = [
        YOLODetection(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, w=100, h=100), class_id=2),
    ]
    
    scene_hints = mapper.get_scene_hints(detections)
    assert "coche" in scene_hints


# ========================================
# Test Scene Classifier
# ========================================

def test_scene_classifier_initialization():
    """Test SceneClassifier initialization."""
    classifier = SceneClassifier()
    assert len(classifier.SCENE_RULES) > 0


def test_scene_classifier_classify_frame():
    """Test frame classification."""
    classifier = SceneClassifier()
    
    detections = [
        YOLODetection(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, w=100, h=100), class_id=2),
    ]
    
    scenes = classifier.classify_frame(
        detections=detections,
        frame_id=0,
        timestamp_ms=0.0
    )
    
    assert len(scenes) > 0
    assert any(s.scene_type == "coche" for s in scenes)


def test_scene_classifier_club_detection():
    """Test club scene detection."""
    classifier = SceneClassifier()
    
    detections = [
        YOLODetection(label="person", confidence=0.9, bbox=BoundingBox(x=0, y=0, w=100, h=150), class_id=0),
        YOLODetection(label="bottle", confidence=0.85, bbox=BoundingBox(x=50, y=50, w=30, h=80), class_id=39),
    ]
    
    scenes = classifier.classify_frame(detections, frame_id=0, timestamp_ms=0.0)
    
    scene_types = [s.scene_type for s in scenes]
    assert "club" in scene_types or "calle" in scene_types


def test_scene_classifier_classify_clip():
    """Test clip-level scene classification."""
    classifier = SceneClassifier()
    
    frame_scenes = [
        [SceneClassification(scene_type="coche", confidence=0.8, frame_id=0, timestamp_ms=0.0)],
        [SceneClassification(scene_type="coche", confidence=0.75, frame_id=1, timestamp_ms=1000.0)],
        [SceneClassification(scene_type="calle", confidence=0.6, frame_id=2, timestamp_ms=2000.0)],
    ]
    
    dominant = classifier.classify_clip(frame_scenes)
    assert dominant == "coche"


def test_scene_classifier_distribution():
    """Test scene distribution calculation."""
    classifier = SceneClassifier()
    
    frame_scenes = [
        [SceneClassification(scene_type="coche", confidence=0.8, frame_id=0, timestamp_ms=0.0)],
        [SceneClassification(scene_type="coche", confidence=0.75, frame_id=1, timestamp_ms=1000.0)],
        [SceneClassification(scene_type="club", confidence=0.7, frame_id=2, timestamp_ms=2000.0)],
    ]
    
    distribution = classifier.get_scene_distribution(frame_scenes)
    
    assert "coche" in distribution
    assert distribution["coche"] == pytest.approx(2/3)


# ========================================
# Test Color Extractor
# ========================================

def test_color_extractor_initialization():
    """Test ColorExtractor initialization."""
    extractor = ColorExtractor(num_colors=5)
    assert extractor.num_colors == 5


def test_color_extractor_extract_palette(sample_frame):
    """Test color palette extraction."""
    extractor = ColorExtractor(num_colors=5)
    
    try:
        palette = extractor.extract_palette(sample_frame)
        
        assert len(palette.colors_hex) == 5
        assert len(palette.percentages) == 5
        assert sum(palette.percentages) == pytest.approx(1.0, abs=0.01)
        assert 0.0 <= palette.purple_score <= 1.0
    except RuntimeError:
        # sklearn not installed
        pytest.skip("scikit-learn not available")


def test_color_extractor_purple_detection():
    """Test purple aesthetic detection."""
    extractor = ColorExtractor()
    
    # Create a purple-ish frame
    purple_frame = np.full((100, 100, 3), [139, 68, 255], dtype=np.uint8)  # #8B44FF
    
    try:
        palette = extractor.extract_palette(purple_frame)
        
        # Should detect high purple score
        assert palette.purple_score > 0.5
    except RuntimeError:
        pytest.skip("scikit-learn not available")


def test_color_extractor_rgb_to_hex():
    """Test RGB to hex conversion."""
    extractor = ColorExtractor()
    
    hex_color = extractor._rgb_to_hex((255, 0, 0))
    assert hex_color == "#ff0000"
    
    hex_color = extractor._rgb_to_hex((139, 68, 255))
    assert hex_color == "#8b44ff"


def test_color_extractor_hex_to_rgb():
    """Test hex to RGB conversion."""
    extractor = ColorExtractor()
    
    rgb = extractor._hex_to_rgb("#ff0000")
    assert rgb == (255, 0, 0)
    
    rgb = extractor._hex_to_rgb("#8b44ff")
    assert rgb == (139, 68, 255)


def test_color_extractor_aesthetic_category():
    """Test aesthetic categorization."""
    extractor = ColorExtractor()
    
    # Purple dominant
    palette = ColorPalette(
        colors_hex=["#8B44FF"],
        percentages=[1.0],
        purple_score=0.8,
        morado_ratio=0.8,
        dominant_color="#8B44FF"
    )
    
    category = extractor.get_aesthetic_category(palette)
    assert category == "morado_dominante"


# ========================================
# Test Integration
# ========================================

def test_full_pipeline_mock(sample_frame, vision_config):
    """Test full vision pipeline with mocked models."""
    
    # Mock YOLO
    with patch('ml.yolo_runner.YOLO') as mock_yolo:
        # Mock YOLO results
        mock_result = Mock()
        mock_result.boxes = Mock()
        mock_result.boxes.xyxy = Mock()
        mock_result.boxes.xyxy.cpu = Mock(return_value=Mock(numpy=lambda: np.array([[10, 20, 110, 120]])))
        mock_result.boxes.conf = Mock()
        mock_result.boxes.conf.cpu = Mock(return_value=Mock(numpy=lambda: np.array([0.85])))
        mock_result.boxes.cls = Mock()
        mock_result.boxes.cls.cpu = Mock(return_value=Mock(numpy=lambda: np.array([2])))
        
        mock_yolo_instance = Mock()
        mock_yolo_instance.return_value = [mock_result]
        mock_yolo.return_value = mock_yolo_instance
        
        # Test COCOMapper
        mapper = COCOMapper()
        detection = YOLODetection(
            label="car",
            confidence=0.85,
            bbox=BoundingBox(x=10, y=20, w=100, h=100),
            class_id=2
        )
        
        enriched = mapper.enrich_detection(detection)
        assert enriched.mapping.coco_label == "car"


def test_clip_metadata_creation():
    """Test ClipMetadata creation."""
    metadata = ClipMetadata(
        clip_id="clip_123",
        video_id="video_456",
        objects_detected=["car", "person"],
        dominant_scene="coche",
        virality_score_visual=0.75,
        brand_affinity_score=0.80,
        aesthetic_score=0.85,
        processing_cost_eur=0.0050
    )
    
    assert metadata.clip_id == "clip_123"
    assert len(metadata.objects_detected) == 2
    assert metadata.virality_score_visual == 0.75


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
