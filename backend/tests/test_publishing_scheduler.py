"""
Tests for Publishing Scheduler (PASO 4.4).

Cobertura completa:
- 2 tests de modelo
- 3 tests de scheduler core
- 2 tests de ventanas horarias
- 2 tests de MIN_GAP_MINUTES
- 2 tests de scheduler_tick
- 1 test de endpoint /scheduler/tick
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import PublishLogModel, Clip, VideoAsset, ClipStatus, SocialAccountModel
from app.publishing_scheduler.models import ScheduleRequest
from app.publishing_scheduler.scheduler import (
    schedule_publication,
    validate_and_adjust_schedule,
    scheduler_tick,
    get_scheduled_logs_for_clip
)
from app.core.config import settings
from test_db import init_test_db, drop_test_db, get_test_session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
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
        title="Test Video for Scheduler",
        file_path="/storage/test_scheduler.mp4",
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


@pytest_asyncio.fixture
async def sample_social_account(db):
    """Create a sample social account for testing."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@testuser",
        external_id="test_user_123",
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS DE MODELO (2 tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_publish_log_has_schedule_fields(db, sample_clip, sample_social_account):
    """Test that PublishLogModel has all scheduling fields."""
    log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=datetime.utcnow() + timedelta(hours=1),
        scheduled_window_end=datetime.utcnow() + timedelta(hours=3),
        scheduled_by="manual"
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    assert log.schedule_type == "scheduled"
    assert log.scheduled_for is not None
    assert log.scheduled_window_end is not None
    assert log.scheduled_by == "manual"
    assert log.status == "scheduled"


@pytest.mark.asyncio
async def test_create_scheduled_log_defaults(db, sample_clip, sample_social_account):
    """Test that schedule_type defaults to 'immediate'."""
    log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="pending"
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    assert log.schedule_type == "immediate"
    assert log.scheduled_for is None
    assert log.scheduled_window_end is None
    assert log.scheduled_by is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS DE SCHEDULER CORE (3 tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_schedule_publication_creates_scheduled_log(db, sample_clip, sample_social_account):
    """Test that schedule_publication creates a log with status=scheduled."""
    tomorrow_20h = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )
    
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="instagram",
        social_account_id=str(sample_social_account.id),
        scheduled_for=tomorrow_20h,
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "scheduled"
    assert response.publish_log_id is not None
    assert response.scheduled_for == tomorrow_20h


@pytest.mark.asyncio
async def test_schedule_publication_rejects_invalid_clip(db, sample_social_account):
    """Test that scheduler rejects non-existent clip."""
    request = ScheduleRequest(
        clip_id=str(uuid4()),  # Non-existent clip
        platform="instagram",
        social_account_id=str(sample_social_account.id),
        scheduled_for=datetime.utcnow() + timedelta(hours=2),
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "rejected"
    assert "Clip not found" in response.reason


@pytest.mark.asyncio
async def test_schedule_publication_rejects_platform_mismatch(db, sample_clip, sample_social_account):
    """Test that scheduler rejects when platform doesn't match account."""
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="tiktok",  # Account is Instagram
        social_account_id=str(sample_social_account.id),
        scheduled_for=datetime.utcnow() + timedelta(hours=2),
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "rejected"
    assert "Platform mismatch" in response.reason


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS DE VENTANAS HORARIAS (2 tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_scheduler_respects_instagram_window(db, sample_clip, sample_social_account):
    """Test that scheduler adjusts time to Instagram window (18:00-23:00)."""
    # Schedule for 14:00 (BEFORE window)
    tomorrow_14h = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="instagram",
        social_account_id=str(sample_social_account.id),
        scheduled_for=tomorrow_14h,
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "scheduled"
    assert response.scheduled_for.hour == 18  # Moved to start of window
    assert response.reason is not None
    assert "platform window" in response.reason.lower()


@pytest.mark.asyncio
async def test_scheduler_respects_tiktok_window(db, sample_clip):
    """Test that TikTok window (16:00-24:00) is respected."""
    # Create TikTok account
    tiktok_account = SocialAccountModel(
        id=uuid4(),
        platform="tiktok",
        handle="@tiktokuser",
        external_id="tiktok_123",
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(tiktok_account)
    await db.commit()
    
    # Schedule for 10:00 (BEFORE window)
    tomorrow_10h = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="tiktok",
        social_account_id=str(tiktok_account.id),
        scheduled_for=tomorrow_10h,
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "scheduled"
    assert response.scheduled_for.hour == 16  # TikTok window starts at 16:00
    assert "platform window" in response.reason.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS DE MIN_GAP_MINUTES (2 tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_scheduler_applies_instagram_60min_gap(db, sample_clip, sample_social_account):
    """Test that Instagram enforces 60-minute gap between posts."""
    # Create existing scheduled post at 20:00
    existing_time = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )
    
    existing_log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=existing_time,
        scheduled_by="test"
    )
    db.add(existing_log)
    await db.commit()
    
    # Try to schedule at 20:30 (only 30 min gap - should be pushed to 21:00)
    new_time = existing_time + timedelta(minutes=30)
    
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="instagram",
        social_account_id=str(sample_social_account.id),
        scheduled_for=new_time,
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "scheduled"
    # Should be pushed to existing + 60 minutes = 21:00
    expected_time = existing_time + timedelta(minutes=60)
    assert response.scheduled_for == expected_time
    assert "gap" in response.reason.lower()


@pytest.mark.asyncio
async def test_scheduler_applies_tiktok_30min_gap(db, sample_clip):
    """Test that TikTok enforces 30-minute gap between posts."""
    # Create TikTok account
    tiktok_account = SocialAccountModel(
        id=uuid4(),
        platform="tiktok",
        handle="@tiktokuser",
        external_id="tiktok_456",
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(tiktok_account)
    await db.commit()
    
    # Create existing scheduled post at 18:00
    existing_time = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=18, minute=0, second=0, microsecond=0
    )
    
    existing_log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="tiktok",
        social_account_id=tiktok_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=existing_time,
        scheduled_by="test"
    )
    db.add(existing_log)
    await db.commit()
    
    # Try to schedule at 18:15 (only 15 min gap - should be pushed to 18:30)
    new_time = existing_time + timedelta(minutes=15)
    
    request = ScheduleRequest(
        clip_id=str(sample_clip.id),
        platform="tiktok",
        social_account_id=str(tiktok_account.id),
        scheduled_for=new_time,
        scheduled_by="manual"
    )
    
    response = await schedule_publication(db, request)
    
    assert response.status == "scheduled"
    # Should be pushed to existing + 30 minutes = 18:30
    expected_time = existing_time + timedelta(minutes=30)
    assert response.scheduled_for == expected_time
    assert "gap" in response.reason.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS DE SCHEDULER_TICK (2 tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_scheduler_tick_moves_due_logs_to_pending(db, sample_clip, sample_social_account):
    """Test that scheduler_tick moves logs from scheduled → pending."""
    # Create 2 scheduled logs: 1 due now, 1 future
    now = datetime.utcnow()
    past_time = now - timedelta(minutes=5)  # Due 5 minutes ago
    future_time = now + timedelta(hours=2)  # Future
    
    due_log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=past_time,
        scheduled_by="test"
    )
    
    future_log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=future_time,
        scheduled_by="test"
    )
    
    db.add(due_log)
    db.add(future_log)
    await db.commit()
    await db.refresh(due_log)
    await db.refresh(future_log)
    
    due_log_id = str(due_log.id)
    future_log_id = str(future_log.id)
    
    # Execute scheduler tick
    moved, log_ids = await scheduler_tick(db, now, dry_run=False)
    
    assert moved == 1  # Only the due log
    assert due_log_id in log_ids
    assert future_log_id not in log_ids
    
    # Verify status changed
    await db.refresh(due_log)
    await db.refresh(future_log)
    
    assert due_log.status == "pending"
    assert future_log.status == "scheduled"  # Unchanged


@pytest.mark.asyncio
async def test_scheduler_tick_dry_run_doesnt_modify(db, sample_clip, sample_social_account):
    """Test that dry_run=True doesn't modify logs."""
    now = datetime.utcnow()
    past_time = now - timedelta(minutes=10)
    
    log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=past_time,
        scheduled_by="test"
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    # Dry run
    moved, log_ids = await scheduler_tick(db, now, dry_run=True)
    
    assert moved == 1
    assert str(log.id) in log_ids
    
    # Verify status NOT changed
    await db.refresh(log)
    assert log.status == "scheduled"  # Still scheduled


# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST DE ENDPOINT (1 test)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_get_scheduled_logs_for_clip(db, sample_clip, sample_social_account):
    """Test retrieving all scheduled logs for a clip."""
    # Create 3 logs: 2 scheduled, 1 immediate
    now = datetime.utcnow()
    
    scheduled_log_1 = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=now + timedelta(hours=1),
        scheduled_by="manual"
    )
    
    scheduled_log_2 = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="scheduled",
        schedule_type="scheduled",
        scheduled_for=now + timedelta(hours=3),
        scheduled_by="rule_engine"
    )
    
    immediate_log = PublishLogModel(
        clip_id=sample_clip.id,
        platform="instagram",
        social_account_id=sample_social_account.id,
        status="pending",
        schedule_type="immediate"
    )
    
    db.add(scheduled_log_1)
    db.add(scheduled_log_2)
    db.add(immediate_log)
    await db.commit()
    
    # Get scheduled logs
    logs = await get_scheduled_logs_for_clip(db, str(sample_clip.id))
    
    assert len(logs) == 2  # Only scheduled logs
    assert all(log.schedule_type == "scheduled" for log in logs)
    assert logs[0].scheduled_for < logs[1].scheduled_for  # Ordered by time
