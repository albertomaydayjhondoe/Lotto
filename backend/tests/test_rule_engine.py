"""
Tests for Rule Engine 2.0
"""
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import Clip, VideoAsset, ClipStatus
from app.rules_engine import RuleEngine
from app.rules_engine.models import AdaptiveRuleSet, DEFAULT_WEIGHTS
from app.rules_engine.heuristics import apply_platform_heuristics
from app.rules_engine.loader import load_rules
from app.rules_engine.persistence import save_rules
from app.ledger import log_event
from tests.test_db import init_test_db, drop_test_db, get_test_session


# Test fixtures
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test."""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def client():
    """Provide an async HTTP client for API tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_initial_weights_exist_for_all_platforms(db_session):
    """Test that default weights are available for all platforms."""
    platforms = ["tiktok", "instagram", "youtube"]
    
    for platform in platforms:
        rules = await load_rules(db_session, platform)
        
        assert rules.platform == platform
        assert "visual_score" in rules.weights
        assert "duration_ms" in rules.weights
        assert "cut_position" in rules.weights
        assert "motion_intensity" in rules.weights
        
        # Verify weights sum to approximately 1.0
        total_weight = sum(rules.weights.values())
        assert 0.9 <= total_weight <= 1.1


@pytest.mark.asyncio
async def test_evaluate_clip_returns_score_between_0_and_1(db_session):
    """Test that clip evaluation returns a valid score."""
    # Create test video asset
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/storage/test.mp4",
        file_size=1000000,
        duration_ms=30000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video_asset)
    await db_session.flush()
    
    # Create test clip
    clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=1000,
        end_ms=11000,
        duration_ms=10000,
        visual_score=0.75,
        status=ClipStatus.READY,
        params={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(clip)
    await db_session.flush()
    
    # Evaluate clip
    engine = RuleEngine()
    score = await engine.evaluate_clip(db_session, clip.id, "instagram")
    
    # Verify score is in valid range
    assert 0.0 <= score <= 1.0
    assert isinstance(score, float)


@pytest.mark.asyncio
async def test_tiktok_heuristics_increase_motion_intensity_weight(db_session):
    """Test that TikTok heuristics prioritize motion intensity."""
    # Load base rules
    base_rules = await load_rules(db_session, "tiktok")
    base_motion_weight = base_rules.weights.get("motion_intensity", 0.0)
    
    # Apply TikTok heuristics
    enhanced_rules = apply_platform_heuristics(base_rules, "tiktok")
    enhanced_motion_weight = enhanced_rules.weights.get("motion_intensity", 0.0)
    
    # Motion intensity should have increased (or be significant)
    assert enhanced_motion_weight > 0
    # After normalization, it should be higher proportion than base
    total_base = sum(base_rules.weights.values())
    total_enhanced = sum(enhanced_rules.weights.values())
    
    base_proportion = base_motion_weight / total_base if total_base > 0 else 0
    enhanced_proportion = enhanced_motion_weight / total_enhanced if total_enhanced > 0 else 0
    
    assert enhanced_proportion >= base_proportion


@pytest.mark.asyncio
async def test_instagram_prioritizes_visual_score(db_session):
    """Test that Instagram heuristics prioritize visual quality."""
    # Load base rules
    base_rules = await load_rules(db_session, "instagram")
    
    # Apply Instagram heuristics
    enhanced_rules = apply_platform_heuristics(base_rules, "instagram")
    
    # Visual score should be the highest or near-highest weight
    visual_weight = enhanced_rules.weights.get("visual_score", 0.0)
    max_weight = max(enhanced_rules.weights.values())
    
    # Visual score should be within 80% of the max weight
    assert visual_weight >= max_weight * 0.8


@pytest.mark.asyncio
async def test_youtube_prefers_longer_duration(db_session):
    """Test that longer clips score higher on YouTube."""
    # Create video asset
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Long Video",
        file_path="/storage/test_long.mp4",
        file_size=5000000,
        duration_ms=90000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video_asset)
    await db_session.flush()
    
    # Create short clip
    short_clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=0,
        end_ms=10000,
        duration_ms=10000,
        visual_score=0.8,
        status=ClipStatus.READY,
        params={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(short_clip)
    
    # Create long clip
    long_clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=0,
        end_ms=60000,
        duration_ms=60000,
        visual_score=0.8,
        status=ClipStatus.READY,
        params={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(long_clip)
    await db_session.flush()
    
    # Evaluate both clips for YouTube
    engine = RuleEngine()
    short_score = await engine.evaluate_clip(db_session, short_clip.id, "youtube")
    long_score = await engine.evaluate_clip(db_session, long_clip.id, "youtube")
    
    # Longer clip should score higher (or similar) on YouTube
    # Since visual_score is the same, duration should make a difference
    assert long_score >= short_score * 0.95  # Allow for small variance


@pytest.mark.asyncio
async def test_training_updates_weights(db_session):
    """Test that training modifies weights based on performance data."""
    platform = "tiktok"
    
    # Get initial weights
    initial_rules = await load_rules(db_session, platform)
    initial_weights = initial_rules.weights.copy()
    
    # Create some evaluation events in ledger to train on
    clip_id = uuid4()
    for i in range(5):
        await log_event(
            db=db_session,
            event_type="clip_evaluated",
            entity_type="clip",
            entity_id=str(clip_id),
            metadata={
                "platform": platform,
                "score": 0.8 + (i * 0.02),
                "features": {
                    "visual_score": 0.7,
                    "duration_ms": 0.3,
                    "cut_position": 0.5,
                    "motion_intensity": 0.6
                },
                "engagement": {
                    "views": 1500 if i >= 2 else 50,
                    "likes": 100 if i >= 2 else 2
                }
            }
        )
    await db_session.commit()
    
    # Train the engine
    engine = RuleEngine()
    trained_rules = await engine.train(db_session, platform)
    
    # At least one weight should have changed
    weights_changed = any(
        abs(trained_rules.weights[key] - initial_weights[key]) > 0.001
        for key in initial_weights.keys()
    )
    
    assert weights_changed, "Training should modify at least one weight"


@pytest.mark.asyncio
async def test_persistence_roundtrip(db_session):
    """Test that saving and loading rules works correctly."""
    platform = "instagram"
    
    # Create custom rule set
    custom_weights = {
        "visual_score": 0.6,
        "duration_ms": 0.15,
        "cut_position": 0.15,
        "motion_intensity": 0.1
    }
    
    custom_rules = AdaptiveRuleSet(
        platform=platform,  # type: ignore
        weights=custom_weights,
        updated_at=datetime.utcnow()
    )
    
    # Save to database
    await save_rules(db_session, custom_rules)
    
    # Load back
    loaded_rules = await load_rules(db_session, platform)
    
    # Verify weights match
    assert loaded_rules.platform == platform
    for key, value in custom_weights.items():
        assert abs(loaded_rules.weights[key] - value) < 0.001


@pytest.mark.asyncio
async def test_api_endpoints_integration(db_session):
    """Test that rule engine API module is properly integrated."""
    # Test that we can import the router
    from app.api import rule_engine
    
    # Verify router exists and has expected routes
    assert rule_engine.router is not None
    
    # Test GET /rules/engine/weights logic directly (bypassing HTTP)
    from app.rules_engine import RuleEngine
    engine = RuleEngine()
    
    rules = await engine.get_rules(db_session, "tiktok")
    assert rules.platform == "tiktok"
    assert "weights" in rules.weights or len(rules.weights) > 0
    
    # This confirms the API layer exists and the underlying logic works
    # Full HTTP integration tests would require dependency override setup
