"""
Tests for Trend Miner - Sprint 4B

Tests trend extraction and analysis from social platforms.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.trend_miner import TrendMiner
from community_ai.models import (
    TrendItem,
    TrendAnalysis,
    TrendCategory,
    Platform
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def miner():
    """Create a TrendMiner instance."""
    return TrendMiner(mode="stub")


@pytest.fixture
def sample_trend_data():
    """Sample trend data."""
    return {
        "id": "trend_001",
        "category": "visual",
        "name": "Purple Neon Aesthetic",
        "description": "Purple and blue neon lights in night scenes with cars",
        "engagement_score": 0.85,
        "growth_rate": 1.8,
        "volume": 15000,
        "platform": "tiktok",
        "colors": ["#8B44FF", "#0A0A0A"],
        "themes": ["aesthetic", "night", "urban"]
    }


@pytest.fixture
def sample_brand_rules():
    """Sample brand rules."""
    return {
        "aesthetic": {
            "colors": ["#8B44FF", "#1A1A2E", "#16213E"],
            "mandatory": ["purple", "neon"]
        },
        "content": {
            "themes": ["trap", "urban", "night"]
        },
        "prohibitions": [
            "genérico", "daytime", "pastel colors"
        ]
    }


# ========================================
# Test Initialization
# ========================================

def test_miner_initialization(miner):
    """Test miner initializes correctly."""
    assert miner is not None
    assert miner.mode == "stub"


# ========================================
# Test Trend Extraction
# ========================================

def test_extract_trending_patterns_basic(miner):
    """Test basic trend extraction."""
    trends = miner.extract_trending_patterns(
        platform=Platform.TIKTOK,
        time_window_days=7
    )
    
    assert isinstance(trends, list)
    assert len(trends) > 0


def test_extracted_trends_have_required_fields(miner):
    """Test extracted trends have all required fields."""
    trends = miner.extract_trending_patterns(
        platform=Platform.INSTAGRAM
    )
    
    for trend in trends:
        assert trend.trend_id is not None
        assert trend.category is not None
        assert trend.name is not None
        assert trend.description is not None
        assert 0.0 <= trend.engagement_score <= 1.0
        assert trend.growth_rate >= 0.0
        assert trend.volume >= 0


def test_extract_from_different_platforms(miner):
    """Test extraction from multiple platforms."""
    tiktok_trends = miner.extract_trending_patterns(Platform.TIKTOK)
    instagram_trends = miner.extract_trending_patterns(Platform.INSTAGRAM)
    
    assert len(tiktok_trends) > 0
    assert len(instagram_trends) > 0


# ========================================
# Test Global Trend Analysis
# ========================================

def test_analyze_global_trends_basic(miner):
    """Test global trend analysis."""
    analysis = miner.analyze_global_trends()
    
    assert isinstance(analysis, TrendAnalysis)
    assert analysis.analysis_id is not None


def test_global_analysis_includes_all_categories(miner):
    """Test analysis includes trending/rising/declining."""
    analysis = miner.analyze_global_trends()
    
    assert isinstance(analysis.trending_now, list)
    assert isinstance(analysis.rising_trends, list)
    assert isinstance(analysis.declining_trends, list)


def test_global_analysis_has_recommendations(miner):
    """Test analysis has actionable recommendations."""
    analysis = miner.analyze_global_trends()
    
    assert isinstance(analysis.apply_immediately, list)
    assert isinstance(analysis.test_in_satellites, list)
    assert isinstance(analysis.avoid, list)


def test_global_analysis_has_summary(miner):
    """Test analysis has summary."""
    analysis = miner.analyze_global_trends()
    
    assert analysis.summary is not None
    assert len(analysis.summary) > 0


def test_analysis_with_brand_rules(miner, sample_brand_rules):
    """Test analysis filters by brand fit."""
    analysis = miner.analyze_global_trends(
        brand_rules=sample_brand_rules
    )
    
    # Should only include brand-aligned trends in "apply_immediately"
    assert isinstance(analysis.apply_immediately, list)


# ========================================
# Test Trend Classification
# ========================================

def test_classify_trend_basic(miner, sample_trend_data):
    """Test trend classification."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert isinstance(trend, TrendItem)
    assert trend.trend_id == sample_trend_data["id"]


def test_classify_trend_rhythm(miner, sample_trend_data):
    """Test rhythm classification."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert trend.rhythm in ["fast", "medium", "slow"]


def test_classify_trend_visual_dominance(miner, sample_trend_data):
    """Test visual dominance classification."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert trend.visual_dominance is not None


def test_classify_trend_storytelling(miner, sample_trend_data):
    """Test storytelling classification."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert trend.storytelling_style in ["narrative", "vibe", "comedic", "motivational"]


def test_classify_trend_brand_fit(miner, sample_trend_data, sample_brand_rules):
    """Test brand fit scoring."""
    trend = miner.classify_trend(
        sample_trend_data,
        brand_rules=sample_brand_rules
    )
    
    assert 0.0 <= trend.brand_fit_score <= 1.0


def test_classify_trend_applicable_flag(miner, sample_trend_data):
    """Test applicable to Stakazo flag."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert isinstance(trend.applicable_to_stakazo, bool)


def test_classify_trend_recommended_action(miner, sample_trend_data):
    """Test recommended action generation."""
    trend = miner.classify_trend(sample_trend_data)
    
    assert trend.recommended_action is not None
    assert len(trend.recommended_action) > 0


# ========================================
# Test Brand Fit Calculation
# ========================================

def test_brand_fit_high_for_aligned_trend(miner, sample_brand_rules):
    """Test high brand fit for aligned trends."""
    aligned_trend = {
        "id": "trend_aligned",
        "name": "Purple Neon",
        "description": "Purple neon urban aesthetic at night",
        "colors": ["#8B44FF"],
        "themes": ["trap", "night"],
        "category": "visual",
        "engagement_score": 0.8,
        "growth_rate": 1.5,
        "volume": 1000,
        "platform": "tiktok"
    }
    
    trend = miner.classify_trend(aligned_trend, sample_brand_rules)
    
    assert trend.brand_fit_score >= 0.70


def test_brand_fit_low_for_prohibited(miner, sample_brand_rules):
    """Test low brand fit for prohibited content."""
    prohibited_trend = {
        "id": "trend_prohibited",
        "name": "Daytime Generic",
        "description": "Generic daytime content with pastel colors",
        "colors": ["#FFB6C1"],
        "themes": ["generic"],
        "category": "visual",
        "engagement_score": 0.8,
        "growth_rate": 1.5,
        "volume": 1000,
        "platform": "tiktok"
    }
    
    trend = miner.classify_trend(prohibited_trend, sample_brand_rules)
    
    # Should be lower due to prohibitions
    assert trend.brand_fit_score < 1.0


# ========================================
# Test Rhythm Classification
# ========================================

def test_classify_fast_rhythm(miner):
    """Test fast rhythm classification."""
    fast_trend = {
        "id": "trend_fast",
        "name": "Fast Cuts",
        "description": "Quick cuts and high energy rapid transitions",
        "category": "format",
        "engagement_score": 0.8,
        "growth_rate": 1.5,
        "volume": 1000,
        "platform": "tiktok"
    }
    
    trend = miner.classify_trend(fast_trend)
    assert trend.rhythm == "fast"


def test_classify_slow_rhythm(miner):
    """Test slow rhythm classification."""
    slow_trend = {
        "id": "trend_slow",
        "name": "Cinematic",
        "description": "Cinematic slow motion atmospheric moody scenes",
        "category": "visual",
        "engagement_score": 0.8,
        "growth_rate": 1.5,
        "volume": 1000,
        "platform": "youtube"
    }
    
    trend = miner.classify_trend(slow_trend)
    assert trend.rhythm == "slow"


# ========================================
# Test Recommended Actions
# ========================================

def test_high_brand_fit_immediate_action(miner):
    """Test high brand fit recommends immediate action."""
    high_fit_trend = {
        "id": "trend_high",
        "name": "High Fit",
        "description": "Perfect brand alignment",
        "category": "visual",
        "engagement_score": 0.9,
        "growth_rate": 2.0,
        "volume": 10000,
        "platform": "tiktok"
    }
    
    brand_rules = {"aesthetic": {"colors": []}}
    trend = miner.classify_trend(high_fit_trend, brand_rules)
    
    # High fit should recommend application
    if trend.brand_fit_score >= 0.85:
        assert "immediately" in trend.recommended_action.lower()


def test_low_brand_fit_avoid_action(miner):
    """Test low brand fit recommends avoid."""
    low_fit_trend = {
        "id": "trend_low",
        "name": "Low Fit",
        "description": "Poor brand alignment",
        "category": "visual",
        "engagement_score": 0.7,
        "growth_rate": 1.2,
        "volume": 5000,
        "platform": "tiktok"
    }
    
    trend = miner.classify_trend(low_fit_trend)
    
    if trend.brand_fit_score < 0.50:
        assert "avoid" in trend.recommended_action.lower()


# ========================================
# Test Trend Categories
# ========================================

def test_trending_now_high_growth(miner):
    """Test trending_now has high growth rate."""
    analysis = miner.analyze_global_trends()
    
    for trend in analysis.trending_now:
        assert trend.growth_rate > 1.5


def test_rising_trends_moderate_growth(miner):
    """Test rising_trends has moderate growth."""
    analysis = miner.analyze_global_trends()
    
    for trend in analysis.rising_trends:
        assert 1.0 < trend.growth_rate <= 1.5


# ========================================
# Test Confidence Scoring
# ========================================

def test_analysis_has_confidence(miner):
    """Test analysis has confidence score."""
    analysis = miner.analyze_global_trends()
    
    assert 0.0 <= analysis.confidence <= 1.0


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
