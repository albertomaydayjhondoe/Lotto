"""
Tests for Publishing Webhooks and Reconciliation.

Tests webhook handlers and reconciliation logic.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import PublishLogModel, Clip, VideoAsset, ClipStatus
from app.publishing_webhooks import (
    handle_instagram_webhook,
    handle_tiktok_webhook,
    handle_youtube_webhook
)
from app.publishing_reconciliation import reconcile_publications
from test_db import init_test_db, drop_test_db, get_test_session


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
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video for Webhooks",
        file_path="/storage/test_webhooks.mp4",
        file_size=1000000,
        duration_ms=10000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video_asset)
    await db.flush()
    
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEBHOOK TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_webhook_instagram_updates_publish_log(db, sample_clip):
    """Test that Instagram webhook updates the publish log correctly."""
    # Create a publish log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        external_post_id="instagram_post_12345",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Simulate Instagram webhook
    payload = {
        "external_post_id": "instagram_post_12345",
        "media_url": "https://www.instagram.com/p/ABC123/",
        "status": "published",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    result = await handle_instagram_webhook(db, payload)
    
    # Verify response
    assert result["status"] == "ok"
    
    # Verify log was updated
    await db.refresh(log)
    assert log.extra_metadata is not None
    assert log.extra_metadata["webhook_received"] is True
    assert log.extra_metadata["webhook_platform"] == "instagram"
    assert log.extra_metadata["media_url"] == "https://www.instagram.com/p/ABC123/"
    assert log.extra_metadata["webhook_status"] == "published"


@pytest.mark.asyncio
async def test_webhook_tiktok_updates_publish_log(db, sample_clip):
    """Test that TikTok webhook updates the publish log correctly."""
    # Create a publish log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="processing",
        external_post_id="tiktok_video_67890",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Simulate TikTok webhook
    payload = {
        "external_post_id": "tiktok_video_67890",
        "task_id": "task_abc123",
        "complete": True,
        "video_url": "https://www.tiktok.com/@user/video/123"
    }
    
    result = await handle_tiktok_webhook(db, payload)
    
    # Verify response
    assert result["status"] == "ok"
    
    # Verify log was updated
    await db.refresh(log)
    assert log.extra_metadata is not None
    assert log.extra_metadata["webhook_received"] is True
    assert log.extra_metadata["webhook_platform"] == "tiktok"
    assert log.extra_metadata["task_id"] == "task_abc123"
    assert log.extra_metadata["complete"] is True


@pytest.mark.asyncio
async def test_webhook_youtube_updates_publish_log(db, sample_clip):
    """Test that YouTube webhook updates the publish log correctly."""
    # Create a publish log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="processing",
        external_post_id="youtube_video_XYZ789",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    # Simulate YouTube webhook
    payload = {
        "external_post_id": "youtube_video_XYZ789",
        "videoId": "dQw4w9WgXcQ",
        "publishAt": "2024-01-15T10:30:00Z",
        "status": "published"
    }
    
    result = await handle_youtube_webhook(db, payload)
    
    # Verify response
    assert result["status"] == "ok"
    
    # Verify log was updated
    await db.refresh(log)
    assert log.extra_metadata is not None
    assert log.extra_metadata["webhook_received"] is True
    assert log.extra_metadata["webhook_platform"] == "youtube"
    assert log.extra_metadata["videoId"] == "dQw4w9WgXcQ"
    assert log.extra_metadata["webhook_status"] == "published"


@pytest.mark.asyncio
async def test_webhook_missing_external_post_id(db):
    """Test webhook handler with missing external_post_id."""
    payload = {
        "media_url": "https://instagram.com/p/ABC/",
        "status": "published"
    }
    
    result = await handle_instagram_webhook(db, payload)
    
    assert result["status"] == "error"
    assert "external_post_id" in result["message"].lower()


@pytest.mark.asyncio
async def test_webhook_log_not_found(db):
    """Test webhook handler when log doesn't exist."""
    payload = {
        "external_post_id": "nonexistent_post_123",
        "status": "published"
    }
    
    result = await handle_instagram_webhook(db, payload)
    
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
async def test_webhook_logs_event_to_ledger(db, sample_clip):
    """Test that webhook events are logged to the ledger."""
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        external_post_id="instagram_post_ledger",
        requested_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    payload = {
        "external_post_id": "instagram_post_ledger",
        "media_url": "https://instagram.com/p/XYZ/",
        "status": "published"
    }
    
    await handle_instagram_webhook(db, payload)
    await db.commit()  # Ensure the event is committed
    
    # Verify event was logged
    from app.ledger import get_events_by_entity
    events = await get_events_by_entity(db, "publish_log", str(log_id))
    
    event_types = [e.event_type for e in events]
    assert len(events) > 0, f"No events found for log {log_id}"
    assert "publish_webhook_received" in event_types


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# RECONCILIATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_reconcile_marks_success_when_data_present(db, sample_clip):
    """Test reconciliation marks log as success when webhook data exists."""
    # Create a stale processing log with webhook data
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        external_post_id="ig_post_recon_success",
        extra_metadata={
            "webhook_received": True,
            "webhook_status": "published",
            "media_url": "https://instagram.com/p/ABC/"
        },
        requested_at=datetime.utcnow() - timedelta(minutes=15),
        updated_at=datetime.utcnow() - timedelta(minutes=15)
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Run reconciliation
    result = await reconcile_publications(db, since_minutes=10)
    
    # Verify statistics
    assert result["total_checked"] == 1
    assert result["marked_success"] == 1
    assert result["marked_failed"] == 0
    assert str(log_id) in result["success_log_ids"]
    
    # Verify log was marked as success
    await db.refresh(log)
    assert log.status == "success"
    assert log.extra_metadata["reconciled"] is True
    assert log.extra_metadata["reconciliation_reason"] == "webhook_confirmed"


@pytest.mark.asyncio
async def test_reconcile_marks_failed_after_timeout(db, sample_clip):
    """Test reconciliation marks log as failed when no webhook received."""
    # Create a stale processing log WITHOUT webhook data
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="processing",
        external_post_id="tiktok_post_timeout",
        extra_metadata={},  # No webhook received
        requested_at=datetime.utcnow() - timedelta(minutes=20),
        updated_at=datetime.utcnow() - timedelta(minutes=20)
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Run reconciliation
    result = await reconcile_publications(db, since_minutes=10)
    
    # Verify statistics
    assert result["total_checked"] == 1
    assert result["marked_success"] == 0
    assert result["marked_failed"] == 1
    assert str(log_id) in result["failed_log_ids"]
    
    # Verify log was marked as failed
    await db.refresh(log)
    assert log.status == "failed"
    assert "No webhook received" in log.error_message
    assert log.extra_metadata["reconciled"] is True
    assert log.extra_metadata["reconciliation_reason"] == "webhook_timeout"


@pytest.mark.asyncio
async def test_reconcile_skips_success_logs(db, sample_clip):
    """Test reconciliation skips logs already in success status."""
    # Create a success log (should be ignored)
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="success",
        external_post_id="yt_already_success",
        published_at=datetime.utcnow() - timedelta(hours=1),
        requested_at=datetime.utcnow() - timedelta(minutes=30),
        updated_at=datetime.utcnow() - timedelta(minutes=30)
    )
    db.add(log)
    await db.commit()
    
    # Run reconciliation
    result = await reconcile_publications(db, since_minutes=20)
    
    # Verify no logs were processed (success logs are not in processing/retry)
    assert result["total_checked"] == 0


@pytest.mark.asyncio
async def test_reconcile_respects_time_window(db, sample_clip):
    """Test reconciliation only processes logs older than time window."""
    now = datetime.utcnow()
    
    # Create two logs: one old, one recent
    old_log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        external_post_id="ig_old",
        requested_at=now - timedelta(minutes=20),
        updated_at=now - timedelta(minutes=20)
    )
    recent_log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="tiktok",
        status="processing",
        external_post_id="tiktok_recent",
        requested_at=now - timedelta(minutes=5),
        updated_at=now - timedelta(minutes=5)
    )
    db.add_all([old_log, recent_log])
    await db.commit()
    
    # Run reconciliation with 10-minute window
    result = await reconcile_publications(db, since_minutes=10)
    
    # Should only process the old log
    assert result["total_checked"] == 1


@pytest.mark.asyncio
async def test_reconcile_handles_retry_status(db, sample_clip):
    """Test reconciliation processes logs in retry status."""
    # Create a stale retry log with webhook
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="youtube",
        status="retry",
        retry_count=2,
        external_post_id="yt_retry_recon",
        extra_metadata={
            "webhook_received": True,
            "webhook_status": "published"
        },
        requested_at=datetime.utcnow() - timedelta(minutes=30),
        updated_at=datetime.utcnow() - timedelta(minutes=15)
    )
    db.add(log)
    await db.commit()
    
    # Run reconciliation
    result = await reconcile_publications(db, since_minutes=10)
    
    # Should mark as success
    assert result["marked_success"] == 1
    await db.refresh(log)
    assert log.status == "success"


@pytest.mark.asyncio
async def test_reconcile_logs_events(db, sample_clip):
    """Test that reconciliation logs events to the ledger."""
    # Create a stale log
    log = PublishLogModel(
        id=uuid4(),
        clip_id=sample_clip.id,
        platform="instagram",
        status="processing",
        external_post_id="ig_event_test",
        extra_metadata={
            "webhook_received": True,
            "webhook_status": "published"
        },
        requested_at=datetime.utcnow() - timedelta(minutes=15),
        updated_at=datetime.utcnow() - timedelta(minutes=15)
    )
    db.add(log)
    await db.commit()
    log_id = log.id
    
    # Run reconciliation
    await reconcile_publications(db, since_minutes=10)
    await db.commit()  # Ensure the event is committed
    
    # Verify event was logged
    from app.ledger import get_events_by_entity
    events = await get_events_by_entity(db, "publish_log", str(log_id))
    
    event_types = [e.event_type for e in events]
    assert len(events) > 0, f"No events found for log {log_id}"
    assert "publish_reconciled" in event_types


@pytest.mark.asyncio
async def test_reconcile_multiple_logs(db, sample_clip):
    """Test reconciliation handles multiple logs correctly."""
    now = datetime.utcnow()
    
    # Create 5 stale logs: 3 with webhook, 2 without
    logs_with_webhook = []
    logs_without_webhook = []
    
    for i in range(3):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=sample_clip.id,
            platform="instagram",
            status="processing",
            external_post_id=f"ig_with_webhook_{i}",
            extra_metadata={
                "webhook_received": True,
                "webhook_status": "published"
            },
            requested_at=now - timedelta(minutes=20),
            updated_at=now - timedelta(minutes=20)
        )
        logs_with_webhook.append(log)
        db.add(log)
    
    for i in range(2):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=sample_clip.id,
            platform="tiktok",
            status="processing",
            external_post_id=f"tiktok_without_webhook_{i}",
            extra_metadata={},
            requested_at=now - timedelta(minutes=20),
            updated_at=now - timedelta(minutes=20)
        )
        logs_without_webhook.append(log)
        db.add(log)
    
    await db.commit()
    
    # Run reconciliation
    result = await reconcile_publications(db, since_minutes=10)
    
    # Verify statistics
    assert result["total_checked"] == 5
    assert result["marked_success"] == 3
    assert result["marked_failed"] == 2
    assert len(result["success_log_ids"]) == 3
    assert len(result["failed_log_ids"]) == 2
