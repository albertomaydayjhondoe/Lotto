"""
Tests for ROAS Engine (PASO 10.5)

Comprehensive test suite for:
- ROAS calculation
- Bayesian smoothing
- Prediction engine
- Optimizer scaling
- Endpoint responses
- Outcome models
- Outlier detection
- Value attribution
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np

from app.meta_ads_orchestrator.roas_engine import (
    ROASCalculator,
    AttributionEngine,
    PredictionEngine,
)
from app.meta_ads_orchestrator.roas_integration import ROASInsightsIntegration
from app.meta_ads_orchestrator.roas_optimizer import ROASOptimizer
from app.models.database import (
    MetaPixelOutcomeModel,
    MetaAdInsightsModel,
    MetaROASMetricsModel,
)


@pytest.mark.asyncio
async def test_roas_formula():
    """
    Test 1: ROAS formula calculation.
    
    ROAS = Revenue / Cost
    """
    # Mock session
    session = AsyncMock()
    calculator = ROASCalculator(session)
    
    # Mock outcomes: 5 conversions @ $100 each = $500 revenue
    mock_outcomes = [
        MagicMock(value_usd=100.0) for _ in range(5)
    ]
    
    # Mock spend: $100
    calculator._get_pixel_outcomes = AsyncMock(return_value=mock_outcomes)
    calculator._get_ad_spend = AsyncMock(return_value=100.0)
    calculator._get_clicks = AsyncMock(return_value=200)
    
    # Calculate ROAS
    result = await calculator.calculate_roas(
        campaign_id=uuid4(),
        date_start=datetime.utcnow() - timedelta(days=7),
        date_end=datetime.utcnow(),
    )
    
    # Expected ROAS = 500 / 100 = 5.0
    assert result["actual_roas"] == 5.0
    assert result["total_revenue_usd"] == 500.0
    assert result["total_cost_usd"] == 100.0
    assert result["total_conversions"] == 5
    assert result["conversion_rate"] == 5 / 200  # 5 conversions / 200 clicks


@pytest.mark.asyncio
async def test_bayesian_smoothing():
    """
    Test 2: Bayesian smoothing for small samples.
    
    With few conversions, smoothed ROAS should be pulled towards prior (2.0).
    """
    session = AsyncMock()
    calculator = ROASCalculator(session)
    
    # Test with 1 conversion (very small sample)
    # Observed ROAS = 10.0, but with only 1 conversion
    smoothed = calculator._apply_bayesian_smoothing(
        observed_roas=10.0,
        conversions=1,
        spend=10.0,
    )
    
    # Smoothed should be closer to prior (2.0) than observed (10.0)
    assert smoothed < 10.0
    assert smoothed > 2.0
    
    # Test with many conversions (large sample)
    # With 100 conversions, should trust observed data more
    smoothed_large = calculator._apply_bayesian_smoothing(
        observed_roas=10.0,
        conversions=100,
        spend=1000.0,
    )
    
    # Should be closer to observed value
    assert smoothed_large > smoothed
    assert smoothed_large > 8.0  # Much closer to 10.0


@pytest.mark.asyncio
async def test_prediction_flow():
    """
    Test 3: ROAS prediction flow.
    
    Predict future ROAS using exponential moving average.
    """
    session = AsyncMock()
    prediction_engine = PredictionEngine(session)
    
    # Mock historical ROAS metrics
    mock_metrics = [
        MagicMock(actual_roas=3.0, date=datetime.utcnow() - timedelta(days=i))
        for i in range(10)
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_metrics
    session.execute = AsyncMock(return_value=mock_result)
    
    # Predict ROAS
    prediction = await prediction_engine.predict_roas(
        campaign_id=uuid4(),
        lookback_days=30,
    )
    
    # Should return prediction close to historical average
    assert "predicted_roas" in prediction
    assert prediction["predicted_roas"] >= 2.5
    assert prediction["predicted_roas"] <= 3.5
    assert prediction["confidence"] > 0.0
    assert prediction["historical_data_points"] == 10


@pytest.mark.asyncio
async def test_optimizer_scaling():
    """
    Test 4: Optimizer scaling recommendations.
    
    High ROAS ads should be scaled up, low ROAS ads scaled down.
    """
    session = AsyncMock()
    optimizer = ROASOptimizer(session)
    
    # Mock high-performing ad
    high_roas_metric = MagicMock(
        ad_id=uuid4(),
        actual_roas=5.0,
        predicted_roas=5.5,
        confidence_score=0.9,
        performance_tier="excellent",
        is_outlier=0,
        sample_size=1000,
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [high_roas_metric]
    session.execute = AsyncMock(return_value=mock_result)
    
    # Mock ad details
    optimizer._get_ad = AsyncMock(return_value=MagicMock(ad_name="Test Ad"))
    
    # Detect scale-up candidates
    scale_up = await optimizer.detect_ads_to_scale_up(uuid4())
    
    assert len(scale_up) == 1
    assert scale_up[0]["recommendation"] == "scale_up"
    assert scale_up[0]["current_roas"] == 5.0
    assert scale_up[0]["budget_increase_pct"] > 0


@pytest.mark.asyncio
async def test_endpoint_responses():
    """
    Test 5: API endpoint response formats.
    
    Validate that endpoint responses match expected structure.
    """
    from app.meta_ads_orchestrator.roas_router import (
        ROASSummaryResponse,
        ROASPredictionResponse,
        PixelOutcomeResponse,
    )
    
    # Test ROASSummaryResponse
    summary = ROASSummaryResponse(
        campaign_id=uuid4(),
        date_start=datetime.utcnow(),
        date_end=datetime.utcnow(),
        impressions=1000,
        clicks=50,
        conversions=5,
        spend=100.0,
        revenue=500.0,
        actual_roas=5.0,
        smoothed_roas=4.5,
        blended_ctr=5.0,
        blended_cpc=2.0,
        blended_cpm=100.0,
        conversion_rate=0.1,
        session_quality_score=75.0,
        user_retention_probability=0.8,
        lifetime_value_estimate=1000.0,
        confidence_interval_low=4.0,
        confidence_interval_high=6.0,
        is_outlier=False,
        sample_size=5,
    )
    
    assert summary.actual_roas == 5.0
    assert summary.conversions == 5
    
    # Test ROASPredictionResponse
    prediction = ROASPredictionResponse(
        ad_id=uuid4(),
        predicted_roas=4.5,
        confidence=0.8,
        historical_data_points=10,
        recent_trend="increasing",
        conversion_probability=0.1,
        credible_interval_low=0.05,
        credible_interval_high=0.15,
    )
    
    assert prediction.predicted_roas == 4.5
    assert prediction.confidence == 0.8


@pytest.mark.asyncio
async def test_outcome_models():
    """
    Test 6: Pixel outcome and conversion event models.
    
    Verify database model structure and relationships.
    """
    # Test MetaPixelOutcomeModel creation
    outcome = MetaPixelOutcomeModel(
        pixel_id="pixel_123",
        event_name="Purchase",
        conversion_type="purchase",
        value_usd=100.0,
        campaign_id=uuid4(),
        session_duration_seconds=300,
        utm_source="facebook",
        utm_campaign="test_campaign",
        attribution_model="last_click",
        attribution_weight=1.0,
        event_timestamp=datetime.utcnow(),
    )
    
    assert outcome.pixel_id == "pixel_123"
    assert outcome.value_usd == 100.0
    assert outcome.attribution_model == "last_click"
    
    # Test that model has all required fields
    required_fields = [
        "pixel_id", "event_name", "conversion_type", "campaign_id",
        "attribution_model", "attribution_weight", "event_timestamp"
    ]
    
    for field in required_fields:
        assert hasattr(outcome, field)


@pytest.mark.asyncio
async def test_outlier_detection():
    """
    Test 7: Outlier detection for suspicious ROAS values.
    
    Detect extremely high/low ROAS, low spend with high ROAS, etc.
    """
    session = AsyncMock()
    calculator = ROASCalculator(session)
    
    # Test extremely high ROAS
    is_outlier, reason = calculator._detect_outlier(
        roas=100.0,
        conversions=1,
        spend=1.0,
    )
    assert is_outlier is True
    assert "Extremely high ROAS" in reason
    
    # Test negative ROAS
    is_outlier, reason = calculator._detect_outlier(
        roas=-1.0,
        conversions=5,
        spend=100.0,
    )
    assert is_outlier is True
    assert "Negative ROAS" in reason
    
    # Test low spend with high ROAS
    is_outlier, reason = calculator._detect_outlier(
        roas=15.0,
        conversions=1,
        spend=5.0,
    )
    assert is_outlier is True
    assert "Low spend" in reason
    
    # Test normal ROAS (should not be outlier)
    is_outlier, reason = calculator._detect_outlier(
        roas=3.5,
        conversions=50,
        spend=500.0,
    )
    assert is_outlier is False
    assert reason is None


@pytest.mark.asyncio
async def test_value_attribution():
    """
    Test 8: Multi-touch attribution models.
    
    Test last_click, first_click, linear, and time_decay attribution.
    """
    # Create mock outcomes
    base_time = datetime.utcnow()
    outcomes = [
        MagicMock(
            event_timestamp=base_time - timedelta(days=i),
            attribution_weight=0.0,
            attribution_model="",
        )
        for i in range(5)
    ]
    
    # Test last_click attribution
    attributed = AttributionEngine.apply_attribution(outcomes, model="last_click")
    assert all(o.attribution_weight == 1.0 for o in attributed)
    assert all(o.attribution_model == "last_click" for o in attributed)
    
    # Test linear attribution
    attributed = AttributionEngine.apply_attribution(outcomes, model="linear")
    expected_weight = 1.0 / len(outcomes)
    assert all(abs(o.attribution_weight - expected_weight) < 0.01 for o in attributed)
    assert all(o.attribution_model == "linear" for o in attributed)
    
    # Test time_decay attribution
    attributed = AttributionEngine.apply_attribution(outcomes, model="time_decay")
    weights = [o.attribution_weight for o in attributed]
    
    # Weights should sum to 1.0
    assert abs(sum(weights) - 1.0) < 0.01
    
    # More recent events should have higher weight
    # (outcomes are sorted oldest to newest in time_decay logic)
    assert all(o.attribution_model == "time_decay" for o in attributed)


@pytest.mark.asyncio
async def test_conversion_probability():
    """
    Test 9: Bayesian conversion probability calculation.
    
    Uses Beta-Binomial conjugate prior.
    """
    session = AsyncMock()
    prediction_engine = PredictionEngine(session)
    
    # Test with 100 clicks, 10 conversions
    result = prediction_engine.calculate_conversion_probability(
        clicks=100,
        conversions=10,
    )
    
    # Expected probability ≈ 10/100 = 0.1
    assert result["probability"] > 0.05
    assert result["probability"] < 0.15
    assert result["credible_interval_low"] < result["probability"]
    assert result["credible_interval_high"] > result["probability"]
    
    # Test with high conversion rate
    result_high = prediction_engine.calculate_conversion_probability(
        clicks=100,
        conversions=50,
    )
    
    # Should have higher probability
    assert result_high["probability"] > result["probability"]


@pytest.mark.asyncio
async def test_expected_value_calculation():
    """
    Test 10: Expected value per click calculation.
    
    EV = (conversion_prob * AOV) - CPC
    """
    session = AsyncMock()
    prediction_engine = PredictionEngine(session)
    
    # Test profitable scenario
    result = prediction_engine.calculate_expected_value(
        conversion_probability=0.1,  # 10% conversion rate
        average_order_value=100.0,   # $100 AOV
        cost_per_click=5.0,          # $5 CPC
    )
    
    # Expected revenue = 0.1 * 100 = $10
    # Expected value = $10 - $5 = $5 (profitable)
    assert result["expected_revenue"] == 10.0
    assert result["expected_value"] == 5.0
    assert result["is_profitable"] is True
    
    # Breakeven conversion rate = $5 / $100 = 5%
    assert abs(result["breakeven_conversion_rate"] - 0.05) < 0.01
    
    # Test unprofitable scenario
    result_loss = prediction_engine.calculate_expected_value(
        conversion_probability=0.02,  # 2% conversion rate (below breakeven)
        average_order_value=100.0,
        cost_per_click=5.0,
    )
    
    # Expected revenue = 0.02 * 100 = $2
    # Expected value = $2 - $5 = -$3 (unprofitable)
    assert result_loss["expected_value"] < 0
    assert result_loss["is_profitable"] is False


@pytest.mark.asyncio
async def test_budget_reallocation():
    """
    Test 11: Budget reallocation across ads.
    
    Higher ROAS ads should receive proportionally more budget.
    """
    session = AsyncMock()
    optimizer = ROASOptimizer(session)
    
    # Mock 3 ads with different ROAS
    mock_metrics = [
        MagicMock(
            ad_id=uuid4(),
            actual_roas=5.0,
            confidence_score=0.9,
            is_outlier=0,
        ),
        MagicMock(
            ad_id=uuid4(),
            actual_roas=3.0,
            confidence_score=0.8,
            is_outlier=0,
        ),
        MagicMock(
            ad_id=uuid4(),
            actual_roas=2.0,
            confidence_score=0.7,
            is_outlier=0,
        ),
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_metrics
    session.execute = AsyncMock(return_value=mock_result)
    
    # Compute budget allocation for $1000 total
    result = await optimizer.compute_budget_reallocations(
        campaign_id=uuid4(),
        total_budget=1000.0,
    )
    
    # Verify allocations
    assert len(result["allocations"]) == 3
    assert result["total_allocated"] <= 1000.0
    
    # First ad (highest ROAS) should get most budget
    allocations = sorted(result["allocations"], key=lambda x: x["allocated_budget"], reverse=True)
    assert allocations[0]["current_roas"] == 5.0  # Highest ROAS
    assert allocations[0]["allocated_budget"] > allocations[1]["allocated_budget"]


@pytest.mark.asyncio
async def test_confidence_intervals():
    """
    Test 12: Statistical confidence intervals for ROAS.
    
    Use bootstrap resampling to calculate CI.
    """
    session = AsyncMock()
    calculator = ROASCalculator(session)
    
    # Create mock outcomes with consistent values
    outcomes = [MagicMock(value_usd=100.0) for _ in range(50)]
    
    # Calculate CI
    ci_low, ci_high = calculator._calculate_confidence_interval(
        outcomes=outcomes,
        spend=1000.0,
        conversions=50,
        confidence=0.95,
    )
    
    # Expected ROAS = 5000 / 1000 = 5.0
    # CI should be around 5.0
    assert ci_low > 0
    assert ci_high >= ci_low  # Edge case: when no variance, ci_high may equal ci_low
    assert ci_low <= 5.0 <= ci_high  # ROAS should be within CI


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
