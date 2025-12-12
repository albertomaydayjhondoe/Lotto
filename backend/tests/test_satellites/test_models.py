"""
Tests for Satellite Engine Models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.satellites.models import (
    UploadRequest,
    UploadResponse,
    PlatformMetrics,
    SatelliteAccount,
    ScheduledPost,
)


def test_upload_request_valid():
    """Test: Valid upload request creation."""
    request = UploadRequest(
        video_path="/tmp/video.mp4",
        caption="Test caption",
        tags=["test", "viral"],
        platform="tiktok",
        account_id="acc_123"
    )
    
    assert request.video_path == "/tmp/video.mp4"
    assert request.platform == "tiktok"
    assert len(request.tags) == 2


def test_upload_request_invalid_platform():
    """Test: Invalid platform raises error."""
    with pytest.raises(ValidationError):
        UploadRequest(
            video_path="/tmp/video.mp4",
            caption="Test",
            platform="invalid_platform",
            account_id="acc_123"
        )


def test_upload_request_caption_too_long_tiktok():
    """Test: TikTok caption exceeding 2200 chars fails."""
    with pytest.raises(ValidationError):
        UploadRequest(
            video_path="/tmp/video.mp4",
            caption="x" * 2201,
            platform="tiktok",
            account_id="acc_123"
        )


def test_upload_request_tags_strip_hashtag():
    """Test: Hashtags are stripped from tags."""
    request = UploadRequest(
        video_path="/tmp/video.mp4",
        caption="Test",
        tags=["#viral", "#fyp", "trending"],
        platform="instagram",
        account_id="acc_123"
    )
    
    assert request.tags == ["viral", "fyp", "trending"]


def test_upload_response_success():
    """Test: Successful upload response."""
    response = UploadResponse(
        success=True,
        platform="tiktok",
        post_id="12345",
        post_url="https://tiktok.com/@user/video/12345",
        account_used="acc_123",
        upload_duration_ms=1500.0,
        cost_estimate=0.01
    )
    
    assert response.success
    assert response.post_id == "12345"
    assert response.cost_estimate == 0.01


def test_platform_metrics_valid():
    """Test: Valid platform metrics."""
    metrics = PlatformMetrics(
        post_id="post_123",
        platform="instagram",
        views=10000,
        likes=800,
        comments=50,
        shares=30,
        saves=120,
        engagement_rate=0.1,
        ctr=0.02,
        avg_watch_time_sec=12.5,
        completion_rate=0.6
    )
    
    assert metrics.views == 10000
    assert metrics.engagement_rate == 0.1


def test_platform_metrics_negative_values():
    """Test: Negative values in metrics fail."""
    with pytest.raises(ValidationError):
        PlatformMetrics(
            post_id="post_123",
            platform="youtube",
            views=-100,  # Invalid
            likes=50
        )


def test_satellite_account_valid():
    """Test: Valid satellite account creation."""
    account = SatelliteAccount(
        account_id="acc_001",
        platform="tiktok",
        username="test_user",
        daily_post_limit=5
    )
    
    assert account.account_id == "acc_001"
    assert account.is_active is True
    assert account.success_rate == 1.0


def test_satellite_account_daily_limit_bounds():
    """Test: Daily post limit has bounds."""
    with pytest.raises(ValidationError):
        SatelliteAccount(
            account_id="acc_001",
            platform="instagram",
            username="test_user",
            daily_post_limit=100  # Exceeds max of 50
        )


def test_scheduled_post_creation():
    """Test: Scheduled post creation."""
    request = UploadRequest(
        video_path="/tmp/video.mp4",
        caption="Test",
        platform="youtube",
        account_id="acc_123"
    )
    
    scheduled_post = ScheduledPost(
        schedule_id="sched_001",
        upload_request=request,
        scheduled_for=datetime.utcnow()
    )
    
    assert scheduled_post.status == "pending"
    assert scheduled_post.retry_count == 0
    assert scheduled_post.max_retries == 3
