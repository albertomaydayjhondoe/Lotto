"""
Tests for Brand Aesthetic Extractor - Sprint 4

Tests visual DNA extraction from real content using Vision Engine.
"""

import pytest
import numpy as np
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from brand_engine.brand_aesthetic_extractor import BrandAestheticExtractor
from brand_engine.models import AestheticDNA
from ml.models import ClipMetadata, ColorPalette, SceneClassification


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def extractor():
    """Create a BrandAestheticExtractor instance."""
    return BrandAestheticExtractor()


@pytest.fixture
def sample_clips_metadata():
    """Sample ClipMetadata for testing."""
    clips = []
    
    # Purple aesthetic clips
    for i in range(10):
        clips.append(ClipMetadata(
            clip_id=f"purple_{i}",
            video_id=f"video_{i}",
            objects_detected=["car", "person", "cell_phone"],
            dominant_scene="coche",
            color_palette=ColorPalette(
                colors_hex=["#8B44FF", "#1A1A2E", "#16213E"],
                percentages=[0.5 + i * 0.01, 0.3, 0.2],
                purple_score=0.75 + i * 0.01,
                morado_ratio=0.6,
                dominant_color="#8B44FF"
            ),
            virality_score_visual=0.80 + i * 0.01,
            brand_affinity_score=0.75 + i * 0.01,
            aesthetic_score=0.85 + i * 0.01,
            processed_at=datetime.utcnow(),
            processing_cost_eur=0.0030
        ))
    
    # Dark aesthetic clips
    for i in range(5):
        clips.append(ClipMetadata(
            clip_id=f"dark_{i}",
            video_id=f"video_{i + 10}",
            objects_detected=["person", "bottle"],
            dominant_scene="club",
            color_palette=ColorPalette(
                colors_hex=["#0A0A0A", "#1C1C1C", "#2E2E2E"],
                percentages=[0.6, 0.25, 0.15],
                purple_score=0.1,
                morado_ratio=0.05,
                dominant_color="#0A0A0A"
            ),
            virality_score_visual=0.70,
            brand_affinity_score=0.65,
            aesthetic_score=0.75,
            processed_at=datetime.utcnow(),
            processing_cost_eur=0.0025
        ))
    
    return clips


# ========================================
# Test Color Analysis
# ========================================

def test_extractor_initialization(extractor):
    """Test extractor initializes correctly."""
    assert extractor is not None
    assert len(extractor.clips) == 0


def test_add_clips(extractor, sample_clips_metadata):
    """Test adding clips."""
    extractor.add_clips(sample_clips_metadata)
    
    assert len(extractor.clips) == len(sample_clips_metadata)


def test_extract_dominant_colors(extractor, sample_clips_metadata):
    """Test extracting dominant colors."""
    extractor.add_clips(sample_clips_metadata)
    
    colors = extractor.extract_dominant_colors(top_k=5)
    
    assert len(colors) <= 5
    assert "#8B44FF" in colors  # Purple should be dominant


def test_calculate_color_consistency(extractor, sample_clips_metadata):
    """Test calculating color consistency."""
    extractor.add_clips(sample_clips_metadata)
    
    consistency = extractor.calculate_color_consistency()
    
    assert 0.0 <= consistency <= 1.0
    assert consistency > 0.5  # Should have some consistency


def test_identify_color_palette(extractor, sample_clips_metadata):
    """Test identifying brand color palette."""
    extractor.add_clips(sample_clips_metadata)
    
    palette = extractor.identify_brand_palette()
    
    assert len(palette) > 0
    assert any("#8B44FF" in color for color in palette)


def test_calculate_purple_prevalence(extractor, sample_clips_metadata):
    """Test calculating purple prevalence."""
    extractor.add_clips(sample_clips_metadata)
    
    purple_ratio = extractor.calculate_purple_prevalence()
    
    assert 0.0 <= purple_ratio <= 1.0
    assert purple_ratio > 0.5  # Most clips are purple


# ========================================
# Test Scene Analysis
# ========================================

def test_analyze_recurring_scenes(extractor, sample_clips_metadata):
    """Test analyzing recurring scenes."""
    extractor.add_clips(sample_clips_metadata)
    
    scenes = extractor.analyze_recurring_scenes()
    
    assert "coche" in scenes
    assert scenes["coche"]["count"] > 5
    assert scenes["coche"]["percentage"] > 0.3


def test_identify_dominant_scenes(extractor, sample_clips_metadata):
    """Test identifying dominant scenes."""
    extractor.add_clips(sample_clips_metadata)
    
    dominant = extractor.identify_dominant_scenes(top_k=3)
    
    assert len(dominant) <= 3
    assert dominant[0][0] == "coche"  # Most common


def test_calculate_scene_diversity(extractor, sample_clips_metadata):
    """Test calculating scene diversity."""
    extractor.add_clips(sample_clips_metadata)
    
    diversity = extractor.calculate_scene_diversity()
    
    assert 0.0 <= diversity <= 1.0


# ========================================
# Test Object Analysis
# ========================================

def test_analyze_recurring_objects(extractor, sample_clips_metadata):
    """Test analyzing recurring objects."""
    extractor.add_clips(sample_clips_metadata)
    
    objects = extractor.analyze_recurring_objects()
    
    assert "car" in objects
    assert "person" in objects
    assert objects["car"]["count"] > 5


def test_identify_signature_objects(extractor, sample_clips_metadata):
    """Test identifying signature objects."""
    extractor.add_clips(sample_clips_metadata)
    
    signature = extractor.identify_signature_objects(min_frequency=0.5)
    
    assert len(signature) > 0
    assert "car" in signature or "person" in signature


# ========================================
# Test Aesthetic Patterns
# ========================================

def test_detect_aesthetic_patterns(extractor, sample_clips_metadata):
    """Test detecting aesthetic patterns."""
    extractor.add_clips(sample_clips_metadata)
    
    patterns = extractor.detect_aesthetic_patterns()
    
    assert len(patterns) > 0
    assert any("purple" in p.lower() for p in patterns)


def test_calculate_aesthetic_consistency(extractor, sample_clips_metadata):
    """Test calculating aesthetic consistency."""
    extractor.add_clips(sample_clips_metadata)
    
    consistency = extractor.calculate_aesthetic_consistency()
    
    assert 0.0 <= consistency <= 1.0


def test_identify_visual_motifs(extractor, sample_clips_metadata):
    """Test identifying visual motifs."""
    extractor.add_clips(sample_clips_metadata)
    
    motifs = extractor.identify_visual_motifs()
    
    assert len(motifs) > 0


# ========================================
# Test DNA Building
# ========================================

def test_build_dna_no_clips(extractor):
    """Test building DNA with no clips raises error."""
    with pytest.raises(ValueError, match="No clips"):
        extractor.build_aesthetic_dna()


def test_build_dna_complete(extractor, sample_clips_metadata):
    """Test building complete aesthetic DNA."""
    extractor.add_clips(sample_clips_metadata)
    
    dna = extractor.build_aesthetic_dna()
    
    assert isinstance(dna, AestheticDNA)
    assert len(dna.dominant_colors) > 0
    assert len(dna.recurring_scenes) > 0
    assert len(dna.signature_objects) > 0
    assert 0.0 <= dna.color_consistency_score <= 1.0


def test_dna_includes_percentages(extractor, sample_clips_metadata):
    """Test DNA includes percentage information."""
    extractor.add_clips(sample_clips_metadata)
    
    dna = extractor.build_aesthetic_dna()
    
    assert len(dna.scene_distribution) > 0
    total_percentage = sum(dna.scene_distribution.values())
    assert 0.99 <= total_percentage <= 1.01


def test_dna_purple_score(extractor, sample_clips_metadata):
    """Test DNA calculates purple prevalence."""
    extractor.add_clips(sample_clips_metadata)
    
    dna = extractor.build_aesthetic_dna()
    
    # Should detect high purple prevalence
    assert dna.color_consistency_score > 0.5


# ========================================
# Test Statistical Analysis
# ========================================

def test_calculate_color_variance(extractor, sample_clips_metadata):
    """Test calculating color variance across clips."""
    extractor.add_clips(sample_clips_metadata)
    
    variance = extractor.calculate_color_variance()
    
    assert variance >= 0


def test_analyze_aesthetic_evolution(extractor, sample_clips_metadata):
    """Test analyzing aesthetic evolution over time."""
    extractor.add_clips(sample_clips_metadata)
    
    evolution = extractor.analyze_aesthetic_evolution()
    
    assert "color_trend" in evolution
    assert "scene_trend" in evolution


# ========================================
# Test Filtering
# ========================================

def test_filter_by_aesthetic_score(extractor, sample_clips_metadata):
    """Test filtering clips by aesthetic score."""
    extractor.add_clips(sample_clips_metadata)
    
    high_aesthetic = extractor.filter_by_aesthetic_score(min_score=0.8)
    
    assert len(high_aesthetic) > 0
    assert all(c.aesthetic_score >= 0.8 for c in high_aesthetic)


def test_filter_by_scene(extractor, sample_clips_metadata):
    """Test filtering clips by scene."""
    extractor.add_clips(sample_clips_metadata)
    
    coche_clips = extractor.filter_by_scene("coche")
    
    assert len(coche_clips) > 0
    assert all(c.dominant_scene == "coche" for c in coche_clips)


def test_filter_by_color_palette(extractor, sample_clips_metadata):
    """Test filtering clips by color palette."""
    extractor.add_clips(sample_clips_metadata)
    
    purple_clips = extractor.filter_by_purple_aesthetic(min_score=0.5)
    
    assert len(purple_clips) > 0
    assert all(c.color_palette.purple_score >= 0.5 for c in purple_clips)


# ========================================
# Test Export
# ========================================

def test_export_dna(extractor, sample_clips_metadata, tmp_path):
    """Test exporting aesthetic DNA to JSON."""
    extractor.add_clips(sample_clips_metadata)
    dna = extractor.build_aesthetic_dna()
    
    export_path = tmp_path / "aesthetic_dna.json"
    extractor.export_dna(dna, str(export_path))
    
    assert export_path.exists()


def test_export_analysis_report(extractor, sample_clips_metadata, tmp_path):
    """Test exporting full analysis report."""
    extractor.add_clips(sample_clips_metadata)
    
    report_path = tmp_path / "analysis_report.json"
    extractor.export_analysis_report(str(report_path))
    
    assert report_path.exists()


# ========================================
# Test Summary
# ========================================

def test_get_summary(extractor, sample_clips_metadata):
    """Test getting summary statistics."""
    extractor.add_clips(sample_clips_metadata)
    
    summary = extractor.get_summary()
    
    assert "total_clips" in summary
    assert "dominant_colors" in summary
    assert "most_common_scene" in summary
    assert summary["total_clips"] == len(sample_clips_metadata)


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
