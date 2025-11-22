"""
Tests for Dashboard Actions Module

Tests action executor and router functionality.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard_actions.executor import execute_action
from app.models.database import (
    VideoAsset,
    Clip,
    ClipVariant,
    PublishLogModel,
    Campaign,
    CampaignStatus,
    ClipStatus
)


@pytest.mark.asyncio
async def test_execute_unknown_action(async_session: AsyncSession):
    """Test executing unknown action type raises error."""
    with pytest.raises(ValueError, match="Unknown action type"):
        await execute_action(
            action_type="invalid_action",
            payload={},
            db=async_session
        )


@pytest.mark.asyncio
async def test_action_retry_failed(async_session: AsyncSession):
    """Test retry failed publications action."""
    # Create failed publications
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    failed_log1 = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="failed",
        requested_at=datetime.utcnow() - timedelta(hours=1)
    )
    failed_log2 = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="tiktok",
        status="failed",
        requested_at=datetime.utcnow() - timedelta(hours=2)
    )
    async_session.add_all([failed_log1, failed_log2])
    await async_session.commit()
    
    # Execute retry action
    result = await execute_action(
        action_type="retry",
        payload={},
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["retry_count"] == 2
    
    # Verify logs are now pending
    await async_session.refresh(failed_log1)
    await async_session.refresh(failed_log2)
    assert failed_log1.status == "pending"
    assert failed_log2.status == "pending"


@pytest.mark.asyncio
async def test_action_rebalance_queue(async_session: AsyncSession):
    """Test rebalance queue action."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # Create pending publications with same scheduled time
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    for i in range(5):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=clip.id,
            platform="instagram",
            status="pending",
            scheduled_for=scheduled_time,
            requested_at=datetime.utcnow()
        )
        async_session.add(log)
    
    await async_session.commit()
    
    # Execute rebalance action
    result = await execute_action(
        action_type="rebalance_queue",
        payload={},
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["rebalanced_count"] == 5


@pytest.mark.asyncio
async def test_action_promote_clip(async_session: AsyncSession):
    """Test promote clip to campaign action."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    campaign = Campaign(
        id=uuid4(),
        name="Test Campaign",
        status=CampaignStatus.ACTIVE
    )
    async_session.add(campaign)
    
    await async_session.commit()
    
    # Execute promote action
    result = await execute_action(
        action_type="promote",
        payload={
            "video_id": str(video.id),
            "campaign_id": str(campaign.id)
        },
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["clip_id"] == str(clip.id)
    assert result["data"]["campaign_id"] == str(campaign.id)
    
    # Verify clip is linked to campaign
    await async_session.refresh(clip)
    assert clip.campaign_id == campaign.id


@pytest.mark.asyncio
async def test_action_reschedule(async_session: AsyncSession):
    """Test reschedule publication action."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    old_time = datetime.utcnow() + timedelta(hours=1)
    log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="pending",
        scheduled_for=old_time,
        requested_at=datetime.utcnow()
    )
    async_session.add(log)
    await async_session.commit()
    
    # Execute reschedule action
    new_time = datetime.utcnow() + timedelta(hours=5)
    result = await execute_action(
        action_type="reschedule",
        payload={
            "log_id": str(log.id),
            "new_time": new_time
        },
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["log_id"] == str(log.id)
    
    # Verify log is rescheduled
    await async_session.refresh(log)
    # Compare with some tolerance for microseconds
    assert abs((log.scheduled_for - new_time).total_seconds()) < 1


@pytest.mark.asyncio
async def test_action_clear_failed(async_session: AsyncSession):
    """Test clear old failed publications action."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # Create old failed log (8 days ago)
    old_log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="failed",
        requested_at=datetime.utcnow() - timedelta(days=8)
    )
    
    # Create recent failed log (2 days ago)
    recent_log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="tiktok",
        status="failed",
        requested_at=datetime.utcnow() - timedelta(days=2)
    )
    
    async_session.add_all([old_log, recent_log])
    await async_session.commit()
    
    # Execute clear action (older than 7 days)
    result = await execute_action(
        action_type="clear_failed",
        payload={"older_than_days": 7},
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["deleted_count"] == 1  # Only old log deleted


@pytest.mark.asyncio
async def test_action_optimize_schedule(async_session: AsyncSession):
    """Test optimize schedule action."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # Create pending publications for specific platforms
    for platform in ["instagram", "tiktok"]:
        for i in range(3):
            log = PublishLogModel(
                id=uuid4(),
                clip_id=clip.id,
                platform=platform,
                status="pending",
                scheduled_for=datetime.utcnow() + timedelta(hours=1),
                requested_at=datetime.utcnow()
            )
            async_session.add(log)
    
    await async_session.commit()
    
    # Execute optimize action
    result = await execute_action(
        action_type="optimize_schedule",
        payload={"platforms": ["instagram", "tiktok"]},
        db=async_session
    )
    
    assert result["success"] is True
    assert result["data"]["optimized_count"] > 0
    assert set(result["data"]["platforms"]) == {"instagram", "tiktok"}


@pytest.mark.asyncio
async def test_action_force_publish_no_clip(async_session: AsyncSession):
    """Test force publish with non-existent clip raises error."""
    fake_clip_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        await execute_action(
            action_type="publish",
            payload={"clip_id": str(fake_clip_id)},
            db=async_session
        )


@pytest.mark.asyncio
async def test_action_reschedule_no_log(async_session: AsyncSession):
    """Test reschedule with non-existent log raises error."""
    fake_log_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        await execute_action(
            action_type="reschedule",
            payload={
                "log_id": str(fake_log_id),
                "new_time": datetime.utcnow()
            },
            db=async_session
        )


@pytest.mark.asyncio
async def test_action_result_structure(async_session: AsyncSession):
    """Test that action results have correct structure."""
    result = await execute_action(
        action_type="retry",
        payload={},
        db=async_session
    )
    
    # Verify result structure
    assert "success" in result
    assert "message" in result
    assert "data" in result
    assert "executed_at" in result
    assert isinstance(result["success"], bool)
    assert isinstance(result["message"], str)
    assert isinstance(result["data"], dict)
