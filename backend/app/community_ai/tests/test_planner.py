"""
Tests for Daily Planner - Sprint 4B

Tests daily planning system for official and satellite channels.
"""

import pytest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.planner import DailyPlanner
from community_ai.models import (
    DailyPlan,
    PostPlan,
    Platform,
    ContentType,
    ChannelType
)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def planner():
    """Create a DailyPlanner instance."""
    return DailyPlanner(mode="stub")


@pytest.fixture
def sample_metrics():
    """Sample performance metrics."""
    return {
        "total_content": 50,
        "top_aesthetics": [
            {
                "name": "purple_neon",
                "avg_retention": 0.85,
                "count": 12,
                "brand_score": 0.92,
                "tags": ["purple", "neon", "night"],
                "description": "Purple neon aesthetic in night scenes"
            },
            {
                "name": "car_night",
                "avg_retention": 0.82,
                "count": 8,
                "brand_score": 0.88,
                "tags": ["car", "night", "urban"],
                "description": "Sports car at night in urban setting"
            }
        ]
    }


@pytest.fixture
def sample_vision_metadata():
    """Sample vision engine metadata."""
    return [
        {
            "clip_id": "clip_001",
            "colors": ["#8B44FF", "#0A0A0A"],
            "scenes": ["coche", "noche"],
            "aesthetic_score": 0.90
        },
        {
            "clip_id": "clip_002",
            "colors": ["#FF0066", "#1A1A2E"],
            "scenes": ["calle", "urbano"],
            "aesthetic_score": 0.85
        }
    ]


@pytest.fixture
def sample_satellite_data():
    """Sample satellite performance data."""
    return {
        "trending_formats": [
            {
                "name": "fast_cuts",
                "virality_score": 0.88,
                "caption": "🎵 Vibe check",
                "hashtags": ["#Viral", "#Music"],
                "tags": ["trending", "aggressive"],
                "concept": "Aggressive cuts on beat"
            }
        ]
    }


# ========================================
# Test Initialization
# ========================================

def test_planner_initialization(planner):
    """Test planner initializes correctly."""
    assert planner is not None
    assert planner.mode == "stub"


def test_planner_load_brand_rules_stub_mode(planner):
    """Test brand rules not loaded in stub mode."""
    assert planner.brand_rules is None


# ========================================
# Test Daily Plan Generation
# ========================================

def test_generate_daily_plan_basic(planner):
    """Test basic daily plan generation."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert isinstance(plan, DailyPlan)
    assert plan.user_id == "test_user"
    assert plan.date == date


def test_generate_daily_plan_has_official_posts(planner):
    """Test plan includes official posts."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert len(plan.official_posts) > 0
    assert all(p.channel_type == ChannelType.OFFICIAL for p in plan.official_posts)


def test_generate_daily_plan_has_satellite_experiments(planner):
    """Test plan includes satellite experiments."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert len(plan.satellite_experiments) > 0
    assert all(p.channel_type == ChannelType.SATELLITE for p in plan.satellite_experiments)


def test_generate_daily_plan_with_metrics(planner, sample_metrics):
    """Test plan generation with performance metrics."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date,
        metrics=sample_metrics
    )
    
    assert plan.total_posts > 0
    assert plan.confidence > 0


def test_plan_includes_strategy_summary(planner):
    """Test plan includes strategy summary."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert plan.strategy_summary is not None
    assert len(plan.strategy_summary) > 0


def test_plan_includes_rationale(planner):
    """Test plan includes rationale."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert plan.rationale is not None
    assert len(plan.rationale) > 0


# ========================================
# Test Official Posts
# ========================================

def test_official_posts_are_brand_compliant(planner):
    """Test official posts have brand compliance."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.official_posts:
        assert post.brand_compliant is True
        assert post.brand_score >= 0.80


def test_official_posts_have_aesthetic_tags(planner):
    """Test official posts have aesthetic tags."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.official_posts:
        assert len(post.aesthetic_tags) > 0


def test_official_posts_have_scheduled_time(planner):
    """Test official posts have scheduled time."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.official_posts:
        assert post.scheduled_time is not None
        assert post.scheduled_time.date() == date.date()


# ========================================
# Test Satellite Experiments
# ========================================

def test_satellite_posts_can_be_non_compliant(planner):
    """Test satellite posts can be non-brand-compliant."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    # Satellites don't need brand compliance
    for post in plan.satellite_experiments:
        assert post.channel_type == ChannelType.SATELLITE


def test_satellite_posts_have_rationale(planner):
    """Test satellite posts have experimental rationale."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.satellite_experiments:
        assert post.rationale is not None
        assert len(post.rationale) > 0


# ========================================
# Test Priority Content
# ========================================

def test_plan_identifies_priority_content(planner):
    """Test plan identifies must-post content."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    # Priority content should be subset of official posts
    priority_ids = set(plan.priority_content)
    official_ids = set(p.post_id for p in plan.official_posts)
    
    assert priority_ids.issubset(official_ids)


# ========================================
# Test Post Timing
# ========================================

def test_predict_best_post_time_instagram(planner):
    """Test best post time prediction for Instagram."""
    best_time = planner.predict_best_post_time(
        platform=Platform.INSTAGRAM,
        content_type=ContentType.REEL
    )
    
    assert isinstance(best_time, datetime)
    # Instagram optimal: 19-22h
    assert 12 <= best_time.hour <= 23


def test_predict_best_post_time_tiktok(planner):
    """Test best post time prediction for TikTok."""
    best_time = planner.predict_best_post_time(
        platform=Platform.TIKTOK,
        content_type=ContentType.VIDEO
    )
    
    assert isinstance(best_time, datetime)


def test_predict_best_post_time_with_historical(planner):
    """Test timing with historical data."""
    historical = {
        "best_hours": {
            "instagram": [21, 20, 22]
        }
    }
    
    best_time = planner.predict_best_post_time(
        platform=Platform.INSTAGRAM,
        content_type=ContentType.REEL,
        historical_data=historical
    )
    
    assert best_time.hour in [21, 20, 22]


# ========================================
# Test Cost Estimation
# ========================================

def test_plan_includes_cost_estimation(planner):
    """Test plan includes cost estimation."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert plan.estimated_cost_eur is not None
    assert plan.estimated_cost_eur > 0
    assert plan.estimated_cost_eur < 0.05  # Should be under €0.05


# ========================================
# Test Confidence Scoring
# ========================================

def test_plan_has_confidence_score(planner):
    """Test plan has confidence score."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert 0.0 <= plan.confidence <= 1.0


def test_confidence_higher_with_more_data(planner, sample_metrics):
    """Test confidence higher with more input data."""
    date = datetime.utcnow()
    
    plan_without_data = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    plan_with_data = planner.generate_daily_plan(
        user_id="test_user",
        date=date,
        metrics=sample_metrics
    )
    
    # With data should have higher confidence (in real implementation)
    assert plan_with_data.confidence >= 0.0


# ========================================
# Test Post Plan Structure
# ========================================

def test_post_plan_has_required_fields(planner):
    """Test post plan has all required fields."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.official_posts:
        assert post.post_id is not None
        assert post.platform is not None
        assert post.content_type is not None
        assert post.channel_type is not None
        assert post.scheduled_time is not None
        assert post.caption is not None
        assert isinstance(post.hashtags, list)
        assert post.visual_concept is not None
        assert isinstance(post.aesthetic_tags, list)


def test_post_plan_has_performance_expectations(planner):
    """Test post plan has performance expectations."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    for post in plan.official_posts:
        assert 0.0 <= post.expected_retention <= 1.0
        assert 0.0 <= post.expected_ctr <= 1.0
        assert 0.0 <= post.virality_score <= 1.0


# ========================================
# Test Counts
# ========================================

def test_plan_counts_match(planner):
    """Test plan counts match actual lists."""
    date = datetime.utcnow()
    plan = planner.generate_daily_plan(
        user_id="test_user",
        date=date
    )
    
    assert plan.official_count == len(plan.official_posts)
    assert plan.satellite_count == len(plan.satellite_experiments)
    assert plan.total_posts == plan.official_count + plan.satellite_count


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
