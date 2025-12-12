"""
Tests for Publishing Worker module.

Tests the worker loop that processes publish_logs from the queue.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch

from app.models.database import (
    PublishLogModel, Clip, VideoAsset, ClipStatus, SocialAccountModel
)
from app.publishing_worker import run_publishing_worker_once
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
        title="Test Video for Worker",
        file_path="/storage/test_worker.mp4",
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
        handle="@testworker",
        external_id="test_worker_123",
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
async def test_worker_processes_pending_log_success(db, sample_clip, sample_social_account):
    """Test that worker successfully processes a pending log."""
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
    log_id = log.id
    
    # Mock publish_clip to return success
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram",
        external_post_id="instagram_post_12345",
        external_url="https://instagram.com/p/ABC123",
        social_account_id=sample_social_account.id
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Run worker once
        result = await run_publishing_worker_once(db)
        
        # Verify result
        assert result["processed"] is True
        assert result["log_id"] == str(log_id)
        assert result["status"] == "success"
        assert result["error"] is None
        assert result["external_post_id"] == "instagram_post_12345"
        assert result["platform"] == "instagram"
        
        # Verify log was updated in database
        from sqlalchemy import select
        db_result = await db.execute(
            select(PublishLogModel).where(PublishLogModel.id == log_id)
        )
        updated_log = db_result.scalar_one()
        
        assert updated_log.status == "success"
        assert updated_log.external_post_id == "instagram_post_12345"
        assert updated_log.external_url == "https://instagram.com/p/ABC123"
        assert updated_log.published_at is not None


@pytest.mark.asyncio
async def test_worker_marks_failed_on_exception(db, sample_clip):
    """Test that worker marks log as failed when publishing raises exception."""
    # Create a pending log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Mock publish_clip to raise exception
    error_message = "Authentication failed: Invalid API key"
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.side_effect = Exception(error_message)
        
        # Run worker once
        result = await run_publishing_worker_once(db)
        
        # Verify result
        assert result["processed"] is True
        assert result["log_id"] == str(log_id)
        assert result["status"] == "failed"
        assert result["error"] == error_message
        assert result["external_post_id"] is None
        assert result["platform"] == "tiktok"
        
        # Verify log was marked as failed in database
        from sqlalchemy import select
        db_result = await db.execute(
            select(PublishLogModel).where(PublishLogModel.id == log_id)
        )
        updated_log = db_result.scalar_one()
        
        assert updated_log.status == "failed"
        assert updated_log.error_message == error_message
        assert updated_log.published_at is None


@pytest.mark.asyncio
async def test_worker_skips_when_no_pending(db):
    """Test that worker returns processed=False when queue is empty."""
    # No pending logs in database
    result = await run_publishing_worker_once(db)
    
    # Verify result
    assert result["processed"] is False
    assert result["log_id"] is None
    assert result["status"] is None
    assert result["error"] is None
    assert result["external_post_id"] is None
    assert result["platform"] is None


@pytest.mark.asyncio
async def test_worker_follows_fifo_order(db, sample_clip):
    """Test that worker processes logs in FIFO order (oldest first)."""
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
    
    # Mock publish_clip
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Process first log
        result = await run_publishing_worker_once(db)
        
        # Should process the oldest one (log1 - 3 hours ago)
        assert result["processed"] is True
        assert result["log_id"] == str(log1.id)
        assert result["platform"] == "instagram"


@pytest.mark.asyncio
async def test_worker_resilient_multiple_iterations(db, sample_clip):
    """Test that worker can process multiple logs in succession."""
    now = datetime.utcnow()
    
    # Create 3 pending logs
    logs = []
    for i in range(3):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=sample_clip.id,
            platform=["instagram", "tiktok", "youtube"][i],
            status="pending",
            requested_at=now - timedelta(hours=3-i)
        )
        logs.append(log)
        db.add(log)
    
    await db.commit()
    
    # Mock publish_clip
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Process all 3 logs
        processed_ids = []
        for _ in range(3):
            result = await run_publishing_worker_once(db)
            assert result["processed"] is True
            processed_ids.append(result["log_id"])
        
        # All 3 should be processed
        assert len(processed_ids) == 3
        assert len(set(processed_ids)) == 3  # All unique
        
        # Queue should now be empty
        result = await run_publishing_worker_once(db)
        assert result["processed"] is False


@pytest.mark.asyncio
async def test_worker_tracks_worker_id_in_metadata(db, sample_clip):
    """Test that worker tracks worker_id in log metadata."""
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
    
    # Mock publish_clip
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Run worker once
        await run_publishing_worker_once(db)
        
        # Verify metadata contains worker_id
        from sqlalchemy import select
        db_result = await db.execute(
            select(PublishLogModel).where(PublishLogModel.id == log_id)
        )
        updated_log = db_result.scalar_one()
        
        assert updated_log.extra_metadata is not None
        assert "worker_id" in updated_log.extra_metadata
        assert updated_log.extra_metadata["worker_id"].startswith("manual-")
        assert "processed_at" in updated_log.extra_metadata


@pytest.mark.asyncio
async def test_worker_logs_events_to_ledger(db, sample_clip):
    """Test that worker logs events to SocialSyncLedger."""
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
    
    # Mock publish_clip
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Run worker once
        await run_publishing_worker_once(db)
        
        # Commit to ensure all ledger events are saved
        await db.commit()
        
        # Verify events were logged
        from app.ledger import get_events_by_entity
        events = await get_events_by_entity(db, "publish_log", str(log.id))
        
        # Should have at least 2 events: log_taken and log_success
        assert len(events) >= 2
        
        event_types = [e.event_type for e in events]
        assert "publish_worker_log_taken" in event_types
        assert "publish_worker_log_success" in event_types


@pytest.mark.asyncio
async def test_worker_handles_logs_without_social_account(db, sample_clip):
    """Test that worker can process logs without social_account_id."""
    # Create a pending log WITHOUT social_account_id
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        social_account_id=None,  # No social account
        platform="instagram",
        status="pending",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Mock publish_clip
    mock_result = make_publish_result(
        clip_id=sample_clip.id,
        platform="instagram"
    )
    
    with patch("app.publishing_worker.worker.publish_clip", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = mock_result
        
        # Run worker once - should not crash
        result = await run_publishing_worker_once(db)
        
        # Verify it processed successfully
        assert result["processed"] is True
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_worker_ignores_non_pending_logs(db, sample_clip):
    """Test that worker only processes pending logs, not processing/success/failed."""
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
        error_message="Previous error"
    )
    
    db.add_all([log_processing, log_success, log_failed])
    await db.commit()
    
    # Run worker once
    result = await run_publishing_worker_once(db)
    
    # Should return processed=False (no pending logs)
    assert result["processed"] is False
