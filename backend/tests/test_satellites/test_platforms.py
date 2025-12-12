"""
Tests for Platform Clients
"""

import pytest
from datetime import datetime

from app.satellites.config import SatelliteConfig
from app.satellites.models import UploadRequest, SatelliteAccount
from app.satellites.platforms import (
    TikTokClient,
    InstagramClient,
    YouTubeClient,
)


@pytest.fixture
def config():
    """Fixture: Default config."""
    return SatelliteConfig(dry_run=True)


@pytest.fixture
def sample_account():
    """Fixture: Sample satellite account."""
    return SatelliteAccount(
        account_id="test_acc_001",
        platform="tiktok",
        username="test_user",
        daily_post_limit=5,
        posts_today=0
    )


@pytest.fixture
def sample_upload_request():
    """Fixture: Sample upload request."""
    return UploadRequest(
        video_path="/tmp/test_video.mp4",
        caption="Test caption #viral",
        tags=["test", "viral"],
        platform="tiktok",
        account_id="test_acc_001"
    )


@pytest.mark.asyncio
async def test_tiktok_client_upload_success(config, sample_account, sample_upload_request):
    """Test: TikTok client upload success."""
    client = TikTokClient(config)
    
    response = await client.upload_short(sample_upload_request, sample_account)
    
    assert response.success is True
    assert response.platform == "tiktok"
    assert response.post_id is not None
    assert response.upload_duration_ms > 0


@pytest.mark.asyncio
async def test_tiktok_client_daily_limit_check(config, sample_account, sample_upload_request):
    """Test: TikTok client respects daily limit."""
    client = TikTokClient(config)
    
    # Set account at limit
    sample_account.posts_today = sample_account.daily_post_limit
    
    response = await client.upload_short(sample_upload_request, sample_account)
    
    assert response.success is False
    assert "limit" in response.error_message.lower()


@pytest.mark.asyncio
async def test_tiktok_client_get_metrics(config, sample_account):
    """Test: TikTok client get metrics (STUB)."""
    client = TikTokClient(config)
    
    metrics = await client.get_metrics("post_123", sample_account)
    
    assert metrics.post_id == "post_123"
    assert metrics.platform == "tiktok"
    assert metrics.views > 0


@pytest.mark.asyncio
async def test_tiktok_client_delete_post(config, sample_account):
    """Test: TikTok client delete post (STUB)."""
    client = TikTokClient(config)
    
    result = await client.delete_post("post_123", sample_account)
    
    assert result is True


@pytest.mark.asyncio
async def test_tiktok_client_validate_account(config, sample_account):
    """Test: TikTok client validate account (STUB)."""
    client = TikTokClient(config)
    
    is_valid = await client.validate_account(sample_account)
    
    assert is_valid is True


@pytest.mark.asyncio
async def test_instagram_client_upload_success(config, sample_upload_request):
    """Test: Instagram client upload success."""
    # Update request for Instagram
    sample_upload_request.platform = "instagram"
    
    account = SatelliteAccount(
        account_id="test_acc_002",
        platform="instagram",
        username="test_ig_user",
        daily_post_limit=5,
        posts_today=0
    )
    
    client = InstagramClient(config)
    response = await client.upload_short(sample_upload_request, account)
    
    assert response.success is True
    assert response.platform == "instagram"


@pytest.mark.asyncio
async def test_instagram_client_wrong_platform_error(config, sample_upload_request):
    """Test: Instagram client rejects wrong platform."""
    # Keep platform as tiktok
    account = SatelliteAccount(
        account_id="test_acc_002",
        platform="instagram",
        username="test_ig_user"
    )
    
    client = InstagramClient(config)
    
    with pytest.raises(ValueError, match="Invalid platform"):
        await client.upload_short(sample_upload_request, account)


@pytest.mark.asyncio
async def test_youtube_client_upload_success(config):
    """Test: YouTube client upload success."""
    request = UploadRequest(
        video_path="/tmp/test_video.mp4",
        caption="Test YouTube short",
        tags=["test", "shorts"],
        platform="youtube",
        account_id="test_acc_003"
    )
    
    account = SatelliteAccount(
        account_id="test_acc_003",
        platform="youtube",
        username="test_yt_channel",
        daily_post_limit=5,
        posts_today=0
    )
    
    client = YouTubeClient(config)
    response = await client.upload_short(request, account)
    
    assert response.success is True
    assert response.platform == "youtube"
    assert "youtube.com/shorts" in response.post_url


@pytest.mark.asyncio
async def test_youtube_client_get_metrics(config):
    """Test: YouTube client get metrics (STUB)."""
    account = SatelliteAccount(
        account_id="test_acc_003",
        platform="youtube",
        username="test_yt_channel"
    )
    
    client = YouTubeClient(config)
    metrics = await client.get_metrics("yt_post_123", account)
    
    assert metrics.platform == "youtube"
    assert metrics.views > 0
    # YouTube doesn't expose shares/saves
    assert metrics.shares == 0
    assert metrics.saves == 0


@pytest.mark.asyncio
async def test_cost_estimation(config, sample_account, sample_upload_request):
    """Test: Cost estimation for uploads."""
    client = TikTokClient(config)
    
    response = await client.upload_short(sample_upload_request, sample_account)
    
    assert response.cost_estimate > 0
    assert response.cost_estimate <= config.max_cost_per_upload
