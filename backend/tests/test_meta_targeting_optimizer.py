"""
Tests for Meta Targeting Optimizer (PASO 10.12).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.meta_targeting_optimizer.schemas import (
    SegmentMetrics,
    SegmentType,
    GenderSplit,
)
from app.meta_targeting_optimizer.scoring_engine import BayesianScoringEngine
from app.meta_targeting_optimizer.geo_allocator import GeoAllocator
from app.meta_targeting_optimizer.audience_builder import AudienceBuilder
from app.meta_targeting_optimizer.optimizer import MetaTargetingOptimizer


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def scoring_engine():
    """Scoring engine instance."""
    return BayesianScoringEngine()


@pytest.fixture
def geo_allocator():
    """Geo allocator instance."""
    return GeoAllocator()


@pytest.fixture
def audience_builder():
    """Audience builder instance."""
    return AudienceBuilder()


@pytest.fixture
def optimizer(mock_db):
    """Optimizer instance with mock DB."""
    return MetaTargetingOptimizer(db=mock_db, mode="stub")


# ============================================================================
# Bayesian Scoring Engine Tests
# ============================================================================

def test_bayesian_smoothing(scoring_engine):
    """Test Bayesian smoothing calculation."""
    # With low sample size, should be close to prior
    smoothed = scoring_engine.bayesian_smoothing(
        observed=0.05,
        prior=0.015,
        sample_size=10
    )
    assert 0.015 < smoothed < 0.05
    assert smoothed < 0.03  # Should be pulled toward prior
    
    # With high sample size, should be close to observed
    smoothed = scoring_engine.bayesian_smoothing(
        observed=0.05,
        prior=0.015,
        sample_size=5000
    )
    assert smoothed > 0.045  # Should be close to observed


def test_confidence_computation(scoring_engine):
    """Test confidence scoring based on sample size."""
    # Low impressions = low confidence
    conf_low = scoring_engine.compute_confidence(50)
    assert conf_low < 0.3
    
    # Medium impressions = medium confidence
    conf_med = scoring_engine.compute_confidence(300)
    assert 0.3 <= conf_med < 0.6
    
    # High impressions = high confidence
    conf_high = scoring_engine.compute_confidence(1500)
    assert 0.6 <= conf_high < 0.9
    
    # Very high impressions = very high confidence
    conf_very_high = scoring_engine.compute_confidence(5000)
    assert conf_very_high >= 0.9


def test_normalize_score(scoring_engine):
    """Test score normalization."""
    # Value at target should be ~0.5
    norm = scoring_engine.normalize_score(2.5, 2.5)
    assert 0.4 <= norm <= 0.6
    
    # Value at 2x target should be ~1.0
    norm = scoring_engine.normalize_score(5.0, 2.5)
    assert norm >= 0.9
    
    # Value at 0 should be 0.0
    norm = scoring_engine.normalize_score(0.0, 2.5)
    assert norm == 0.0


def test_segment_scoring(scoring_engine):
    """Test complete segment scoring."""
    metrics = SegmentMetrics(
        impressions=2000,
        clicks=60,
        conversions=10,
        spend=100.0,
        revenue=350.0,
        ctr=0.03,
        cvr=0.167,
        roas=3.5
    )
    
    score = scoring_engine.score_segment(
        metrics=metrics,
        segment_id="test_segment",
        segment_name="Test Segment",
        segment_type=SegmentType.INTEREST
    )
    
    assert score.segment_id == "test_segment"
    assert score.bayesian_ctr > 0
    assert score.bayesian_cvr > 0
    assert score.bayesian_roas > 0
    assert 0 <= score.composite_score <= 1.0
    assert 0 <= score.confidence <= 1.0
    assert score.is_fatigued == False


def test_fatigue_detection(scoring_engine):
    """Test fatigue detection for low-performing segments."""
    # Low CTR with sufficient impressions should be fatigued
    metrics = SegmentMetrics(
        impressions=1000,
        clicks=3,  # 0.3% CTR (way below prior)
        conversions=0,
        spend=50.0,
        revenue=0.0,
    )
    
    score = scoring_engine.score_segment(
        metrics=metrics,
        segment_id="fatigued_segment",
        segment_name="Fatigued Segment",
        segment_type=SegmentType.INTEREST
    )
    
    assert score.is_fatigued == True


def test_segment_ranking(scoring_engine):
    """Test segment ranking."""
    # Create multiple segments
    segments = []
    for i in range(5):
        metrics = SegmentMetrics(
            impressions=1000 + i * 100,
            clicks=20 + i * 5,
            conversions=3 + i,
            spend=50.0,
            revenue=150.0 + i * 20,
        )
        
        score = scoring_engine.score_segment(
            metrics=metrics,
            segment_id=f"segment_{i}",
            segment_name=f"Segment {i}",
            segment_type=SegmentType.INTEREST
        )
        segments.append(score)
    
    # Rank segments
    ranked = scoring_engine.rank_segments(segments)
    
    # Check ranks are assigned
    assert all(s.rank is not None for s in ranked)
    
    # Check descending order
    for i in range(len(ranked) - 1):
        assert ranked[i].composite_score >= ranked[i + 1].composite_score


# ============================================================================
# Geo Allocator Tests
# ============================================================================

def test_spain_minimum_allocation(geo_allocator):
    """Test Spain gets minimum 35% allocation."""
    total_budget = 1000.0
    geo_performance = geo_allocator.get_default_geo_performance()
    
    allocations = geo_allocator.allocate_budget(total_budget, geo_performance)
    
    # Find Spain allocation
    spain = next(a for a in allocations if a.country_code == "ES")
    
    assert spain.budget_pct >= 35.0
    assert spain.budget_amount >= 350.0


def test_total_allocation_100pct(geo_allocator):
    """Test total allocation sums to 100%."""
    total_budget = 1000.0
    geo_performance = geo_allocator.get_default_geo_performance()
    
    allocations = geo_allocator.allocate_budget(total_budget, geo_performance)
    
    total_pct = sum(a.budget_pct for a in allocations)
    total_amount = sum(a.budget_amount for a in allocations)
    
    assert abs(total_pct - 100.0) < 0.1  # Allow rounding
    assert abs(total_amount - total_budget) < 1.0


def test_engagement_score_computation(geo_allocator):
    """Test engagement score calculation."""
    # High performance = high engagement
    high_eng = geo_allocator.compute_engagement_score(
        ctr=0.03,
        cvr=0.05,
        roas=5.0,
        cpc=0.3
    )
    
    # Low performance = low engagement
    low_eng = geo_allocator.compute_engagement_score(
        ctr=0.01,
        cvr=0.01,
        roas=1.5,
        cpc=1.0
    )
    
    assert high_eng > low_eng


def test_allocation_validation(geo_allocator):
    """Test allocation validation."""
    total_budget = 1000.0
    geo_performance = geo_allocator.get_default_geo_performance()
    
    allocations = geo_allocator.allocate_budget(total_budget, geo_performance)
    
    is_valid, message = geo_allocator.validate_allocation(allocations)
    
    assert is_valid == True
    assert message == "Valid"


# ============================================================================
# Audience Builder Tests
# ============================================================================

def test_interest_ranking(audience_builder):
    """Test interest ranking."""
    # Create mock scores
    from app.meta_targeting_optimizer.schemas import SegmentScore
    
    scores = []
    for i in range(10):
        score = SegmentScore(
            segment_id=f"int_{i}",
            segment_name=f"Interest {i}",
            segment_type=SegmentType.INTEREST,
            metrics=SegmentMetrics(),
            composite_score=0.5 + i * 0.05,
            confidence=0.7
        )
        scores.append(score)
    
    ranked = audience_builder.rank_interests(scores, top_n=5)
    
    assert len(ranked) == 5
    assert all(isinstance(r.interest_id, str) for r in ranked)
    
    # Check descending order
    for i in range(len(ranked) - 1):
        assert ranked[i].score >= ranked[i + 1].score


def test_behavior_ranking(audience_builder):
    """Test behavior ranking."""
    from app.meta_targeting_optimizer.schemas import SegmentScore
    
    scores = []
    for i in range(10):
        score = SegmentScore(
            segment_id=f"beh_{i}",
            segment_name=f"Behavior {i}",
            segment_type=SegmentType.BEHAVIOR,
            metrics=SegmentMetrics(),
            composite_score=0.6 + i * 0.03,
            confidence=0.8
        )
        scores.append(score)
    
    ranked = audience_builder.rank_behaviors(scores, top_n=5)
    
    assert len(ranked) == 5
    assert all(isinstance(r.behavior_id, str) for r in ranked)


def test_pixel_to_interest_mapping(audience_builder):
    """Test genre-to-interest mapping."""
    interests = audience_builder.map_pixel_to_interests("action")
    
    assert len(interests) > 0
    assert any("action" in i.lower() for i in interests)
    
    # Test unknown genre
    unknown = audience_builder.map_pixel_to_interests("unknown_genre")
    assert len(unknown) == 0


def test_lookalike_generation_stub(audience_builder):
    """Test lookalike generation in stub mode."""
    lookalike = audience_builder.generate_lookalike_stub(
        source_audience_id="ca_12345",
        countries=["ES", "MX", "AR"],
        ratio=0.01
    )
    
    assert lookalike.source_audience_id == "ca_12345"
    assert lookalike.country_codes == ["ES", "MX", "AR"]
    assert lookalike.ratio == 0.01
    assert "1%" in lookalike.name


def test_custom_audience_generation_stub(audience_builder):
    """Test custom audience generation in stub mode."""
    audience = audience_builder.generate_custom_audience_stub("converters", 5000)
    
    assert "converters" in audience.audience_id
    assert audience.size == 5000
    assert "converters" in audience.name


# ============================================================================
# Full Optimizer Tests
# ============================================================================

@pytest.mark.asyncio
async def test_optimizer_run_optimization(optimizer, mock_db):
    """Test complete optimization run."""
    # Mock database queries
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    
    result = await optimizer.run_optimization(campaign_id=None, force_refresh=True)
    
    assert "run_id" in result
    assert "recommendations_count" in result
    assert "duration_ms" in result
    assert result["recommendations_count"] >= 0


@pytest.mark.asyncio
async def test_optimizer_segment_scores_stub(optimizer):
    """Test stub segment score generation."""
    scores = await optimizer._compute_segment_scores_stub()
    
    assert len(scores) > 0
    assert all(s.composite_score >= 0 for s in scores)
    assert any(s.segment_type == SegmentType.INTEREST for s in scores)
    assert any(s.segment_type == SegmentType.BEHAVIOR for s in scores)


@pytest.mark.asyncio
async def test_optimizer_generate_recommendation(optimizer):
    """Test recommendation generation."""
    from app.meta_targeting_optimizer.schemas import SegmentScore
    
    # Create mock scores
    scores = await optimizer._compute_segment_scores_stub()
    
    recommendation = await optimizer._generate_recommendation(
        run_id="test_run_123",
        campaign_id="campaign_1",
        adset_id="adset_1",
        segment_scores=scores
    )
    
    assert recommendation.campaign_id == "campaign_1"
    assert recommendation.adset_id == "adset_1"
    assert len(recommendation.countries) > 0
    assert "ES" in recommendation.countries  # Spain must be included
    assert len(recommendation.interests) > 0
    assert recommendation.total_budget > 0
    assert recommendation.expected_ctr > 0
    assert recommendation.expected_roas > 0


@pytest.mark.asyncio
async def test_optimizer_apply_recommendation_stub(optimizer, mock_db):
    """Test applying recommendation in stub mode."""
    # Mock recommendation in DB
    from app.meta_targeting_optimizer.models import MetaTargetingRecommendationModel
    from app.meta_targeting_optimizer.schemas import TargetingRecommendation
    
    mock_rec = MetaTargetingRecommendationModel(
        id=1,
        run_id="test_run",
        campaign_id="campaign_1",
        adset_id="adset_1",
        targeting_spec={
            "adset_id": "adset_1",
            "campaign_id": "campaign_1",
            "countries": ["ES", "MX"],
            "age_min": 25,
            "age_max": 54,
            "gender": "all",
            "interests": [],
            "behaviors": [],
            "custom_audiences": [],
            "lookalikes": [],
            "frequency_cap": 3,
            "frequency_window_days": 7,
            "total_budget": 500.0,
            "budget_per_segment": {},
            "reasoning": {},
            "expected_ctr": 0.02,
            "expected_cvr": 0.025,
            "expected_roas": 3.0,
            "confidence": 0.7,
            "geo_allocations": []
        },
        status="pending"
    )
    
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_rec
    
    result = await optimizer.apply_recommendation(recommendation_id=1, dry_run=True)
    
    assert result["success"] == True
    assert result["adset_id"] == "adset_1"
    assert "applied_changes" in result


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_optimization_pipeline(optimizer, mock_db):
    """Test complete optimization pipeline."""
    # Mock DB responses
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    
    # Run optimization
    result = await optimizer.run_optimization(
        campaign_id="campaign_1",
        force_refresh=True
    )
    
    assert result["recommendations_count"] > 0
    assert result["duration_ms"] > 0
    
    # Verify recommendations were saved
    assert mock_db.add.called
    assert mock_db.commit.called
