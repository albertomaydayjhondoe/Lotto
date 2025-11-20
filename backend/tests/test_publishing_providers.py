"""
Tests for Publishing Integrations (Step 3).

These tests validate provider clients, validation logic, and API endpoints
WITHOUT making real API calls to external services.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.publishing_integrations import (
    get_provider_client,
    InstagramPublishingClient,
    TikTokPublishingClient,
    YouTubePublishingClient,
    PublishingAuthError,
    PublishingUploadError,
    PublishingPostError
)


@pytest_asyncio.fixture
async def client():
    """Provide an async HTTP client for API tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Test 1: List providers endpoint
@pytest.mark.asyncio
async def test_list_providers(client):
    """Test GET /publishing/providers endpoint."""
    response = await client.get("/publishing/providers")
    
    assert response.status_code == 200
    providers = response.json()
    
    # Verify all expected providers are present
    assert isinstance(providers, list)
    assert "instagram" in providers
    assert "tiktok" in providers
    assert "youtube" in providers
    assert len(providers) == 3


# Test 2: Get provider details
@pytest.mark.asyncio
async def test_get_provider_details(client):
    """Test GET /publishing/providers/{platform} endpoint."""
    # Test Instagram
    response = await client.get("/publishing/providers/instagram")
    assert response.status_code == 200
    
    data = response.json()
    assert data["platform"] == "instagram"
    assert data["authenticated"] == False  # No credentials provided
    assert "features" in data
    assert "video_upload" in data["features"]
    assert "limits" in data
    assert data["limits"]["max_caption_length"] == 2200
    assert data["limits"]["max_hashtags"] == 30
    assert data["api_version"] == "v18.0"
    assert "documentation" in data
    
    # Test TikTok
    response = await client.get("/publishing/providers/tiktok")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "tiktok"
    assert data["limits"]["max_caption_length"] == 150
    
    # Test YouTube
    response = await client.get("/publishing/providers/youtube")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "youtube"
    assert data["limits"]["max_title_length"] == 100
    assert data["limits"]["max_description_length"] == 5000
    
    # Test invalid provider
    response = await client.get("/publishing/providers/invalid")
    assert response.status_code == 404


# Test 3: Validate Instagram payload
@pytest.mark.asyncio
async def test_validate_payload_instagram(client):
    """Test POST /publishing/validate for Instagram."""
    # Valid caption
    response = await client.post("/publishing/validate", json={
        "platform": "instagram",
        "params": {
            "caption": "Great video! #test #instagram"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "instagram"
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    
    # Caption too long
    long_caption = "a" * 2201
    response = await client.post("/publishing/validate", json={
        "platform": "instagram",
        "params": {
            "caption": long_caption
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert "Caption too long" in data["errors"][0]
    
    # Too many hashtags
    hashtags = " ".join([f"#tag{i}" for i in range(31)])
    response = await client.post("/publishing/validate", json={
        "platform": "instagram",
        "params": {
            "caption": f"Post with many tags {hashtags}"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("hashtags" in error.lower() for error in data["errors"])


# Test 4: Validate TikTok payload
@pytest.mark.asyncio
async def test_validate_payload_tiktok(client):
    """Test POST /publishing/validate for TikTok."""
    # Valid title
    response = await client.post("/publishing/validate", json={
        "platform": "tiktok",
        "params": {
            "title": "Short TikTok video"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "tiktok"
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    
    # Title too long
    long_title = "a" * 151
    response = await client.post("/publishing/validate", json={
        "platform": "tiktok",
        "params": {
            "title": long_title
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Title too long" in data["errors"][0]
    
    # Invalid privacy level
    response = await client.post("/publishing/validate", json={
        "platform": "tiktok",
        "params": {
            "title": "Valid title",
            "privacy_level": "INVALID_LEVEL"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("privacy_level" in error for error in data["errors"])
    
    # Valid privacy level
    for privacy in ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"]:
        response = await client.post("/publishing/validate", json={
            "platform": "tiktok",
            "params": {
                "title": "Valid title",
                "privacy_level": privacy
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


# Test 5: Validate YouTube payload
@pytest.mark.asyncio
async def test_validate_payload_youtube(client):
    """Test POST /publishing/validate for YouTube."""
    # Valid parameters
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "title": "My YouTube Video",
            "description": "This is a great video about testing",
            "tags": ["test", "youtube", "video"],
            "privacy_status": "public"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "youtube"
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    
    # Missing title
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "description": "Description without title"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("title" in error.lower() for error in data["errors"])
    
    # Title too long
    long_title = "a" * 101
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "title": long_title,
            "description": "Valid description"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Title too long" in data["errors"][0]
    
    # Description too long
    long_description = "a" * 5001
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "title": "Valid title",
            "description": long_description
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Description too long" in data["errors"][0]
    
    # Tag too long
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "title": "Valid title",
            "description": "Valid description",
            "tags": ["valid", "a" * 31]  # Second tag too long
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("tag" in error.lower() for error in data["errors"])
    
    # Invalid privacy status
    response = await client.post("/publishing/validate", json={
        "platform": "youtube",
        "params": {
            "title": "Valid title",
            "privacy_status": "invalid"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("privacy_status" in error for error in data["errors"])


# Test 6: Factory function
@pytest.mark.asyncio
async def test_get_provider_client_factory():
    """Test get_provider_client factory function."""
    # Valid platforms
    ig_client = get_provider_client("instagram")
    assert isinstance(ig_client, InstagramPublishingClient)
    assert ig_client.platform_name == "instagram"
    
    tt_client = get_provider_client("tiktok")
    assert isinstance(tt_client, TikTokPublishingClient)
    assert tt_client.platform_name == "tiktok"
    
    yt_client = get_provider_client("youtube")
    assert isinstance(yt_client, YouTubePublishingClient)
    assert yt_client.platform_name == "youtube"
    
    # Invalid platform
    with pytest.raises(ValueError) as exc_info:
        get_provider_client("invalid_platform")
    assert "not supported" in str(exc_info.value).lower()


# Test 7: Client capabilities
@pytest.mark.asyncio
async def test_client_capabilities():
    """Test client get_capabilities method."""
    ig_client = InstagramPublishingClient()
    capabilities = ig_client.get_capabilities()
    
    assert capabilities["platform"] == "instagram"
    assert capabilities["authenticated"] == False
    assert "video_upload" in capabilities["features"]
    assert capabilities["limits"]["max_caption_length"] == 2200
    assert "documentation" in capabilities


# Test 8: Client authentication (stub mode)
@pytest.mark.asyncio
async def test_client_authentication_stub():
    """Test client authentication in stub mode (no credentials)."""
    # Instagram
    ig_client = InstagramPublishingClient()
    assert ig_client.is_authenticated == False
    
    result = await ig_client.authenticate()
    assert result is True
    assert ig_client.is_authenticated is True
    
    # TikTok
    tt_client = TikTokPublishingClient()
    result = await tt_client.authenticate()
    assert result is True
    
    # YouTube
    yt_client = YouTubePublishingClient()
    result = await yt_client.authenticate()
    assert result is True


# Test 9: Client validation methods
@pytest.mark.asyncio
async def test_client_validation_methods():
    """Test client validate_post_params methods directly."""
    # Instagram validation
    ig_client = InstagramPublishingClient()
    
    valid_result = ig_client.validate_post_params(caption="Short caption")
    assert valid_result["valid"] is True
    
    invalid_result = ig_client.validate_post_params(caption="a" * 2201)
    assert invalid_result["valid"] is False
    assert len(invalid_result["errors"]) > 0
    
    # TikTok validation
    tt_client = TikTokPublishingClient()
    
    valid_result = tt_client.validate_post_params(title="Short title")
    assert valid_result["valid"] is True
    
    invalid_result = tt_client.validate_post_params(title="a" * 151)
    assert invalid_result["valid"] is False
    
    # YouTube validation
    yt_client = YouTubePublishingClient()
    
    valid_result = yt_client.validate_post_params(
        title="Valid title",
        description="Valid description"
    )
    assert valid_result["valid"] is True
    
    invalid_result = yt_client.validate_post_params(description="Only description")
    assert invalid_result["valid"] is False
    assert any("title" in error.lower() for error in invalid_result["errors"])
