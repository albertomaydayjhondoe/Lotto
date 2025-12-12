"""
Tests for Upload Scheduler
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.satellites.config import SatelliteConfig
from app.satellites.models import UploadRequest, SatelliteAccount
from app.satellites.scheduler import UploadScheduler


@pytest.fixture
def config():
    """Fixture: Config with dry_run enabled."""
    return SatelliteConfig(dry_run=True, max_retries=2)


@pytest.fixture
def scheduler(config):
    """Fixture: Upload scheduler."""
    return UploadScheduler(config)


@pytest.fixture
def sample_request():
    """Fixture: Sample upload request."""
    return UploadRequest(
        video_path="/tmp/test.mp4",
        caption="Test post",
        tags=["test"],
        platform="tiktok",
        account_id="acc_001"
    )


@pytest.fixture
def sample_account():
    """Fixture: Sample account."""
    return SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="test_user",
        posts_today=0
    )


@pytest.mark.asyncio
async def test_schedule_upload_immediate(scheduler, sample_request, sample_account):
    """Test: Schedule immediate upload."""
    scheduled = await scheduler.schedule_upload(
        sample_request,
        sample_account,
        scheduled_for=None  # Immediate
    )
    
    assert scheduled.status == "pending"
    assert scheduled.schedule_id is not None
    assert len(scheduler.scheduled_posts) == 1


@pytest.mark.asyncio
async def test_schedule_upload_future(scheduler, sample_request, sample_account):
    """Test: Schedule future upload."""
    future_time = datetime.utcnow() + timedelta(hours=2)
    
    scheduled = await scheduler.schedule_upload(
        sample_request,
        sample_account,
        scheduled_for=future_time
    )
    
    assert scheduled.scheduled_for == future_time
    assert scheduled.status == "pending"


@pytest.mark.asyncio
async def test_schedule_upload_past_fails(scheduler, sample_request, sample_account):
    """Test: Cannot schedule in the past."""
    past_time = datetime.utcnow() - timedelta(hours=1)
    
    with pytest.raises(ValueError, match="past"):
        await scheduler.schedule_upload(
            sample_request,
            sample_account,
            scheduled_for=past_time
        )


@pytest.mark.asyncio
async def test_duplicate_detection(scheduler, sample_request, sample_account):
    """Test: Duplicate content detection."""
    sample_request.content_id = "content_123"
    
    # First upload
    await scheduler.schedule_upload(sample_request, sample_account)
    
    # Simulate completion
    scheduler._add_to_history("content_123", "acc_001")
    
    # Second upload (duplicate)
    is_dup = scheduler._is_duplicate("content_123", "acc_001")
    
    assert is_dup is True


@pytest.mark.asyncio
async def test_get_scheduled_posts_filter(scheduler, sample_request, sample_account):
    """Test: Filter scheduled posts by status."""
    # Schedule 3 posts
    await scheduler.schedule_upload(sample_request, sample_account)
    await scheduler.schedule_upload(sample_request, sample_account)
    await scheduler.schedule_upload(sample_request, sample_account)
    
    # Mark one as completed
    scheduler.scheduled_posts[0].status = "completed"
    
    pending = scheduler.get_scheduled_posts(status="pending")
    completed = scheduler.get_scheduled_posts(status="completed")
    
    assert len(pending) == 2
    assert len(completed) == 1


@pytest.mark.asyncio
async def test_cancel_scheduled_post(scheduler, sample_request, sample_account):
    """Test: Cancel a pending post."""
    scheduled = await scheduler.schedule_upload(sample_request, sample_account)
    
    result = scheduler.cancel_scheduled_post(scheduled.schedule_id)
    
    assert result is True
    assert scheduled.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_completed_post_fails(scheduler, sample_request, sample_account):
    """Test: Cannot cancel completed post."""
    scheduled = await scheduler.schedule_upload(sample_request, sample_account)
    scheduled.status = "completed"
    
    result = scheduler.cancel_scheduled_post(scheduled.schedule_id)
    
    assert result is False


@pytest.mark.asyncio
async def test_execute_upload_success(scheduler, sample_request):
    """Test: Execute upload successfully."""
    scheduled = await scheduler.schedule_upload(
        sample_request,
        SatelliteAccount(
            account_id="acc_001",
            platform="tiktok",
            username="test_user",
            posts_today=0
        )
    )
    
    # Execute
    await scheduler._execute_upload(scheduled)
    
    assert scheduled.status == "completed"
    assert scheduled.upload_response is not None
    assert scheduled.upload_response.success is True


@pytest.mark.asyncio
async def test_max_concurrent_uploads(scheduler, sample_request, sample_account):
    """Test: Respects max concurrent uploads limit."""
    # Schedule multiple posts
    for _ in range(5):
        await scheduler.schedule_upload(sample_request, sample_account)
    
    # All should be pending initially
    pending = scheduler.get_scheduled_posts(status="pending")
    assert len(pending) == 5
    
    # Active uploads should not exceed limit
    assert len(scheduler.active_uploads) <= scheduler.config.max_concurrent_uploads
