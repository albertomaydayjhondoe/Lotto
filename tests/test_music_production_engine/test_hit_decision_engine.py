"""Tests for Hit Decision Engine module."""
import pytest
from backend.app.music_production_engine.hit_decision_engine import (
    TrendMinerStub, ComparativeModelStub, HitScoreCalculator, RecommendationEngine
)

@pytest.mark.asyncio
async def test_trend_mining():
    miner = TrendMinerStub()
    trends = await miner.mine_trends("hip-hop")
    assert len(trends) > 0
    assert trends[0].popularity_score > 0

@pytest.mark.asyncio
async def test_comparative_model():
    model = ComparativeModelStub()
    comparisons = await model.compare_to_hits({"bpm": 140})
    assert len(comparisons) > 0
    assert 0 <= comparisons[0].similarity_score <= 1

def test_hit_score_calculator():
    calc = HitScoreCalculator()
    score = calc.calculate({"audio_analysis": {"overall_score": 80}})
    assert 0 <= score.overall_score <= 100
    assert score.confidence > 0

def test_recommendation_engine():
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations({"overall_score": 65}, {})
    assert len(recommendations) > 0
