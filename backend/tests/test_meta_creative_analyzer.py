"""Tests for Meta Creative Analyzer (PASO 10.15)"""
import pytest, uuid
from unittest.mock import AsyncMock
from app.meta_creative_analyzer.core import CreativeIntelligenceCore
from app.meta_creative_analyzer.fatigue import FatigueDetector
from app.meta_creative_analyzer.variant_generator import CreativeVariantGenerator
from app.meta_creative_analyzer.recombination import CreativeRecombinationEngine
from app.meta_creative_analyzer.schemas import CreativePerformanceMetrics

@pytest.fixture
def sample_metrics():
    return CreativePerformanceMetrics(
        ctr=2.5, cvr=3.0, cpc=1.5, cpm=20.0, roas=3.5, video_3s=70, video_25pct=50,
        video_50pct=35, video_100pct=20, engagement_rate=5.0, impressions=50000,
        clicks=1250, conversions=150, spend=500
    )

@pytest.mark.asyncio
async def test_creative_scoring(sample_metrics):
    """Test creative scoring calculation."""
    core = CreativeIntelligenceCore(mode="stub")
    score = await core.calculate_creative_score(sample_metrics, fatigue_penalty=0.0)
    
    assert 0 <= score.overall_score <= 100
    assert 0 <= score.performance_score <= 40
    assert 0 <= score.engagement_score <= 30
    assert score.fatigue_penalty == 0.0

@pytest.mark.asyncio
async def test_fatigue_detection(sample_metrics):
    """Test fatigue detection."""
    detector = FatigueDetector(mode="stub")
    result = await detector.detect_fatigue(uuid.uuid4(), sample_metrics, days_active=30, impressions_total=100000)
    
    assert result.creative_id is not None
    assert isinstance(result.is_fatigued, bool)
    assert 0 <= result.fatigue_score <= 100
    assert result.fatigue_level in ["healthy", "mild", "moderate", "severe", "critical"]

@pytest.mark.asyncio
async def test_variant_generation():
    """Test variant generation."""
    generator = CreativeVariantGenerator(mode="stub")
    variants = await generator.generate_variants(uuid.uuid4(), num_variants=5, strategy="balanced")
    
    assert len(variants) == 5
    assert all(v.variant_number >= 1 for v in variants)
    assert all(len(v.changes) > 0 for v in variants)

@pytest.mark.asyncio
async def test_recombination():
    """Test creative recombination."""
    engine = CreativeRecombinationEngine(mode="stub")
    result = await engine.recombine([uuid.uuid4(), uuid.uuid4()], num_variants=5, strategy="balanced")
    
    assert len(result.generated_variants) == 5
    assert len(result.best_fragments) > 0
    assert result.total_variants == 5

@pytest.mark.asyncio
async def test_scoring_with_fatigue_penalty(sample_metrics):
    """Test scoring with fatigue penalty applied."""
    core = CreativeIntelligenceCore(mode="stub")
    score_no_penalty = await core.calculate_creative_score(sample_metrics, fatigue_penalty=0.0)
    score_with_penalty = await core.calculate_creative_score(sample_metrics, fatigue_penalty=20.0)
    
    assert score_with_penalty.overall_score < score_no_penalty.overall_score
    assert score_with_penalty.fatigue_penalty == 20.0
