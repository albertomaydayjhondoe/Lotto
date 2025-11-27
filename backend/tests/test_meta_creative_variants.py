"""
Tests para Meta Creative Variants Engine (PASO 10.10)
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_creative_variants.engine import CreativeVariantsEngine
from app.meta_creative_variants.extractor import CreativeMaterialExtractor
from app.meta_creative_variants.generator import CreativeVariantsGenerator
from app.meta_creative_variants.uploader import CreativeUploader
from app.meta_creative_variants.schemas import (
    GenerateVariantsRequest,
    VideoVariant,
    TextVariant,
    ThumbnailVariant,
    CreativeVariant,
    CropRatio,
    CTAType,
    VariantStatus,
)


# ==================== Fixtures ====================


@pytest.fixture
def db_session():
    """Mock database session"""
    return Mock(spec=AsyncSession)


@pytest.fixture
def extractor(db_session):
    """CreativeMaterialExtractor instance"""
    return CreativeMaterialExtractor(db_session)


@pytest.fixture
def generator(extractor):
    """CreativeVariantsGenerator instance"""
    return CreativeVariantsGenerator(extractor)


@pytest.fixture
def uploader():
    """CreativeUploader instance"""
    return CreativeUploader()


@pytest.fixture
def engine(db_session):
    """CreativeVariantsEngine instance"""
    return CreativeVariantsEngine(db_session)


@pytest.fixture
def sample_request():
    """Sample GenerateVariantsRequest"""
    return GenerateVariantsRequest(
        clip_id="test_clip_001",
        campaign_id="23847656789012340",
        adset_id="23847656789012345",
        num_variants=10,
        video_variants_count=5,
        text_variants_count=5,
        thumbnail_variants_count=4,
        crop_ratios=[CropRatio.SQUARE, CropRatio.VERTICAL],
        cta_types=[CTAType.LEARN_MORE, CTAType.SHOP_NOW],
        auto_upload=False,
        dry_run=False,
    )


# ==================== Extractor Tests ====================


@pytest.mark.asyncio
async def test_extract_from_clip(extractor):
    """Test: Extract material from clip (stub mode)"""
    clip_id = "test_clip_001"
    
    material = await extractor.extract_from_clip(clip_id)
    
    assert material["clip_id"] == clip_id
    assert "clip_metadata" in material
    assert "video_asset" in material
    assert "text_content" in material
    assert "keywords" in material
    assert "hashtags" in material
    assert "scenes" in material
    
    # Verify structure
    assert material["video_asset"]["duration"] > 0
    assert len(material["keywords"]) > 0
    assert len(material["hashtags"]) > 0


# ==================== Generator Tests ====================


@pytest.mark.asyncio
async def test_generate_video_variants(generator):
    """Test: Generate video variants"""
    clip_id = "test_clip_001"
    count = 5
    
    variants = await generator.generate_video_variants(
        clip_id=clip_id,
        count=count,
        crop_ratios=[CropRatio.SQUARE, CropRatio.VERTICAL]
    )
    
    assert len(variants) == count
    assert all(isinstance(v, VideoVariant) for v in variants)
    assert all(v.clip_id == clip_id for v in variants)
    assert all(v.duration > 0 for v in variants)
    assert all(v.crop_ratio in [CropRatio.SQUARE, CropRatio.VERTICAL, CropRatio.PORTRAIT] for v in variants)


@pytest.mark.asyncio
async def test_generate_text_variants(generator):
    """Test: Generate text variants"""
    clip_id = "test_clip_001"
    count = 5
    
    variants = await generator.generate_text_variants(
        clip_id=clip_id,
        count=count,
        cta_types=[CTAType.LEARN_MORE, CTAType.SHOP_NOW],
        language="es"
    )
    
    assert len(variants) == count
    assert all(isinstance(v, TextVariant) for v in variants)
    assert all(len(v.headline) <= 40 for v in variants)
    assert all(len(v.primary_text) <= 125 for v in variants)
    assert all(v.cta_type in [CTAType.LEARN_MORE, CTAType.SHOP_NOW, CTAType.SIGN_UP] for v in variants)
    assert all(v.language == "es" for v in variants)


@pytest.mark.asyncio
async def test_generate_thumbnail_variants(generator):
    """Test: Generate thumbnail variants"""
    clip_id = "test_clip_001"
    count = 4
    
    variants = await generator.generate_thumbnail_variants(
        clip_id=clip_id,
        count=count,
        crop_ratios=[CropRatio.SQUARE, CropRatio.VERTICAL]
    )
    
    assert len(variants) == count
    assert all(isinstance(v, ThumbnailVariant) for v in variants)
    assert all(v.source_type in ["freeze_frame", "extract_frame", "overlay"] for v in variants)
    assert all(v.timestamp is not None for v in variants)


@pytest.mark.asyncio
async def test_generate_creative_combinations(generator):
    """Test: Generate creative combinations (permutations)"""
    clip_id = "test_clip_001"
    
    # Generate components
    video_variants = await generator.generate_video_variants(clip_id, 3)
    text_variants = await generator.generate_text_variants(clip_id, 3)
    thumbnail_variants = await generator.generate_thumbnail_variants(clip_id, 3)
    
    # Generate combinations
    creative_variants = await generator.generate_creative_combinations(
        video_variants=video_variants,
        text_variants=text_variants,
        thumbnail_variants=thumbnail_variants,
        target_count=10,
        campaign_id="test_campaign",
        adset_id="test_adset",
    )
    
    assert len(creative_variants) <= 10
    assert all(isinstance(v, CreativeVariant) for v in creative_variants)
    assert all(v.campaign_id == "test_campaign" for v in creative_variants)
    assert all(v.status == VariantStatus.GENERATED for v in creative_variants)
    
    # Verify each variant has all components
    for variant in creative_variants:
        assert isinstance(variant.video_variant, VideoVariant)
        assert isinstance(variant.text_variant, TextVariant)
        assert isinstance(variant.thumbnail_variant, ThumbnailVariant)


# ==================== Uploader Tests ====================


@pytest.mark.asyncio
async def test_upload_creative_stub(uploader):
    """Test: Upload creative in stub mode"""
    # Create sample variant
    video_variant = VideoVariant(
        variant_id="video_001",
        clip_id="clip_001",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    
    text_variant = TextVariant(
        variant_id="text_001",
        headline="Test Headline",
        primary_text="Test primary text for ad",
    )
    
    thumbnail_variant = ThumbnailVariant(
        variant_id="thumb_001",
        source_type="freeze_frame",
        timestamp=5.0,
    )
    
    creative_variant = CreativeVariant(
        variant_id="creative_001",
        video_variant=video_variant,
        text_variant=text_variant,
        thumbnail_variant=thumbnail_variant,
    )
    
    # Upload in stub mode
    response = await uploader.upload_creative(
        variant=creative_variant,
        ad_account_id="act_test",
        campaign_id="campaign_test",
        adset_id="adset_test",
    )
    
    assert response.success is True
    assert response.variant_id == "creative_001"
    assert response.meta_creative_id is not None
    assert response.meta_ad_id is not None
    assert "stub" in response.meta_creative_id


# ==================== Engine Tests ====================


@pytest.mark.asyncio
async def test_generate_variants_engine(engine, sample_request):
    """Test: Full generation workflow via engine"""
    response = await engine.generate_variants(sample_request)
    
    assert response.success is True
    assert response.clip_id == sample_request.clip_id
    assert response.total_variants == sample_request.num_variants
    assert len(response.variants) == sample_request.num_variants
    assert response.video_variants_generated == sample_request.video_variants_count
    assert response.text_variants_generated == sample_request.text_variants_count
    assert response.thumbnail_variants_generated == sample_request.thumbnail_variants_count
    assert response.generation_time_seconds > 0


@pytest.mark.asyncio
async def test_generate_variants_dry_run(engine, sample_request):
    """Test: Dry run mode (no persistence)"""
    sample_request.dry_run = True
    
    response = await engine.generate_variants(sample_request)
    
    assert response.success is True
    assert len(response.variants) > 0
    # In dry_run, no DB operations should happen
    # (mocked DB won't show calls, but verifies no errors)


# ==================== Integration Tests ====================


@pytest.mark.asyncio
async def test_bulk_upload_workflow(generator, uploader):
    """Test: Generate and bulk upload workflow"""
    clip_id = "test_clip_bulk"
    
    # Generate components
    video_variants = await generator.generate_video_variants(clip_id, 3)
    text_variants = await generator.generate_text_variants(clip_id, 3)
    thumbnail_variants = await generator.generate_thumbnail_variants(clip_id, 2)
    
    # Generate combinations
    creative_variants = await generator.generate_creative_combinations(
        video_variants=video_variants,
        text_variants=text_variants,
        thumbnail_variants=thumbnail_variants,
        target_count=5,
    )
    
    # Upload all
    upload_results = []
    for variant in creative_variants:
        response = await uploader.upload_creative(
            variant=variant,
            ad_account_id="act_test",
            campaign_id="campaign_test",
            adset_id="adset_test",
        )
        upload_results.append(response)
    
    assert len(upload_results) == 5
    assert all(r.success for r in upload_results)
    assert all(r.meta_creative_id is not None for r in upload_results)


# ==================== Validation Tests ====================


@pytest.mark.asyncio
async def test_text_length_validation(generator):
    """Test: Text variants respect character limits"""
    variants = await generator.generate_text_variants("test_clip", 5)
    
    for variant in variants:
        assert len(variant.headline) <= 40, f"Headline too long: {len(variant.headline)}"
        assert len(variant.primary_text) <= 125, f"Primary text too long: {len(variant.primary_text)}"
        if variant.description:
            assert len(variant.description) <= 30, f"Description too long: {len(variant.description)}"


@pytest.mark.asyncio
async def test_crop_ratio_matching(generator):
    """Test: Video and thumbnail can have matching crop ratios"""
    video_variants = await generator.generate_video_variants("test_clip", 3, [CropRatio.SQUARE])
    thumbnail_variants = await generator.generate_thumbnail_variants("test_clip", 3, [CropRatio.SQUARE])
    
    # All should be square
    assert all(v.crop_ratio == CropRatio.SQUARE for v in video_variants)
    assert all(v.crop_ratio == CropRatio.SQUARE for v in thumbnail_variants)
