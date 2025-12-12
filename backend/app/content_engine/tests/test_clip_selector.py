"""
Content Engine Integration Tests - Vision Engine

Tests for ClipSelector integration with Vision Engine.
"""

import pytest
import numpy as np
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.models import (
    ClipMetadata,
    ColorPalette,
    EnrichedDetection,
    YOLODetection,
    BoundingBox,
    COCOMapping
)
from content_engine.clip_selector import ClipSelector, create_clip_selector


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def sample_clip_metadata():
    """Sample ClipMetadata for testing."""
    return ClipMetadata(
        clip_id="clip_001",
        video_id="video_001",
        objects_detected=["car", "person"],
        dominant_scene="coche",
        color_palette=ColorPalette(
            colors_hex=["#8B44FF", "#1A1A2E"],
            percentages=[0.6, 0.4],
            purple_score=0.75,
            morado_ratio=0.6,
            dominant_color="#8B44FF"
        ),
        virality_score_visual=0.82,
        brand_affinity_score=0.78,
        aesthetic_score=0.85,
        processed_at=datetime.utcnow(),
        processing_cost_eur=0.0030
    )


@pytest.fixture
def low_quality_clip_metadata():
    """Low quality clip for comparison."""
    return ClipMetadata(
        clip_id="clip_002",
        video_id="video_001",
        objects_detected=["chair", "table"],
        dominant_scene="interior",
        color_palette=ColorPalette(
            colors_hex=["#CCCCCC", "#888888"],
            percentages=[0.7, 0.3],
            purple_score=0.1,
            morado_ratio=0.05,
            dominant_color="#CCCCCC"
        ),
        virality_score_visual=0.35,
        brand_affinity_score=0.40,
        aesthetic_score=0.30,
        processed_at=datetime.utcnow(),
        processing_cost_eur=0.0020
    )


# ========================================
# Test ClipSelector
# ========================================

def test_clip_selector_initialization():
    """Test ClipSelector initialization."""
    selector = ClipSelector()
    assert selector is not None


def test_clip_selector_score_clip(sample_clip_metadata):
    """Test clip scoring."""
    selector = ClipSelector()
    
    score = selector.score_clip(sample_clip_metadata)
    
    # High-quality clip should score high
    assert 0.7 <= score <= 1.0


def test_clip_selector_score_low_quality(low_quality_clip_metadata):
    """Test scoring low-quality clip."""
    selector = ClipSelector()
    
    score = selector.score_clip(low_quality_clip_metadata)
    
    # Low-quality clip should score low
    assert score < 0.6


def test_clip_selector_custom_weights(sample_clip_metadata):
    """Test custom scoring weights."""
    selector = ClipSelector()
    
    # Prioritize aesthetic over virality
    weights = {
        "virality": 0.2,
        "brand_affinity": 0.2,
        "aesthetic": 0.5,
        "scene_bonus": 0.1
    }
    
    score = selector.score_clip(sample_clip_metadata, weights=weights)
    
    # Should still be high because aesthetic is high
    assert score > 0.7


def test_select_best_clips(sample_clip_metadata, low_quality_clip_metadata):
    """Test selecting best clips from a list."""
    selector = ClipSelector()
    
    clips = [sample_clip_metadata, low_quality_clip_metadata]
    
    best = selector.select_best_clips(clips, top_k=1, min_score=0.5)
    
    # Should select the high-quality clip
    assert len(best) == 1
    assert best[0].clip_id == "clip_001"


def test_select_with_scene_filter(sample_clip_metadata, low_quality_clip_metadata):
    """Test filtering by scene."""
    selector = ClipSelector()
    
    clips = [sample_clip_metadata, low_quality_clip_metadata]
    
    # Filter for "coche" scene
    best = selector.select_best_clips(
        clips,
        top_k=5,
        min_score=0.0,
        filters={"dominant_scene": "coche"}
    )
    
    assert len(best) == 1
    assert best[0].dominant_scene == "coche"


def test_select_with_purple_filter(sample_clip_metadata, low_quality_clip_metadata):
    """Test filtering by purple aesthetic."""
    selector = ClipSelector()
    
    clips = [sample_clip_metadata, low_quality_clip_metadata]
    
    # Filter for purple score >= 0.5
    best = selector.select_best_clips(
        clips,
        top_k=5,
        min_score=0.0,
        filters={"min_purple_score": 0.5}
    )
    
    assert len(best) == 1
    assert best[0].color_palette.purple_score >= 0.5


def test_select_with_object_filter(sample_clip_metadata, low_quality_clip_metadata):
    """Test filtering by required objects."""
    selector = ClipSelector()
    
    clips = [sample_clip_metadata, low_quality_clip_metadata]
    
    # Filter for clips with "car"
    best = selector.select_best_clips(
        clips,
        top_k=5,
        min_score=0.0,
        filters={"required_objects": ["car"]}
    )
    
    assert len(best) == 1
    assert "car" in best[0].objects_detected


def test_publication_recommendation_instagram(sample_clip_metadata):
    """Test publication recommendation for Instagram."""
    selector = ClipSelector()
    
    rec = selector.get_publication_recommendation(sample_clip_metadata, platform="instagram")
    
    assert rec["platform"] == "instagram"
    assert rec["recommendation"] == "publish_immediately"
    assert rec["priority"] == "high"
    assert rec["score"] > 0.8


def test_publication_recommendation_tiktok(sample_clip_metadata):
    """Test publication recommendation for TikTok."""
    selector = ClipSelector()
    
    rec = selector.get_publication_recommendation(sample_clip_metadata, platform="tiktok")
    
    assert rec["platform"] == "tiktok"
    # TikTok prefers high-energy scenes like "coche"
    assert rec["score"] > 0.8


def test_publication_recommendation_low_quality(low_quality_clip_metadata):
    """Test recommendation for low-quality clip."""
    selector = ClipSelector()
    
    rec = selector.get_publication_recommendation(low_quality_clip_metadata, platform="instagram")
    
    assert rec["recommendation"] == "hold_for_review"
    assert rec["priority"] == "low"


def test_compare_clips(sample_clip_metadata, low_quality_clip_metadata):
    """Test comparing two clips."""
    selector = ClipSelector()
    
    comparison = selector.compare_clips(sample_clip_metadata, low_quality_clip_metadata)
    
    assert comparison["winner_clip_id"] == "clip_001"
    assert comparison["scores"]["clip_001"] > comparison["scores"]["clip_002"]
    assert comparison["score_difference"] > 0.2


def test_filter_by_aesthetic_purple(sample_clip_metadata, low_quality_clip_metadata):
    """Test filtering by purple aesthetic."""
    selector = ClipSelector()
    
    clips = [sample_clip_metadata, low_quality_clip_metadata]
    
    filtered = selector.filter_by_aesthetic(
        clips,
        aesthetic_type="morado_dominante",
        min_threshold=0.5
    )
    
    assert len(filtered) == 1
    assert filtered[0].clip_id == "clip_001"


def test_create_clip_selector():
    """Test factory function."""
    selector = create_clip_selector(initialize_vision=False)
    assert selector is not None
    assert isinstance(selector, ClipSelector)


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
