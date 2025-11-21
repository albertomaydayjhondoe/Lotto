"""
Tests for Publishing Queue module.

Tests the queue operations for processing publish_logs with proper
status transitions and concurrency handling.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import PublishLogModel, Clip, SocialAccountModel
from app.publishing_queue import (
    fetch_next_pending_log,
    mark_log_processing,
    mark_log_success,
    mark_log_failed,
)
from tests.test_db import init_test_db, drop_test_db, get_test_session


# Test fixtures
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test."""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def sample_clip(db):
    """Create a sample clip for testing."""
    from app.models.database import VideoAsset, ClipStatus
    
    # Create video asset first
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video for Queue",
        file_path="/storage/test_queue.mp4",
        file_size=1000000,
        duration_ms=10000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video_asset)
    await db.flush()
    
    # Create clip
    clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=0,
        end_ms=10000,
        duration_ms=10000,
        visual_score=0.85,
        status=ClipStatus.READY,
        params={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(clip)
    await db.commit()
    await db.refresh(clip)
    return clip


@pytest_asyncio.fixture
async def sample_social_account(db):
    """Create a sample social account for testing."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@testuser",
        external_id="test_123",
        extra_metadata={"access_token": "test_token"},
        is_main_account=1,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest.mark.asyncio
async def test_fetch_next_pending_log_returns_oldest(db, sample_clip):
    """Test that fetch_next_pending_log returns the oldest pending log."""
    now = datetime.utcnow()
    
    # Create 3 pending logs with different timestamps
    log1 = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        requested_at=now - timedelta(hours=3)
    )
    log2 = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="pending",
        requested_at=now - timedelta(hours=1)
    )
    log3 = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="pending",
        requested_at=now - timedelta(hours=2)
    )
    
    db.add_all([log1, log2, log3])
    await db.commit()
    
    # Fetch next pending log
    next_log = await fetch_next_pending_log(db)
    
    # Should return the oldest one (log1 - 3 hours ago)
    assert next_log is not None
    assert next_log.id == log1.id
    assert next_log.platform == "instagram"


@pytest.mark.asyncio
async def test_fetch_next_pending_log_returns_none_when_empty(db):
    """Test that fetch_next_pending_log returns None when no pending logs exist."""
    # No logs in database
    next_log = await fetch_next_pending_log(db)
    
    assert next_log is None


@pytest.mark.asyncio
async def test_fetch_next_pending_log_ignores_non_pending(db, sample_clip):
    """Test that fetch_next_pending_log only returns pending logs."""
    now = datetime.utcnow()
    
    # Create logs with different statuses
    log_processing = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        requested_at=now - timedelta(hours=2)
    )
    log_success = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="success",
        requested_at=now - timedelta(hours=3),
        published_at=now - timedelta(hours=2)
    )
    log_failed = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="failed",
        requested_at=now - timedelta(hours=4),
        error_message="Test error"
    )
    log_pending = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        requested_at=now - timedelta(hours=1)
    )
    
    db.add_all([log_processing, log_success, log_failed, log_pending])
    await db.commit()
    
    # Fetch next pending log
    next_log = await fetch_next_pending_log(db)
    
    # Should return only the pending one
    assert next_log is not None
    assert next_log.id == log_pending.id
    assert next_log.status == "pending"


@pytest.mark.asyncio
async def test_mark_log_processing_changes_status(db, sample_clip):
    """Test that mark_log_processing updates status to 'processing'."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Mark as processing
    await mark_log_processing(db, log)
    
    # Verify in database
    await db.refresh(log)
    assert log.status == "processing"
    assert log.updated_at is not None
    
    # Also verify by re-fetching from DB
    from sqlalchemy import select
    result = await db.execute(
        select(PublishLogModel).where(PublishLogModel.id == log_id)
    )
    refreshed_log = result.scalar_one()
    assert refreshed_log.status == "processing"


@pytest.mark.asyncio
async def test_mark_log_success_fills_fields(db, sample_clip):
    """Test that mark_log_success fills all success fields."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Mark as success with external details
    external_post_id = "17841405793187218"
    external_url = "https://www.instagram.com/p/ABC123/"
    extra_metadata = {"likes": 0, "comments": 0}
    
    await mark_log_success(
        db,
        log,
        external_post_id=external_post_id,
        external_url=external_url,
        extra_metadata=extra_metadata
    )
    
    # Verify all fields
    await db.refresh(log)
    assert log.status == "success"
    assert log.external_post_id == external_post_id
    assert log.external_url == external_url
    assert log.published_at is not None
    assert log.updated_at is not None
    assert log.extra_metadata is not None
    assert log.extra_metadata["likes"] == 0
    assert log.extra_metadata["comments"] == 0


@pytest.mark.asyncio
async def test_mark_log_success_merges_metadata(db, sample_clip):
    """Test that mark_log_success merges extra_metadata with existing metadata."""
    # Create a log with existing metadata
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="pending",
        requested_at=datetime.utcnow(),
        extra_metadata={"attempt": 1, "original_file": "video.mp4"}
    )
    db.add(log)
    await db.commit()
    
    # Mark as success with new metadata
    await mark_log_success(
        db,
        log,
        external_post_id="tiktok_12345",
        extra_metadata={"views": 100, "shares": 5}
    )
    
    # Verify metadata is merged
    await db.refresh(log)
    assert log.extra_metadata["attempt"] == 1  # Original preserved
    assert log.extra_metadata["original_file"] == "video.mp4"  # Original preserved
    assert log.extra_metadata["views"] == 100  # New added
    assert log.extra_metadata["shares"] == 5  # New added


@pytest.mark.asyncio
async def test_mark_log_failed_fills_error(db, sample_clip):
    """Test that mark_log_failed stores error message."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Mark as failed with error
    error_message = "Authentication failed: Invalid API key"
    extra_metadata = {"error_code": 401, "error_type": "AuthenticationError"}
    
    await mark_log_failed(
        db,
        log,
        error_message=error_message,
        extra_metadata=extra_metadata
    )
    
    # Verify error details
    await db.refresh(log)
    assert log.status == "failed"
    assert log.error_message == error_message
    assert log.updated_at is not None
    assert log.extra_metadata is not None
    assert log.extra_metadata["error_code"] == 401
    assert log.extra_metadata["error_type"] == "AuthenticationError"


@pytest.mark.asyncio
async def test_mark_log_failed_merges_metadata(db, sample_clip):
    """Test that mark_log_failed merges extra_metadata with existing metadata."""
    # Create a log with existing metadata
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow(),
        extra_metadata={"attempt": 3, "retry_count": 2}
    )
    db.add(log)
    await db.commit()
    
    # Mark as failed with new metadata
    await mark_log_failed(
        db,
        log,
        error_message="Rate limit exceeded",
        extra_metadata={"retry_after": 3600, "error_code": 429}
    )
    
    # Verify metadata is merged
    await db.refresh(log)
    assert log.extra_metadata["attempt"] == 3  # Original preserved
    assert log.extra_metadata["retry_count"] == 2  # Original preserved
    assert log.extra_metadata["retry_after"] == 3600  # New added
    assert log.extra_metadata["error_code"] == 429  # New added


@pytest.mark.asyncio
async def test_queue_processing_workflow(db, sample_clip, sample_social_account):
    """Test the complete queue processing workflow."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        social_account_id=sample_social_account.id,
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Step 1: Fetch from queue
    fetched_log = await fetch_next_pending_log(db)
    assert fetched_log is not None
    assert fetched_log.id == log.id
    
    # Step 2: Mark as processing
    await mark_log_processing(db, fetched_log)
    await db.refresh(fetched_log)
    assert fetched_log.status == "processing"
    
    # Step 3: Simulate successful publishing
    await mark_log_success(
        db,
        fetched_log,
        external_post_id="ig_post_123",
        external_url="https://instagram.com/p/ABC123"
    )
    await db.refresh(fetched_log)
    assert fetched_log.status == "success"
    assert fetched_log.external_post_id == "ig_post_123"
    assert fetched_log.published_at is not None
    
    # Step 4: Verify queue is empty
    next_log = await fetch_next_pending_log(db)
    assert next_log is None


@pytest.mark.asyncio
async def test_multiple_pending_logs_fifo_order(db, sample_clip):
    """Test that multiple pending logs are processed in FIFO order."""
    now = datetime.utcnow()
    
    # Create 5 pending logs at different times
    logs = []
    for i in range(5):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=sample_clip.id,
            platform=["instagram", "tiktok", "youtube", "instagram", "tiktok"][i],
            status="pending",
            requested_at=now - timedelta(hours=5-i)  # 5h, 4h, 3h, 2h, 1h ago
        )
        logs.append(log)
        db.add(log)
    
    await db.commit()
    
    # Process logs one by one
    processed_ids = []
    for _ in range(5):
        log = await fetch_next_pending_log(db)
        assert log is not None
        processed_ids.append(log.id)
        await mark_log_processing(db, log)
    
    # Verify FIFO order (oldest first)
    assert processed_ids[0] == logs[0].id  # 5 hours ago
    assert processed_ids[1] == logs[1].id  # 4 hours ago
    assert processed_ids[2] == logs[2].id  # 3 hours ago
    assert processed_ids[3] == logs[3].id  # 2 hours ago
    assert processed_ids[4] == logs[4].id  # 1 hour ago
    
    # Queue should be empty now
    next_log = await fetch_next_pending_log(db)
    assert next_log is None
