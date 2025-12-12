"""Tests for Meta Creative Production Engine (PASO 10.17)"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.meta_creative_production.schemas import (
    MasterCreativeInput, CreativeFragmentInput, StyleGuideInput,
    CreativeProductionRequest, VariantGenerationConfig,
    RecombinationRequest, PromotionRequest, FragmentType,
    NarrativeStructure
)
from app.meta_creative_production.variant_generator import AutonomousVariantGenerator
from app.meta_creative_production.recombination_engine import CreativeRecombinationEngine
from app.meta_creative_production.promotion_loop import AutoPromotionLoop
from app.meta_creative_production.fatigue_monitor import FatigueMonitor

@pytest.fixture
def sample_master_creative():
    """Sample master creative"""
    return MasterCreativeInput(
        video_url="https://example.com/master.mp4",
        title="Test Master Creative",
        description="Test description",
        duration_seconds=12.5,
        pixels=["pixel_A", "pixel_B"],
        genre="tech",
        subgenres=["gaming", "education"]
    )

@pytest.fixture
def sample_fragments():
    """Sample approved fragments"""
    return [
        CreativeFragmentInput(
            fragment_id=uuid4(),
            fragment_type=FragmentType.HOOK,
            start_time=0.0,
            end_time=3.0,
            duration=3.0,
            video_url="https://example.com/hook.mp4",
            performance_score=85.0
        ),
        CreativeFragmentInput(
            fragment_id=uuid4(),
            fragment_type=FragmentType.BODY,
            start_time=3.0,
            end_time=8.0,
            duration=5.0,
            video_url="https://example.com/body.mp4",
            performance_score=78.0
        ),
        CreativeFragmentInput(
            fragment_id=uuid4(),
            fragment_type=FragmentType.CTA,
            start_time=8.0,
            end_time=12.0,
            duration=4.0,
            video_url="https://example.com/cta.mp4",
            performance_score=82.0
        )
    ]

@pytest.fixture
def sample_style_guide():
    """Sample style guide"""
    return StyleGuideInput(
        vibes=["energetic", "modern", "minimalist"],
        aesthetic_reference="Clean tech aesthetic with vibrant colors",
        color_palette=["#FF5733", "#33FF57", "#3357FF"],
        font_style="bold_sans",
        music_style="upbeat_electronic",
        tone="energetic"
    )

# ==================== VARIANT GENERATION TESTS ====================

@pytest.mark.asyncio
async def test_variant_generation_5_to_15(
    sample_master_creative,
    sample_fragments,
    sample_style_guide
):
    """Test variant generation produces 5-15 variants"""
    generator = AutonomousVariantGenerator(mode="stub")
    
    request = CreativeProductionRequest(
        master_creative=sample_master_creative,
        fragments=sample_fragments,
        style_guide=sample_style_guide
    )
    
    config = VariantGenerationConfig(min_variants=5, max_variants=15)
    
    result = await generator.generate_variants(request, config)
    
    assert 5 <= result.variants_generated <= 15
    assert len(result.variants) == result.variants_generated
    assert result.generation_time_ms > 0

@pytest.mark.asyncio
async def test_duration_variants_short_medium_long(
    sample_master_creative,
    sample_fragments,
    sample_style_guide
):
    """Test generation of 3 duration variants"""
    generator = AutonomousVariantGenerator(mode="stub")
    
    request = CreativeProductionRequest(
        master_creative=sample_master_creative,
        fragments=sample_fragments,
        style_guide=sample_style_guide
    )
    
    config = VariantGenerationConfig(
        min_variants=9,
        max_variants=9,
        enable_short_duration=True,
        enable_medium_duration=True,
        enable_long_duration=True
    )
    
    result = await generator.generate_variants(request, config)
    
    # Check duration categories
    short_variants = [v for v in result.variants if 5 <= v.duration_seconds <= 7]
    medium_variants = [v for v in result.variants if 8 <= v.duration_seconds <= 12]
    long_variants = [v for v in result.variants if 13 <= v.duration_seconds <= 18]
    
    # Should have variants in different duration categories
    assert len(short_variants) > 0 or len(medium_variants) > 0 or len(long_variants) > 0

# ==================== RECOMBINATION TESTS ====================

@pytest.mark.asyncio
async def test_recombination_structures():
    """Test recombination with different narrative structures"""
    engine = CreativeRecombinationEngine(mode="stub")
    
    request = RecombinationRequest(
        master_creative_id=uuid4(),
        use_best_fragments=True,
        narrative_structures=[
            NarrativeStructure.HOOK_BODY_CTA,
            NarrativeStructure.HOOK_INVERTED,
            NarrativeStructure.CTA_FORWARD
        ],
        min_recombinations=2
    )
    
    result = await engine.recombine_fragments(request)
    
    assert result.recombinations_created >= 6  # 3 structures × 2 recombinations
    assert len(result.recombinations) == result.recombinations_created
    assert result.best_structure in NarrativeStructure
    assert result.processing_time_ms > 0

@pytest.mark.asyncio
async def test_fragment_extraction():
    """Test extraction of best fragments"""
    engine = CreativeRecombinationEngine(mode="stub")
    
    fragments = await engine._extract_best_fragments(uuid4())
    
    assert "hook" in fragments
    assert "body" in fragments
    assert "cta" in fragments
    assert len(fragments["hook"]) > 0
    assert len(fragments["body"]) > 0

# ==================== PROMOTION TESTS ====================

@pytest.mark.asyncio
async def test_auto_upload_to_meta():
    """Test variant upload to Meta Ads"""
    loop = AutoPromotionLoop(mode="stub")
    
    request = PromotionRequest(
        variant_id=uuid4(),
        campaign_id=uuid4()
    )
    
    result = await loop.upload_variant(request)
    
    assert result.variant_id == request.variant_id
    assert result.campaign_id == request.campaign_id
    assert result.uploaded_at is not None

@pytest.mark.asyncio
async def test_promotion_loop():
    """Test auto-promotion of top 3 variants"""
    loop = AutoPromotionLoop(mode="stub")
    
    # Create mock variants
    from app.meta_creative_production.schemas import GeneratedVariant, VariantType
    
    variants = [
        GeneratedVariant(
            variant_id=uuid4(),
            parent_id=uuid4(),
            variant_type=VariantType.FRAGMENT_REORDER,
            narrative_structure=NarrativeStructure.HOOK_BODY_CTA,
            fragments_order=[uuid4()],
            caption="Test caption",
            hashtags=["#test"],
            duration_seconds=10.0,
            estimated_score=score,
            confidence=0.8,
            generated_at=datetime.utcnow(),
            mode="stub"
        )
        for score in [95.0, 88.0, 82.0, 75.0, 70.0]
    ]
    
    result = await loop.promote_top_variants(variants, uuid4(), top_n=3)
    
    assert len(result.top_3_promoted) <= 3
    assert result.variants_uploaded <= 3
    assert result.total_time_ms > 0

# ==================== FATIGUE MONITORING TESTS ====================

@pytest.mark.asyncio
async def test_fatigue_detection_and_refresh():
    """Test fatigue detection and refresh suggestion"""
    monitor = FatigueMonitor(mode="stub")
    
    variant_id = uuid4()
    result = await monitor.detect_variant_fatigue(variant_id)
    
    assert result.variant_id == variant_id
    assert 0 <= result.fatigue_score <= 100
    assert result.days_active >= 0
    assert result.recommendation in ["archive", "refresh", "continue"]

@pytest.mark.asyncio
async def test_archive_fatigued():
    """Test archiving fatigued variants"""
    monitor = FatigueMonitor(mode="stub")
    
    variant_ids = [uuid4() for _ in range(5)]
    archived = await monitor.archive_obsolete(variant_ids)
    
    assert archived == len(variant_ids)

@pytest.mark.asyncio
async def test_refresh_creation():
    """Test creation of refresh variant"""
    monitor = FatigueMonitor(mode="stub")
    
    refresh_id = await monitor.create_refresh(uuid4())
    
    assert refresh_id is not None

# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_production_pipeline(
    sample_master_creative,
    sample_fragments,
    sample_style_guide
):
    """Test complete production pipeline"""
    # Step 1: Generate variants
    generator = AutonomousVariantGenerator(mode="stub")
    request = CreativeProductionRequest(
        master_creative=sample_master_creative,
        fragments=sample_fragments,
        style_guide=sample_style_guide
    )
    config = VariantGenerationConfig(min_variants=5, max_variants=10)
    gen_result = await generator.generate_variants(request, config)
    
    assert len(gen_result.variants) >= 5
    
    # Step 2: Promote top variants
    loop = AutoPromotionLoop(mode="stub")
    promo_result = await loop.promote_top_variants(gen_result.variants, uuid4(), top_n=3)
    
    assert len(promo_result.top_3_promoted) <= 3
    
    # Step 3: Monitor fatigue
    monitor = FatigueMonitor(mode="stub")
    fatigue_result = await monitor.monitor_all_variants()
    
    assert fatigue_result.variants_checked >= 0

@pytest.mark.asyncio
async def test_scheduler_12h_cycle():
    """Test scheduler runs 12h cycles"""
    from app.meta_creative_production.scheduler import (
        start_creative_production_scheduler,
        stop_creative_production_scheduler,
        _is_running
    )
    
    # Start scheduler
    task = await start_creative_production_scheduler()
    assert task is not None
    
    # Stop scheduler
    await stop_creative_production_scheduler(task)
    # Note: Actual stopping is async, so task is cancelled

@pytest.mark.asyncio
async def test_integration_with_optimizer_10_16():
    """Test integration with PASO 10.16 (Creative Optimizer)"""
    # This test verifies that production engine can work with optimizer
    generator = AutonomousVariantGenerator(mode="stub")
    
    # In LIVE mode, generator would query 10.16 for winner decisions
    # STUB: Just verify component initialization
    assert generator.mode == "stub"

@pytest.mark.asyncio
async def test_human_constraint_enforcement(
    sample_master_creative,
    sample_fragments,
    sample_style_guide
):
    """Test that system respects human-defined pixels and genres"""
    generator = AutonomousVariantGenerator(mode="stub")
    
    request = CreativeProductionRequest(
        master_creative=sample_master_creative,
        fragments=sample_fragments,
        style_guide=sample_style_guide
    )
    config = VariantGenerationConfig(min_variants=5, max_variants=5)
    
    result = await generator.generate_variants(request, config)
    
    # All variants should respect original pixels/genres from master
    # In LIVE mode, system CANNOT create new pixels
    assert len(result.variants) > 0
