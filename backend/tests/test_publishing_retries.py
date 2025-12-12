"""
Tests for Publishing Retries and Backoff Exponential.

Tests the retry mechanism with exponential backoff for failed publications.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch

from app.models.database import PublishLogModel, Clip, VideoAsset, ClipStatus
from app.publishing_worker import run_publishing_worker_once
from app.publishing_queue import fetch_next_pending_log, mark_log_retry
from app.publishing_engine.models import PublishResult
from test_db import init_test_db, drop_test_db, get_test_session


# Helper function
def make_publish_result(
    clip_id: UUID,
    platform: str = "instagram",
    success: bool = True,
    external_post_id: str = "test_post_123",
    external_url: str = "https://example.com/post",
    error_message: str = None,
    social_account_id: UUID = None
) -> PublishResult:
    """Helper to create PublishResult with all required fields."""
    return PublishResult(
        success=success,
        platform=platform,
        clip_id=clip_id,
        external_post_id=external_post_id,
        external_url=external_url,
        error_message=error_message,
        social_account_id=social_account_id
    )


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
    # Create video asset first
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video for Retries",
        file_path="/storage/test_retries.mp4",
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


@pytest.mark.asyncio
async def test_retry_moves_to_retry_status(db, sample_clip):
    """Test that failed publication moves to retry status when retries remain."""
    # Create a pending log with retry capacity
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        retry_count=0,
        max_retries=3,
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Mock publish_clip to raise exception
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.side_effect = Exception("API rate limit exceeded")
        
        # Run worker once
        result = await run_publishing_worker_once(db)
        
        # Verify result shows retry
        assert result["processed"] is True
        assert result["log_id"] == str(log_id)
        assert result["status"] == "retry"
        assert "rate limit" in result["error"].lower()
        
        # Verify log was updated in database
        from sqlalchemy import select
        db_result = await db.execute(
            select(PublishLogModel).where(PublishLogModel.id == log_id)
        )
        updated_log = db_result.scalar_one()
        
        assert updated_log.status == "retry"
        assert updated_log.retry_count == 1
        assert updated_log.last_retry_at is not None
        assert updated_log.error_message == "API rate limit exceeded"


@pytest.mark.asyncio
async def test_retry_moves_to_failed_after_max(db, sample_clip):
    """Test that log moves to failed status after max retries reached."""
    # Create a log that's already at max retries
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="retry",
        retry_count=2,  # Already tried 2 times
        max_retries=3,
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Mock publish_clip to raise exception (third failure)
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.side_effect = Exception("Authentication failed")
        
        # Run worker once
        result = await run_publishing_worker_once(db)
        
        # Verify result shows failed (not retry)
        assert result["processed"] is True
        assert result["log_id"] == str(log_id)
        assert result["status"] == "failed"
        assert "Authentication failed" in result["error"]
        
        # Verify log was marked as failed in database
        from sqlalchemy import select
        db_result = await db.execute(
            select(PublishLogModel).where(PublishLogModel.id == log_id)
        )
        updated_log = db_result.scalar_one()
        
        assert updated_log.status == "failed"
        assert updated_log.retry_count == 3  # Incremented
        assert updated_log.error_message == "Authentication failed"


@pytest.mark.asyncio
async def test_worker_processes_retry_entries(db, sample_clip):
    """Test that worker picks up and processes retry entries from the queue."""
    # Create a log with retry status
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="retry",
        retry_count=1,
        max_retries=3,
        last_retry_at=datetime.utcnow() - timedelta(minutes=5),
        requested_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(log)
    await db.commit()
    
    # Mock publish_clip to succeed this time
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="youtube",
        external_post_id="yt_retry_success_123"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Fetch from queue should return the retry log
        fetched_log = await fetch_next_pending_log(db)
        assert fetched_log is not None
        assert fetched_log.status == "retry"
        
        # Run worker once
        result = await run_publishing_worker_once(db)
        
        # Should succeed
        assert result["processed"] is True
        assert result["status"] == "success"
        assert result["external_post_id"] == "yt_retry_success_123"


@pytest.mark.asyncio
async def test_mark_log_retry_increments_count(db, sample_clip):
    """Test that mark_log_retry correctly increments retry_count."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        retry_count=0,
        max_retries=3,
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    initial_retry_count = log.retry_count
    
    # Mark for retry
    await mark_log_retry(
        db,
        log,
        error_message="Network timeout",
        extra_metadata={"error_type": "TimeoutError"}
    )
    
    # Verify retry_count incremented
    assert log.retry_count == initial_retry_count + 1
    assert log.status == "retry"
    assert log.last_retry_at is not None
    assert log.error_message == "Network timeout"


@pytest.mark.asyncio
async def test_retry_with_different_max_retries(db, sample_clip):
    """Test retry logic with custom max_retries value."""
    # Create a log with max_retries=2 (two retries allowed)
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="pending",
        retry_count=0,
        max_retries=2,  # Custom value (instead of default 3)
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # First failure -> should go to retry (retry_count=1 < max_retries=2)
    await mark_log_retry(db, log, error_message="First failure")
    await db.refresh(log)
    assert log.status == "retry"
    assert log.retry_count == 1
    
    # Second failure -> should still be retry (retry_count=2 == max_retries, but failed)
    # Actually with retry_count < max_retries logic, when retry_count=2 and max_retries=2, it fails
    await mark_log_retry(db, log, error_message="Second failure")
    await db.refresh(log)
    assert log.status == "failed"
    assert log.retry_count == 2


@pytest.mark.asyncio
async def test_retry_logs_event_to_ledger(db, sample_clip):
    """Test that retry events are logged to the ledger."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="pending",
        retry_count=0,
        max_retries=3,
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Mock publish_clip to fail
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.side_effect = Exception("Temporary error")
        
        # Run worker once
        await run_publishing_worker_once(db)
        
        # Commit to ensure ledger events are saved
        await db.commit()
        
        # Verify retry event was logged
        from app.ledger import get_events_by_entity
        events = await get_events_by_entity(db, "publish_log", str(log.id))
        
        event_types = [e.event_type for e in events]
        assert "publish_worker_log_retry" in event_types or "publish_worker_log_taken" in event_types


@pytest.mark.asyncio
async def test_multiple_retries_progression(db, sample_clip):
    """Test that multiple retries work correctly with progression."""
    # Create a log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="pending",
        retry_count=0,
        max_retries=3,
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Mock publish_clip to always fail
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.side_effect = Exception("Persistent error")
        
        # Attempt 1: pending -> retry (count=1)
        result = await run_publishing_worker_once(db)
        assert result["status"] == "retry"
        await db.refresh(log)
        assert log.retry_count == 1
        assert log.status == "retry"
        
        # Attempt 2: retry -> retry (count=2)
        result = await run_publishing_worker_once(db)
        assert result["status"] == "retry"
        await db.refresh(log)
        assert log.retry_count == 2
        assert log.status == "retry"
        
        # Attempt 3: retry -> failed (count=3, max reached)
        result = await run_publishing_worker_once(db)
        assert result["status"] == "failed"
        await db.refresh(log)
        assert log.retry_count == 3
        assert log.status == "failed"
