"""
Tests for Dashboard API (PASO 6.1)

This test suite validates the internal dashboard API layer:
1. Overview stats endpoint
2. Queue stats endpoint
3. Orchestrator stats endpoint
4. Platform stats endpoint
5. Campaign stats endpoint
6. Empty database returns zeros
7. Optional fields handling
8. Schema validation
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.dashboard_api.service import (
    get_overview_stats,
    get_queue_stats,
    get_orchestrator_stats,
    get_platform_stats,
    get_campaign_stats
)
from app.dashboard_api.schemas import (
    OverviewStats,
    QueueStats,
    OrchestratorStats,
    PlatformStats,
    CampaignStats
)
from app.models.database import (
    VideoAsset,
    Clip,
    ClipVariant,
    Publication,
    Job,
    Campaign,
    PublishLogModel,
    JobStatus,
    ClipStatus,
    CampaignStatus
)
from test_db import init_test_db, drop_test_db, get_test_session


# Fixtures for test database
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def test_db():
    """Get async test database session"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def sample_data(test_db):
    """Create sample data for testing."""
    # Create videos
    video1 = VideoAsset(
        id=uuid4(),
        file_path="/test/video1.mp4",
        duration_ms=120000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    video2 = VideoAsset(
        id=uuid4(),
        file_path="/test/video2.mp4",
        duration_ms=180000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(video1)
    test_db.add(video2)
    
    # Create jobs
    job1 = Job(
        id=uuid4(),
        job_type="clip_generation",
        status=JobStatus.PENDING,
        params={"platform": "instagram", "duration": 30},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    job2 = Job(
        id=uuid4(),
        job_type="clip_generation",
        status=JobStatus.PROCESSING,
        params={"platform": "tiktok", "duration": 30},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    job3 = Job(
        id=uuid4(),
        job_type="clip_generation",
        status=JobStatus.FAILED,
        params={"platform": "youtube", "duration": 30},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    job4 = Job(
        id=uuid4(),
        job_type="clip_generation",
        status=JobStatus.COMPLETED,
        params={"platform": "instagram", "duration": 30},
        video_asset_id=video1.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add_all([job1, job2, job3, job4])
    
    # Create clips
    clip1 = Clip(
        id=uuid4(),
        video_asset_id=video1.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=0.85,
        status=ClipStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    clip2 = Clip(
        id=uuid4(),
        video_asset_id=video1.id,
        start_ms=30000,
        end_ms=60000,
        duration_ms=30000,
        visual_score=0.92,
        status=ClipStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    clip3 = Clip(
        id=uuid4(),
        video_asset_id=video2.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=0.78,
        status=ClipStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add_all([clip1, clip2, clip3])
    
    # Create campaigns
    campaign1 = Campaign(
        id=uuid4(),
        name="Test Campaign 1",
        status=CampaignStatus.DRAFT,
        clip_id=clip1.id,
        budget_cents=100000,  # $1000
        targeting={"age": "18-35"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    campaign2 = Campaign(
        id=uuid4(),
        name="Test Campaign 2",
        status=CampaignStatus.ACTIVE,
        clip_id=clip2.id,
        budget_cents=250000,  # $2500
        targeting={"age": "25-45"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    campaign3 = Campaign(
        id=uuid4(),
        name="Test Campaign 3",
        status=CampaignStatus.COMPLETED,
        clip_id=clip3.id,
        budget_cents=500000,  # $5000
        targeting={"age": "30-50"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add_all([campaign1, campaign2, campaign3])
    
    # Create publish logs
    now = datetime.utcnow()
    log1 = PublishLogModel(
        id=uuid4(),
        clip_id=clip1.id,
        platform="instagram",
        status="pending",
        requested_at=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2)
    )
    log2 = PublishLogModel(
        id=uuid4(),
        clip_id=clip2.id,
        platform="tiktok",
        status="success",
        requested_at=now - timedelta(hours=1),
        published_at=now - timedelta(minutes=30),
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(minutes=30)
    )
    log3 = PublishLogModel(
        id=uuid4(),
        clip_id=clip3.id,
        platform="youtube",
        status="failed",
        requested_at=now - timedelta(hours=3),
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(hours=3)
    )
    log4 = PublishLogModel(
        id=uuid4(),
        clip_id=clip1.id,
        platform="instagram",
        status="processing",
        requested_at=now - timedelta(minutes=10),
        created_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=10)
    )
    test_db.add_all([log1, log2, log3, log4])
    
    await test_db.commit()
    
    return {
        "videos": [video1, video2],
        "jobs": [job1, job2, job3, job4],
        "clips": [clip1, clip2, clip3],
        "campaigns": [campaign1, campaign2, campaign3],
        "logs": [log1, log2, log3, log4]
    }


# Test 1: Overview stats with data
@pytest.mark.asyncio
async def test_overview_stats(test_db, sample_data):
    """Test overview stats endpoint with sample data."""
    stats = await get_overview_stats(test_db)
    
    assert isinstance(stats, OverviewStats)
    assert stats.total_videos == 2
    assert stats.total_clips == 3
    assert stats.total_jobs == 4
    assert stats.total_campaigns == 3
    assert stats.pending_jobs == 1
    assert stats.processing_jobs == 1
    assert stats.failed_jobs == 1
    assert stats.success_logs == 1
    assert stats.failed_logs == 1
    assert stats.scheduled_publications == 1  # pending status


# Test 2: Queue stats with data
@pytest.mark.asyncio
async def test_queue_stats(test_db, sample_data):
    """Test queue stats endpoint with sample data."""
    stats = await get_queue_stats(test_db)
    
    assert isinstance(stats, QueueStats)
    assert stats.pending == 1
    assert stats.processing == 1
    assert stats.success == 1
    assert stats.failed == 1
    assert stats.avg_processing_time_ms is not None
    assert stats.avg_processing_time_ms > 0
    assert stats.oldest_pending_age_seconds is not None
    assert stats.oldest_pending_age_seconds > 0


# Test 3: Orchestrator stats with data
@pytest.mark.asyncio
async def test_orchestrator_stats(test_db, sample_data):
    """Test orchestrator stats endpoint with sample data."""
    stats = await get_orchestrator_stats(test_db)
    
    assert isinstance(stats, OrchestratorStats)
    assert stats.last_run_at is not None
    assert stats.actions_last_run >= 0
    assert stats.actions_last_24h >= 0
    assert 0.0 <= stats.queue_saturation <= 1.0
    assert stats.active_workers >= 0


# Test 4: Platform stats with data
@pytest.mark.asyncio
async def test_platform_stats(test_db, sample_data):
    """Test platform stats endpoint with sample data."""
    stats = await get_platform_stats(test_db)
    
    assert isinstance(stats, PlatformStats)
    
    # Instagram - has 1 pending log + 1 processing log for clip1
    assert stats.instagram.clips_ready >= 1
    
    # TikTok - has 1 success log
    assert stats.tiktok.clips_published == 1
    
    # YouTube - has 1 failed log
    assert stats.youtube.clips_ready == 0  # No pending for youtube
    
    # Other
    assert stats.other.clips_ready == 0
    assert stats.other.clips_published == 0


# Test 5: Campaign stats with data
@pytest.mark.asyncio
async def test_campaign_stats(test_db, sample_data):
    """Test campaign stats endpoint with sample data."""
    stats = await get_campaign_stats(test_db)
    
    assert isinstance(stats, CampaignStats)
    assert stats.draft == 1
    assert stats.active == 1
    assert stats.paused == 0
    assert stats.completed == 1
    assert stats.total_budget_spent == 0.0  # Simulated


# Test 6: Empty database returns zeros
@pytest.mark.asyncio
async def test_empty_database_returns_zeroes(test_db):
    """Test that empty database returns zero values, not errors."""
    # Overview
    overview = await get_overview_stats(test_db)
    assert overview.total_videos == 0
    assert overview.total_clips == 0
    assert overview.total_jobs == 0
    assert overview.total_campaigns == 0
    
    # Queue
    queue = await get_queue_stats(test_db)
    assert queue.pending == 0
    assert queue.processing == 0
    assert queue.success == 0
    assert queue.failed == 0
    assert queue.avg_processing_time_ms is None
    assert queue.oldest_pending_age_seconds is None
    
    # Orchestrator
    orchestrator = await get_orchestrator_stats(test_db)
    assert orchestrator.last_run_at is None
    assert orchestrator.actions_last_run == 0
    assert orchestrator.actions_last_24h == 0
    assert orchestrator.queue_saturation == 0.0
    assert orchestrator.active_workers == 0
    
    # Platforms
    platforms = await get_platform_stats(test_db)
    assert platforms.instagram.clips_ready == 0
    assert platforms.tiktok.clips_ready == 0
    assert platforms.youtube.clips_ready == 0
    assert platforms.other.clips_ready == 0
    
    # Campaigns
    campaigns = await get_campaign_stats(test_db)
    assert campaigns.draft == 0
    assert campaigns.active == 0
    assert campaigns.paused == 0
    assert campaigns.completed == 0


# Test 7: Stats do not crash without optional fields
@pytest.mark.asyncio
async def test_stats_do_not_crash_without_optional_fields(test_db):
    """Test that stats functions handle missing optional fields gracefully."""
    # Create minimal video
    video = VideoAsset(
        id=uuid4(),
        file_path="/test/minimal.mp4",
        duration_ms=30000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(video)
    
    # Create minimal clip without visual_score
    clip = Clip(
        id=uuid4(),
        video_asset_id=video.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=None,  # Missing optional field
        status=ClipStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(clip)
    
    # Create publish log without published_at
    log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow(),
        published_at=None,  # Missing optional field
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(log)
    await test_db.commit()
    
    # Should not crash
    overview = await get_overview_stats(test_db)
    assert overview.total_clips == 1
    
    queue = await get_queue_stats(test_db)
    assert queue.pending == 1
    
    platforms = await get_platform_stats(test_db)
    assert platforms.instagram.clips_ready == 1


# Test 8: Schema validation
@pytest.mark.asyncio
async def test_schema_validation(test_db, sample_data):
    """Test that all schemas validate correctly."""
    # Overview
    overview = await get_overview_stats(test_db)
    assert overview.model_dump()  # Should serialize without error
    
    # Queue
    queue = await get_queue_stats(test_db)
    assert queue.model_dump()
    
    # Orchestrator
    orchestrator = await get_orchestrator_stats(test_db)
    assert orchestrator.model_dump()
    
    # Platforms
    platforms = await get_platform_stats(test_db)
    assert platforms.model_dump()
    assert platforms.instagram.model_dump()
    
    # Campaigns
    campaigns = await get_campaign_stats(test_db)
    assert campaigns.model_dump()


# Test 9: Queue stats calculates processing time correctly
@pytest.mark.asyncio
async def test_queue_processing_time_calculation(test_db):
    """Test that average processing time is calculated correctly."""
    now = datetime.utcnow()
    
    # Create video and clip
    video = VideoAsset(
        id=uuid4(),
        file_path="/test/timed.mp4",
        duration_ms=30000,
        created_at=now,
        updated_at=now
    )
    test_db.add(video)
    
    clip = Clip(
        id=uuid4(),
        video_asset_id=video.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        status=ClipStatus.READY,
        created_at=now,
        updated_at=now
    )
    test_db.add(clip)
    
    # Create log with known processing time: 5 seconds
    log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="success",
        requested_at=now - timedelta(seconds=5),
        published_at=now,
        created_at=now - timedelta(seconds=5),
        updated_at=now
    )
    test_db.add(log)
    await test_db.commit()
    
    stats = await get_queue_stats(test_db)
    assert stats.avg_processing_time_ms is not None
    # Should be around 5000ms (5 seconds)
    assert 4000 < stats.avg_processing_time_ms < 6000


# Test 10: Platform stats aggregates correctly
@pytest.mark.asyncio
async def test_platform_stats_aggregation(test_db):
    """Test that platform stats aggregate multiple clips correctly."""
    # Create video
    video = VideoAsset(
        id=uuid4(),
        file_path="/test/ig_video.mp4",
        duration_ms=150000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(video)
    
    # Create multiple clips for Instagram
    clips_ids = []
    for i in range(5):
        clip = Clip(
            id=uuid4(),
            video_asset_id=video.id,
            start_ms=i * 30000,
            end_ms=(i + 1) * 30000,
            duration_ms=30000,
            visual_score=0.8 + (i * 0.02),  # Scores from 0.8 to 0.88
            status=ClipStatus.READY,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(clip)
        clips_ids.append(clip.id)
    
    # Create publish logs for Instagram (pending status counts as ready)
    for clip_id in clips_ids:
        log = PublishLogModel(
            id=uuid4(),
            clip_id=clip_id,
            platform="instagram",
            status="pending",
            requested_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(log)
    
    await test_db.commit()
    
    stats = await get_platform_stats(test_db)
    assert stats.instagram.clips_ready == 5
    # Average score should be around 0.84
    assert 0.83 < stats.instagram.avg_score < 0.85
