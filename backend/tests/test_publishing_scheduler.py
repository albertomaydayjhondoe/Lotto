"""
Tests for Publishing Scheduler.

Tests scheduling logic, platform windows, minimum gaps, and scheduler tick.
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


# Test basic scheduling
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
