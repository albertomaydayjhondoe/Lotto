"""
Tests for Content Recommender - Sprint 4B

Tests creative recommendations for videoclips, wardrobe, narrative, aesthetics.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.content_recommender import ContentRecommender
from community_ai.models import (
    CreativeRecommendation,
    VideoclipRecommendation
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def recommender():
    """Create a ContentRecommender instance."""
    return ContentRecommender(mode="stub")


@pytest.fixture
def sample_performance_data():
    """Sample performance data."""
    return {
        "top_aesthetics": [
            {
                "name": "purple_neon",
                "avg_retention": 0.85,
                "count": 12,
                "brand_score": 0.92,
                "colors": ["#8B44FF", "#0A0A0A"],
                "scenes": ["noche", "coche"],
                "tags": ["purple", "neon", "night"]
            }
        ]
    }


@pytest.fixture
def sample_trend_data():
    """Sample trend data."""
    return {
        "trending_formats": [
            {
                "name": "fast_cuts",
                "description": "Aggressive cutting on beat",
                "engagement_score": 0.88,
                "brand_fit_score": 0.75
            }
        ],
        "applicable_trends": [
            {
                "name": "purple_aesthetic",
                "description": "Purple color grading trending",
                "brand_fit_score": 0.92
            }
        ]
    }


# ========================================
# Test Initialization
# ========================================

def test_recommender_initialization(recommender):
    """Test recommender initializes correctly."""
    assert recommender is not None
    assert recommender.mode == "stub"


# ========================================
# Test Official Content Recommendations
# ========================================

def test_recommend_official_content_basic(recommender):
    """Test basic official content recommendations."""
    recommendations = recommender.recommend_official_content(
        user_id="test_user"
    )
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_official_recommendations_are_brand_aligned(recommender):
    """Test official recommendations have high brand alignment."""
    recommendations = recommender.recommend_official_content(
        user_id="test_user"
    )
    
    for rec in recommendations:
        assert rec.brand_aligned is True
        assert rec.brand_score >= 0.70


def test_official_recommendations_have_details(recommender):
    """Test recommendations have complete details."""
    recommendations = recommender.recommend_official_content(
        user_id="test_user"
    )
    
    for rec in recommendations:
        assert rec.recommendation_id is not None
        assert rec.category is not None
        assert rec.title is not None
        assert rec.description is not None
        assert isinstance(rec.details, dict)


def test_recommend_with_performance_data(recommender, sample_performance_data):
    """Test recommendations with performance data."""
    recommendations = recommender.recommend_official_content(
        user_id="test_user",
        performance_data=sample_performance_data
    )
    
    assert len(recommendations) > 0


# ========================================
# Test Satellite Experiments
# ========================================

def test_recommend_satellite_experiments(recommender):
    """Test satellite experiment recommendations."""
    experiments = recommender.recommend_satellite_experiments(
        user_id="test_user"
    )
    
    assert isinstance(experiments, list)
    assert len(experiments) > 0


def test_satellite_experiments_can_be_non_aligned(recommender):
    """Test satellite experiments don't need brand alignment."""
    experiments = recommender.recommend_satellite_experiments(
        user_id="test_user"
    )
    
    # Satellites can have low brand score
    for exp in experiments:
        assert exp.brand_aligned is False or exp.brand_score < 0.70


def test_satellite_experiments_with_trends(recommender, sample_trend_data):
    """Test experiments with trend data."""
    experiments = recommender.recommend_satellite_experiments(
        user_id="test_user",
        trend_data=sample_trend_data
    )
    
    assert len(experiments) > 0


# ========================================
# Test Video Aesthetic Recommendations
# ========================================

def test_recommend_video_aesthetic_basic(recommender):
    """Test video aesthetic recommendation."""
    recommendation = recommender.recommend_video_aesthetic(
        track_name="Test Track",
        track_mood="dark"
    )
    
    assert isinstance(recommendation, CreativeRecommendation)
    assert recommendation.category == "aesthetic"


def test_aesthetic_includes_color_palette(recommender):
    """Test aesthetic includes color palette."""
    recommendation = recommender.recommend_video_aesthetic(
        track_name="Test Track",
        track_mood="dark"
    )
    
    assert len(recommendation.color_palette) > 0


def test_aesthetic_includes_scenes(recommender):
    """Test aesthetic includes scene types."""
    recommendation = recommender.recommend_video_aesthetic(
        track_name="Test Track",
        track_mood="energetic"
    )
    
    assert len(recommendation.scene_types) > 0


def test_aesthetic_mood_mapping(recommender):
    """Test different moods produce different aesthetics."""
    dark_rec = recommender.recommend_video_aesthetic("Track", "dark")
    energetic_rec = recommender.recommend_video_aesthetic("Track", "energetic")
    
    # Should have different characteristics
    assert dark_rec.color_palette != energetic_rec.color_palette or \
           dark_rec.scene_types != energetic_rec.scene_types


# ========================================
# Test Clip Styles
# ========================================

def test_recommend_clip_styles_instagram(recommender):
    """Test clip style recommendations for Instagram."""
    styles = recommender.recommend_clip_styles(
        content_type="reel",
        target_platform="instagram"
    )
    
    assert isinstance(styles, list)
    assert len(styles) > 0


def test_recommend_clip_styles_tiktok(recommender):
    """Test clip style recommendations for TikTok."""
    styles = recommender.recommend_clip_styles(
        content_type="video",
        target_platform="tiktok"
    )
    
    assert isinstance(styles, list)
    assert len(styles) > 0


def test_clip_styles_are_actionable(recommender):
    """Test clip styles are specific and actionable."""
    styles = recommender.recommend_clip_styles(
        content_type="reel",
        target_platform="instagram"
    )
    
    for style in styles:
        assert len(style) > 10  # Should be descriptive


# ========================================
# Test Creative Brainstorm
# ========================================

def test_creative_brainstorm_videoclip(recommender):
    """Test brainstorming for videoclip."""
    ideas = recommender.creative_brainstorm(topic="videoclip")
    
    assert isinstance(ideas, list)
    assert len(ideas) > 0


def test_creative_brainstorm_vestuario(recommender):
    """Test brainstorming for wardrobe."""
    ideas = recommender.creative_brainstorm(topic="vestuario")
    
    assert isinstance(ideas, list)
    assert len(ideas) > 0


def test_creative_brainstorm_narrative(recommender):
    """Test brainstorming for narrative."""
    ideas = recommender.creative_brainstorm(topic="narrative")
    
    assert isinstance(ideas, list)
    assert len(ideas) > 0


def test_brainstorm_with_constraints(recommender):
    """Test brainstorming with constraints."""
    ideas = recommender.creative_brainstorm(
        topic="videoclip",
        constraints=["low budget", "urban locations"]
    )
    
    assert len(ideas) > 0


# ========================================
# Test Videoclip Concept
# ========================================

def test_recommend_videoclip_concept_basic(recommender):
    """Test videoclip concept recommendation."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert isinstance(concept, VideoclipRecommendation)


def test_videoclip_concept_has_narrative(recommender):
    """Test concept has narrative."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert concept.narrative is not None
    assert len(concept.narrative) > 0


def test_videoclip_concept_has_aesthetic(recommender):
    """Test concept has aesthetic."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert concept.aesthetic is not None
    assert len(concept.color_palette) > 0


def test_videoclip_concept_has_scene_sequence(recommender):
    """Test concept has scene sequence."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert len(concept.scene_sequence) > 0


def test_videoclip_concept_has_wardrobe(recommender):
    """Test concept includes wardrobe."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert concept.wardrobe is not None
    assert len(concept.wardrobe) > 0


def test_videoclip_concept_has_props(recommender):
    """Test concept includes props."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert len(concept.props) > 0


def test_videoclip_concept_has_locations(recommender):
    """Test concept includes locations."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert len(concept.locations) > 0


def test_videoclip_concept_has_emotional_tone(recommender):
    """Test concept has emotional tone."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert concept.emotional_tone is not None
    assert concept.target_emotion is not None


def test_videoclip_concept_has_references(recommender):
    """Test concept includes references."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert len(concept.references) > 0


def test_videoclip_concept_brand_score(recommender):
    """Test concept has high brand score."""
    concept = recommender.recommend_videoclip_concept(
        track_name="Test Track",
        track_lyrics_theme="superación"
    )
    
    assert concept.brand_score >= 0.80


# ========================================
# Test Confidence Scoring
# ========================================

def test_recommendations_have_confidence(recommender):
    """Test recommendations have confidence scores."""
    recommendations = recommender.recommend_official_content(
        user_id="test_user"
    )
    
    for rec in recommendations:
        assert 0.0 <= rec.confidence <= 1.0


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
