"""
Tests para Meta Creative Intelligence System
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.meta_creative_intelligence.visual_analyzer import VisualAnalyzer
from app.meta_creative_intelligence.variant_generator import VariantGenerator
from app.meta_creative_intelligence.winner_engine import WinnerEngine
from app.meta_creative_intelligence.thumbnail_generator import ThumbnailGenerator
from app.meta_creative_intelligence.lifecycle_manager import LifecycleManager
from app.meta_creative_intelligence.orchestrator import MetaCreativeIntelligenceOrchestrator
from app.meta_creative_intelligence.schemas import (
    VariantConfig,
    WinnerSelectionRequest,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_video_asset_id():
    """Sample video asset UUID"""
    return uuid4()


@pytest.fixture
def sample_campaign_id():
    """Sample campaign UUID"""
    return uuid4()


# ============================================================================
# 1. VISUAL ANALYZER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_visual_analyzer_stub_mode(sample_video_asset_id):
    """Test visual analyzer in STUB mode"""
    analyzer = VisualAnalyzer(mode="stub")
    
    result = await analyzer.analyze(
        video_asset_id=sample_video_asset_id,
        detect_objects=True,
        detect_faces=True,
        detect_text=True,
        extract_fragments=True,
        max_fragments=5,
    )
    
    # Assertions
    assert result.video_asset_id == sample_video_asset_id
    assert result.mode == "stub"
    assert len(result.objects) >= 0
    assert len(result.faces) >= 0
    assert len(result.texts) >= 0
    assert 0 <= result.scoring.overall_score <= 100
    assert 0 <= len(result.fragments) <= 5
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_visual_scoring_calculation(sample_video_asset_id):
    """Test visual scoring calculation"""
    analyzer = VisualAnalyzer(mode="stub")
    
    result = await analyzer.analyze(
        video_asset_id=sample_video_asset_id,
        detect_objects=True,
        detect_faces=True,
        detect_text=False,
        extract_fragments=False,
    )
    
    scoring = result.scoring
    
    # All scores should be 0-100
    assert 0 <= scoring.overall_score <= 100
    assert 0 <= scoring.face_score <= 100
    assert 0 <= scoring.action_score <= 100
    assert 0 <= scoring.text_score <= 100
    assert 0 <= scoring.color_score <= 100
    assert 0 <= scoring.composition_score <= 100
    assert 0 <= scoring.engagement_potential <= 100


# ============================================================================
# 2. VARIANT GENERATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_variant_generator_stub_mode(sample_video_asset_id):
    """Test variant generator in STUB mode"""
    generator = VariantGenerator(mode="stub")
    
    config = VariantConfig(
        reorder_fragments=True,
        add_subtitles=True,
        add_overlays=True,
        vary_music=False,
        vary_duration=True,
        min_variants=5,
        max_variants=10,
    )
    
    result = await generator.generate_variants(
        video_asset_id=sample_video_asset_id,
        config=config,
        analysis=None,
    )
    
    # Assertions
    assert result.video_asset_id == sample_video_asset_id
    assert 5 <= len(result.variants) <= 10
    assert result.total_variants == len(result.variants)
    assert result.processing_time_ms > 0
    
    # Check variants have expected structure
    for variant in result.variants:
        assert variant.variant_number > 0
        assert variant.duration_seconds > 0
        assert 0 <= variant.estimated_score <= 100
        assert isinstance(variant.changes, dict)


@pytest.mark.asyncio
async def test_variant_transformations(sample_video_asset_id):
    """Test individual variant transformations"""
    generator = VariantGenerator(mode="stub")
    
    # Test reorder
    reorder_result = await generator._apply_reorder(None)
    assert "strategy" in reorder_result
    assert "fragments_reordered" in reorder_result
    
    # Test subtitles
    subtitles_result = await generator._apply_subtitles()
    assert "style" in subtitles_result
    assert "language" in subtitles_result
    
    # Test overlays
    overlays_result = await generator._apply_overlays()
    assert "overlays" in overlays_result
    assert "total_overlays" in overlays_result


# ============================================================================
# 3. WINNER ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_winner_selection_stub_mode(mock_db, sample_campaign_id):
    """Test winner selection in STUB mode"""
    engine = WinnerEngine(mode="stub")
    
    candidate_ids = [uuid4(), uuid4(), uuid4()]
    
    result = await engine.select_winner(
        db=mock_db,
        campaign_id=sample_campaign_id,
        candidate_asset_ids=candidate_ids,
        criteria_weights={"roas": 0.4, "ctr": 0.25, "cvr": 0.20, "view_depth": 0.15},
        min_impressions=1000,
    )
    
    # Assertions
    assert result.campaign_id == sample_campaign_id
    assert result.winner_asset_id in candidate_ids
    assert 0 <= result.winner_score <= 100
    assert len(result.all_scores) >= 1
    assert result.reasoning is not None


@pytest.mark.asyncio
async def test_performance_metrics_generation(mock_db):
    """Test performance metrics generation"""
    engine = WinnerEngine(mode="stub")
    
    asset_id = uuid4()
    metrics = await engine._get_performance_metrics_stub(asset_id)
    
    # Assertions
    assert metrics.roas is not None
    assert metrics.ctr is not None
    assert metrics.cvr is not None
    assert metrics.view_depth is not None
    assert metrics.impressions > 0
    assert metrics.clicks >= 0
    assert metrics.conversions >= 0
    assert metrics.spend >= 0


# ============================================================================
# 4. THUMBNAIL GENERATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_thumbnail_generation_stub_mode(sample_video_asset_id):
    """Test thumbnail generation in STUB mode"""
    generator = ThumbnailGenerator(mode="stub")
    
    result = await generator.generate_thumbnail(
        video_asset_id=sample_video_asset_id,
        analysis=None,
        max_candidates=5,
        prefer_faces=True,
        prefer_action=True,
        avoid_text=False,
    )
    
    # Assertions
    assert result.video_asset_id == sample_video_asset_id
    assert result.selected_frame >= 0
    assert result.selected_timestamp >= 0
    assert len(result.candidates) <= 5
    assert result.reasoning is not None
    
    # Selected should be best candidate
    selected_candidate = next(c for c in result.candidates if c.frame_number == result.selected_frame)
    assert selected_candidate.score == max(c.score for c in result.candidates)


@pytest.mark.asyncio
async def test_thumbnail_candidate_scoring(sample_video_asset_id):
    """Test thumbnail candidate scoring"""
    generator = ThumbnailGenerator(mode="stub")
    
    candidates = await generator._generate_stub_candidates(
        video_asset_id=sample_video_asset_id,
        max_candidates=5,
        prefer_faces=True,
        prefer_action=False,
        avoid_text=True,
    )
    
    # Candidates with faces should have higher scores on average
    face_scores = [c.score for c in candidates if c.has_face]
    non_face_scores = [c.score for c in candidates if not c.has_face]
    
    if face_scores and non_face_scores:
        assert sum(face_scores) / len(face_scores) > sum(non_face_scores) / len(non_face_scores)


# ============================================================================
# 5. LIFECYCLE MANAGER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_fatigue_detection_stub_mode(mock_db):
    """Test fatigue detection in STUB mode"""
    manager = LifecycleManager(mode="stub")
    
    creative_id = uuid4()
    
    result = await manager.detect_fatigue(db=mock_db, creative_id=creative_id)
    
    # Assertions
    assert result.creative_id == creative_id
    assert isinstance(result.is_fatigued, bool)
    assert 0 <= result.fatigue_score <= 100
    assert result.recommendation is not None
    assert result.days_active >= 0
    assert result.impressions_total >= 0


@pytest.mark.asyncio
async def test_fatigue_score_calculation(mock_db):
    """Test fatigue score calculation"""
    manager = LifecycleManager(mode="stub")
    
    creative_id = uuid4()
    
    # Generate metrics trend
    metrics_trend = await manager._get_metrics_trend_stub(creative_id)
    
    # Calculate fatigue score
    fatigue_score = await manager._calculate_fatigue_score(metrics_trend)
    
    # Assertions
    assert 0 <= fatigue_score <= 100
    
    # High drops should result in moderate fatigue (>35)
    if metrics_trend.get("ctr_drop_pct", 0) > 30:
        assert fatigue_score > 35


@pytest.mark.asyncio
async def test_creative_renewal(mock_db):
    """Test creative renewal"""
    manager = LifecycleManager(mode="stub")
    
    creative_id = uuid4()
    
    result = await manager.renew_creative(
        db=mock_db,
        creative_id=creative_id,
        strategy="generate_variant",
        auto_apply=False,
    )
    
    # Assertions
    assert result.creative_id == creative_id
    assert result.strategy == "generate_variant"
    assert result.success is True
    assert len(result.actions_taken) > 0


# ============================================================================
# 6. ORCHESTRATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_full_run(mock_db):
    """Test orchestrator full run"""
    orchestrator = MetaCreativeIntelligenceOrchestrator(mode="stub")
    
    video_ids = [uuid4(), uuid4()]
    
    result = await orchestrator.run(
        db=mock_db,
        video_asset_ids=video_ids,
        enable_analysis=True,
        enable_variants=True,
        enable_thumbnails=True,
        enable_lifecycle_check=True,
    )
    
    # Assertions
    assert result.video_assets_processed == len(video_ids)
    assert result.duration_ms > 0
    assert isinstance(result.summary, dict)


@pytest.mark.asyncio
async def test_orchestrator_selective_execution(mock_db):
    """Test orchestrator with selective execution"""
    orchestrator = MetaCreativeIntelligenceOrchestrator(mode="stub")
    
    video_ids = [uuid4()]
    
    # Only analysis and thumbnails
    result = await orchestrator.run(
        db=mock_db,
        video_asset_ids=video_ids,
        enable_analysis=True,
        enable_variants=False,
        enable_thumbnails=True,
        enable_lifecycle_check=False,
    )
    
    # Assertions
    assert result.analyses_completed >= 0
    assert result.variants_generated == 0  # Disabled
    assert result.thumbnails_created >= 0
    assert result.fatigues_detected == 0  # Disabled
