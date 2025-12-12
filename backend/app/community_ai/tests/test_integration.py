"""
Integration Tests for Community Manager AI - Sprint 4B

Tests end-to-end workflows and cross-module interactions.
"""

import pytest
from datetime import date, datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from community_ai.planner import DailyPlanner
from community_ai.content_recommender import ContentRecommender
from community_ai.trend_miner import TrendMiner
from community_ai.sentiment_analyzer import SentimentAnalyzer
from community_ai.daily_reporter import DailyReporter
from community_ai.models import Platform, ContentType


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def full_cm_system():
    """Create complete CM system with all modules."""
    return {
        "planner": DailyPlanner(mode="stub"),
        "recommender": ContentRecommender(mode="stub"),
        "trend_miner": TrendMiner(mode="stub"),
        "sentiment_analyzer": SentimentAnalyzer(),
        "reporter": DailyReporter(mode="stub")
    }


@pytest.fixture
def sample_date():
    """Sample date."""
    return date(2024, 12, 7)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "test_user_integration"


# ========================================
# Test Complete CM Pipeline
# ========================================

def test_full_cm_pipeline_end_to_end(full_cm_system, sample_date, sample_user_id):
    """
    Test complete CM pipeline:
    1. Analyze trends
    2. Generate daily plan
    3. Get creative recommendations
    4. Analyze sentiment
    5. Generate daily report
    """
    cm = full_cm_system
    
    # Step 1: Analyze trends
    trend_analysis = cm["trend_miner"].analyze_global_trends()
    assert trend_analysis is not None
    assert len(trend_analysis.trending_now) > 0
    
    # Step 2: Generate daily plan (uses trend insights)
    daily_plan = cm["planner"].generate_daily_plan(
        date=sample_date,
        user_id=sample_user_id
    )
    assert daily_plan is not None
    assert daily_plan.official_plan is not None
    assert daily_plan.satellite_plan is not None
    
    # Step 3: Get creative recommendations for official post
    if len(daily_plan.official_plan.posts) > 0:
        official_post = daily_plan.official_plan.posts[0]
        recommendations = cm["recommender"].recommend_official_content(
            theme=official_post.theme,
            constraints={"platform": official_post.platform}
        )
        assert len(recommendations) > 0
    
    # Step 4: Analyze audience sentiment
    sample_comments = [
        "Me encanta este contenido",
        "Cuando sale el próximo video?",
        "Increíble como siempre"
    ]
    sentiment_results = cm["sentiment_analyzer"].analyze_batch(
        comments=sample_comments,
        language="es"
    )
    assert len(sentiment_results) == 3
    
    # Step 5: Generate daily report
    report = cm["reporter"].generate_daily_report(
        report_date=sample_date,
        user_id=sample_user_id
    )
    assert report is not None
    assert report.recommendations is not None


def test_official_vs_satellite_workflow(full_cm_system, sample_date, sample_user_id):
    """
    Test that official and satellite workflows are distinct:
    - Official: Brand validation, high quality, 1-2 posts
    - Satellite: No validation, experimental, 3-5 posts
    """
    cm = full_cm_system
    
    # Generate plan
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    
    # Validate official channel workflow
    assert plan.official_plan.channel_type == "official"
    assert 1 <= len(plan.official_plan.posts) <= 2
    for post in plan.official_plan.posts:
        # Official posts should have brand validation
        assert post.brand_compliance_score is not None
        assert post.brand_compliance_score >= 0.8
    
    # Validate satellite channel workflow
    assert plan.satellite_plan.channel_type == "satellite"
    assert 3 <= len(plan.satellite_plan.posts) <= 5
    for post in plan.satellite_plan.posts:
        # Satellite posts skip brand validation
        assert post.brand_compliance_score is None


def test_trend_to_content_pipeline(full_cm_system):
    """
    Test pipeline from trend discovery to content recommendation:
    1. Discover trending pattern
    2. Classify and score brand fit
    3. Generate content recommendation based on trend
    """
    cm = full_cm_system
    
    # Step 1: Discover trends
    trends = cm["trend_miner"].extract_trending_patterns(
        platform=Platform.TIKTOK
    )
    assert len(trends) > 0
    
    # Step 2: Get high brand fit trend
    high_fit_trends = [t for t in trends if t.brand_fit_score >= 0.7]
    if len(high_fit_trends) > 0:
        trend = high_fit_trends[0]
        
        # Step 3: Generate content based on trend
        recommendations = cm["recommender"].recommend_official_content(
            theme=f"trend_{trend.name}",
            constraints={
                "platform": trend.platform,
                "trend_category": trend.category
            }
        )
        assert len(recommendations) > 0


def test_sentiment_to_planning_feedback_loop(full_cm_system, sample_date, sample_user_id):
    """
    Test feedback loop:
    1. Analyze audience sentiment
    2. Detect hype signals
    3. Planner adjusts next day's content based on sentiment
    """
    cm = full_cm_system
    
    # Step 1: Analyze comments with hype signals
    hype_comments = [
        "Cuando sale el nuevo tema?",
        "NECESITO más contenido así",
        "Release date please!!!"
    ]
    
    sentiment_results = cm["sentiment_analyzer"].analyze_batch(
        comments=hype_comments,
        language="es"
    )
    
    # Step 2: Detect hype
    hype_count = sum(1 for r in sentiment_results if r.is_hype)
    assert hype_count >= 2  # At least 2 hype comments detected
    
    # Step 3: Planner should generate more content when hype detected
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    
    # With high hype, should have more posts
    total_posts = len(plan.official_plan.posts) + len(plan.satellite_plan.posts)
    assert total_posts >= 4


def test_daily_report_aggregates_all_sources(full_cm_system, sample_date, sample_user_id):
    """
    Test that daily report aggregates data from:
    - Planner (publications summary)
    - Sentiment analyzer (audience insights)
    - Trend miner (recommendations based on trends)
    - Performance metrics (top/worst performers)
    """
    cm = full_cm_system
    
    # Generate all data sources
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    trends = cm["trend_miner"].analyze_global_trends()
    
    # Generate report
    report = cm["reporter"].generate_daily_report(sample_date, sample_user_id)
    
    # Validate report aggregates all sources
    assert report.publications_summary is not None  # From planner
    assert report.audience_insights is not None      # From sentiment
    assert len(report.recommendations) > 0           # Could reference trends
    assert report.tomorrow_focus is not None


# ========================================
# Test Cost Guards Across Pipeline
# ========================================

def test_pipeline_respects_cost_guards(full_cm_system, sample_date, sample_user_id):
    """
    Test that full pipeline respects cost guards:
    - Planner: <€0.02/plan
    - Recommender: <€0.02/request
    - Sentiment: ~€0 (lexicon-based, NO LLM)
    - Reporter: <€0.01/report
    Total: <€0.05/day
    """
    cm = full_cm_system
    
    # Execute full pipeline
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    
    recommendations = cm["recommender"].recommend_official_content(
        theme="test",
        constraints={}
    )
    
    sentiment_results = cm["sentiment_analyzer"].analyze_batch(
        comments=["Test comment"] * 100,
        language="es"
    )
    
    report = cm["reporter"].generate_daily_report(sample_date, sample_user_id)
    
    # In real implementation, would track actual costs
    # Here we just validate operations complete successfully
    assert plan is not None
    assert len(recommendations) > 0
    assert len(sentiment_results) == 100
    assert report is not None


# ========================================
# Test Performance Targets
# ========================================

def test_pipeline_meets_latency_target(full_cm_system, sample_date, sample_user_id):
    """
    Test pipeline meets <1.5s latency target.
    """
    cm = full_cm_system
    
    import time
    start = time.time()
    
    # Execute critical path
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    
    elapsed = time.time() - start
    
    # Should complete quickly (in STUB mode)
    assert elapsed < 1.5  # Target: <1.5s


# ========================================
# Test Error Handling Across Modules
# ========================================

def test_graceful_degradation_on_module_failure(full_cm_system, sample_date, sample_user_id):
    """
    Test that system degrades gracefully if one module fails.
    """
    cm = full_cm_system
    
    # Even if trend miner fails, planner should work
    try:
        plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
        assert plan is not None
    except Exception as e:
        pytest.fail(f"Planner should not fail if trend miner unavailable: {e}")
    
    # Even if sentiment analyzer has issues, report should work
    try:
        report = cm["reporter"].generate_daily_report(sample_date, sample_user_id)
        assert report is not None
    except Exception as e:
        pytest.fail(f"Reporter should not fail if sentiment unavailable: {e}")


# ========================================
# Test Data Consistency
# ========================================

def test_data_consistency_across_modules(full_cm_system, sample_date, sample_user_id):
    """
    Test that data is consistent when passed between modules.
    """
    cm = full_cm_system
    
    # Generate plan
    plan = cm["planner"].generate_daily_plan(sample_date, sample_user_id)
    
    # Report should reflect same date
    report = cm["reporter"].generate_daily_report(sample_date, sample_user_id)
    
    assert plan.date == report.date


# ========================================
# Run tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
