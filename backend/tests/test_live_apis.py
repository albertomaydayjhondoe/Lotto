"""
Tests Sprint 7C - Live APIs
Tests para YouTube/Instagram/TikTok Live APIs.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.telegram_exchange_bot.platforms import (
    YouTubeLiveAPI,
    InstagramLiveAPI,
    TikTokLiveAPI,
    YouTubeVideoMetadata,
    InstagramPostMetadata,
    TikTokVideoMetadata
)
from app.telegram_exchange_bot.security import SecurityContext


@pytest.fixture
def mock_security_context():
    """Mock SecurityContext."""
    return SecurityContext(
        account_id="test_acc_001",
        vpn_active=True,
        proxy=Mock(host="proxy.test", port=8080),
        fingerprint="mock_fingerprint_abc123",
        rate_limit_respected=True
    )


class TestYouTubeLiveAPI:
    """Tests para YouTubeLiveAPI."""
    
    def test_extract_video_id_standard_url(self):
        """Test extracción de video ID desde URL estándar."""
        api = YouTubeLiveAPI()
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = api.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short_url(self):
        """Test extracción desde URL corta."""
        api = YouTubeLiveAPI()
        
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = api.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_mobile_url(self):
        """Test extracción desde URL móvil."""
        api = YouTubeLiveAPI()
        
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = api.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid_url(self):
        """Test URL inválida."""
        api = YouTubeLiveAPI()
        
        url = "https://example.com/invalid"
        video_id = api.extract_video_id(url)
        
        assert video_id is None
    
    @pytest.mark.asyncio
    async def test_get_video_metadata_simulation(self, mock_security_context):
        """Test obtención de metadata (simulado)."""
        api = YouTubeLiveAPI()
        
        url = "https://youtube.com/watch?v=test123"
        metadata = await api.get_video_metadata(url, mock_security_context)
        
        assert metadata is not None
        assert metadata.video_id == "test123"
        assert metadata.views > 0
        assert api.stats["metadata_fetched"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_like_simulation(self, mock_security_context):
        """Test ejecución de like (simulado)."""
        api = YouTubeLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            result = await api.execute_like(
                video_url="https://youtube.com/watch?v=test",
                username="test_user",
                security_context=mock_security_context
            )
        
        assert result["success"] is True
        assert result["mode"] == "simulation"
        assert api.stats["likes_executed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_comment_with_text(self, mock_security_context):
        """Test ejecución de comment."""
        api = YouTubeLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            result = await api.execute_comment(
                video_url="https://youtube.com/watch?v=test",
                comment_text="Great video!",
                username="test_user",
                security_context=mock_security_context
            )
        
        assert result["success"] is True
        assert result["comment_text"] == "Great video!"
        assert api.stats["comments_executed"] == 1


class TestInstagramLiveAPI:
    """Tests para InstagramLiveAPI."""
    
    @pytest.mark.asyncio
    async def test_login_simulation(self, mock_security_context):
        """Test login (simulado)."""
        api = InstagramLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            success = await api.login(
                account_id="test_acc",
                username="test_user",
                password="test_pass",
                security_context=mock_security_context
            )
        
        # En modo simulación, login siempre exitoso
        assert success is True
        assert api.stats["sessions_created"] == 1
    
    @pytest.mark.asyncio
    async def test_get_post_metadata_simulation(self, mock_security_context):
        """Test obtención de metadata."""
        api = InstagramLiveAPI()
        
        # Login primero
        with patch('asyncio.sleep', new=AsyncMock()):
            await api.login(
                account_id="test_acc",
                username="test_user",
                password="test_pass",
                security_context=mock_security_context
            )
        
        metadata = await api.get_post_metadata(
            post_url="https://instagram.com/p/test123",
            account_id="test_acc"
        )
        
        assert metadata is not None
        assert metadata.shortcode == "test123"
        assert metadata.likes > 0
    
    @pytest.mark.asyncio
    async def test_execute_like_without_login(self, mock_security_context):
        """Test like sin login previo."""
        api = InstagramLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            result = await api.execute_like(
                post_url="https://instagram.com/p/test123",
                account_id="test_acc",
                security_context=mock_security_context
            )
        
        # Debe fallar por falta de sesión
        assert result["success"] is False
        assert "not logged in" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_save_with_login(self, mock_security_context):
        """Test save con login."""
        api = InstagramLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            # Login
            await api.login(
                account_id="test_acc",
                username="test_user",
                password="test_pass",
                security_context=mock_security_context
            )
            
            # Save
            result = await api.execute_save(
                post_url="https://instagram.com/p/test123",
                account_id="test_acc",
                security_context=mock_security_context
            )
        
        assert result["success"] is True
        assert api.stats["saves_executed"] == 1


class TestTikTokLiveAPI:
    """Tests para TikTokLiveAPI."""
    
    def test_extract_video_id_standard_url(self):
        """Test extracción de video ID."""
        api = TikTokLiveAPI()
        
        url = "https://www.tiktok.com/@user123/video/7234567890123456789"
        video_id = api.extract_video_id(url)
        
        assert video_id == "7234567890123456789"
    
    def test_extract_video_id_short_url(self):
        """Test extracción desde URL corta."""
        api = TikTokLiveAPI()
        
        # Mock de requests.head para simular redirección
        with patch('requests.head') as mock_head:
            mock_head.return_value.url = "https://www.tiktok.com/@user/video/123456"
            
            url = "https://vm.tiktok.com/ZMabcdef"
            video_id = api.extract_video_id(url)
            
            assert video_id == "123456"
    
    @pytest.mark.asyncio
    async def test_get_video_metadata_simulation(self, mock_security_context):
        """Test obtención de metadata."""
        api = TikTokLiveAPI()
        
        url = "https://tiktok.com/@user/video/123456"
        metadata = await api.get_video_metadata(url, mock_security_context)
        
        assert metadata is not None
        assert metadata.video_id == "123456"
        assert metadata.views > 0
        assert api.stats["metadata_fetched"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_like_circuit_breaker_open(self, mock_security_context):
        """Test like con circuit breaker abierto."""
        api = TikTokLiveAPI()
        
        # Activar circuit breaker
        api.shadowban_signals["failed_requests"] = 5
        
        with patch('asyncio.sleep', new=AsyncMock()):
            result = await api.execute_like(
                video_url="https://tiktok.com/@user/video/123",
                username="test_user",
                security_context=mock_security_context
            )
        
        assert result["success"] is False
        assert "circuit breaker" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_comment_normal(self, mock_security_context):
        """Test comment normal."""
        api = TikTokLiveAPI()
        
        with patch('asyncio.sleep', new=AsyncMock()):
            result = await api.execute_comment(
                video_url="https://tiktok.com/@user/video/123",
                comment_text="Amazing!",
                username="test_user",
                security_context=mock_security_context
            )
        
        assert result["success"] is True
        assert result["comment_text"] == "Amazing!"
        assert api.stats["comments_executed"] == 1
    
    @pytest.mark.asyncio
    async def test_shadowban_detection(self, mock_security_context):
        """Test detección de shadowban."""
        api = TikTokLiveAPI()
        
        # Simular múltiples fallos
        for _ in range(5):
            api._record_error("Rate limit exceeded")
        
        assert api._is_shadowbanned() is True
        assert api.stats["shadowban_detected"] == 1
    
    def test_reset_circuit_breaker(self):
        """Test reset de circuit breaker."""
        api = TikTokLiveAPI()
        
        # Activar circuit breaker
        api.shadowban_signals["failed_requests"] = 5
        assert api._is_shadowbanned() is True
        
        # Reset
        api.reset_circuit_breaker()
        
        assert api._is_shadowbanned() is False
        assert api.shadowban_signals["failed_requests"] == 0


@pytest.mark.asyncio
async def test_integration_all_platforms(mock_security_context):
    """Test de integración: todas las plataformas."""
    
    # YouTube
    yt_api = YouTubeLiveAPI()
    with patch('asyncio.sleep', new=AsyncMock()):
        yt_result = await yt_api.execute_like(
            video_url="https://youtube.com/watch?v=test",
            username="test_user",
            security_context=mock_security_context
        )
    assert yt_result["success"] is True
    
    # Instagram
    ig_api = InstagramLiveAPI()
    with patch('asyncio.sleep', new=AsyncMock()):
        await ig_api.login(
            account_id="test_acc",
            username="test_user",
            password="test_pass",
            security_context=mock_security_context
        )
        ig_result = await ig_api.execute_like(
            post_url="https://instagram.com/p/test",
            account_id="test_acc",
            security_context=mock_security_context
        )
    assert ig_result["success"] is True
    
    # TikTok
    tt_api = TikTokLiveAPI()
    with patch('asyncio.sleep', new=AsyncMock()):
        tt_result = await tt_api.execute_like(
            video_url="https://tiktok.com/@user/video/123",
            username="test_user",
            security_context=mock_security_context
        )
    assert tt_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
