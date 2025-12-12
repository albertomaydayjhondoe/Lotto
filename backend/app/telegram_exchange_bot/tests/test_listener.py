"""
Tests para MessageListener - Sprint 7A
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.telegram_exchange_bot.listener import (
    MessageListener,
    URLDetector,
    KeywordMatcher,
    MessageClassifier
)
from app.telegram_exchange_bot.models import Platform


class TestURLDetector:
    """Tests para URLDetector."""
    
    def test_extract_youtube_urls(self):
        """Extrae URLs de YouTube correctamente."""
        text = "Miren mi video https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        urls = URLDetector.extract_urls(text)
        
        assert Platform.YOUTUBE in urls
        assert len(urls[Platform.YOUTUBE]) == 1
        assert "dQw4w9WgXcQ" in urls[Platform.YOUTUBE][0]
    
    def test_extract_youtube_shorts(self):
        """Extrae YouTube Shorts."""
        text = "https://youtube.com/shorts/abc123XYZ"
        urls = URLDetector.extract_urls(text)
        
        assert Platform.YOUTUBE in urls
        assert "abc123XYZ" in urls[Platform.YOUTUBE][0]
    
    def test_extract_instagram_urls(self):
        """Extrae URLs de Instagram."""
        text = "Apoyen mi post https://instagram.com/p/ABC123def/"
        urls = URLDetector.extract_urls(text)
        
        assert Platform.INSTAGRAM in urls
        assert "ABC123def" in urls[Platform.INSTAGRAM][0]
    
    def test_extract_tiktok_urls(self):
        """Extrae URLs de TikTok."""
        text = "Mi tiktok https://www.tiktok.com/@user123/video/1234567890"
        urls = URLDetector.extract_urls(text)
        
        assert Platform.TIKTOK in urls
    
    def test_extract_multiple_platforms(self):
        """Extrae URLs de múltiples plataformas."""
        text = """
        YouTube: https://youtube.com/watch?v=abc123
        Instagram: https://instagram.com/p/def456/
        TikTok: https://tiktok.com/@user/video/789
        """
        urls = URLDetector.extract_urls(text)
        
        assert Platform.YOUTUBE in urls
        assert Platform.INSTAGRAM in urls
        assert Platform.TIKTOK in urls
    
    def test_has_any_url(self):
        """Verifica detección de URLs."""
        assert URLDetector.has_any_url("https://youtube.com/watch?v=abc")
        assert not URLDetector.has_any_url("Sin URLs aquí")


class TestKeywordMatcher:
    """Tests para KeywordMatcher."""
    
    def test_match_spanish_keywords(self):
        """Detecta keywords en español."""
        assert KeywordMatcher.match("like x like", "es")
        assert KeywordMatcher.match("sub por sub aquí", "es")
        assert KeywordMatcher.match("APOYO MUTUO", "es")
        assert not KeywordMatcher.match("video random", "es")
    
    def test_match_english_keywords(self):
        """Detecta keywords en inglés."""
        assert KeywordMatcher.match("like for like", "en")
        assert KeywordMatcher.match("sub 4 sub here", "en")
        assert KeywordMatcher.match("MUTUAL SUPPORT", "en")
        assert not KeywordMatcher.match("random video", "en")
    
    def test_match_portuguese_keywords(self):
        """Detecta keywords en portugués."""
        assert KeywordMatcher.match("troca de like", "pt")
        assert KeywordMatcher.match("sub por sub aqui", "pt")
        assert not KeywordMatcher.match("video aleatório", "pt")
    
    def test_match_any_language(self):
        """Detecta keywords en cualquier idioma."""
        assert KeywordMatcher.match("like x like")
        assert KeywordMatcher.match("like for like")
        assert KeywordMatcher.match("troca de like")
    
    def test_get_matched_keywords(self):
        """Retorna keywords encontradas."""
        text = "Hola, busco like x like y sub x sub"
        keywords = KeywordMatcher.get_matched_keywords(text)
        
        assert "like x like" in keywords
        assert "sub x sub" in keywords
        assert len(keywords) == 2


class TestMessageClassifier:
    """Tests para MessageClassifier."""
    
    def test_classify_opportunity_with_keywords_and_urls(self):
        """Clasifica como oportunidad si tiene keywords + URLs."""
        result = MessageClassifier.classify(
            text="like x like https://youtube.com/watch?v=abc",
            has_urls=True,
            has_keywords=True
        )
        assert result == "oportunidad"
    
    def test_classify_opportunity_with_only_keywords(self):
        """Clasifica como oportunidad con solo keywords."""
        result = MessageClassifier.classify(
            text="Busco apoyo mutuo",
            has_urls=False,
            has_keywords=True
        )
        assert result == "oportunidad"
    
    def test_classify_opportunity_with_only_urls(self):
        """Clasifica como oportunidad con solo URLs."""
        result = MessageClassifier.classify(
            text="https://youtube.com/watch?v=abc123",
            has_urls=True,
            has_keywords=False
        )
        assert result == "oportunidad"
    
    def test_classify_spam_long_message(self):
        """Detecta spam por longitud."""
        result = MessageClassifier.classify(
            text="a" * 1500,
            has_urls=False,
            has_keywords=False
        )
        assert result == "spam"
    
    def test_classify_spam_many_emojis(self):
        """Detecta spam por emojis."""
        result = MessageClassifier.classify(
            text="🔥" * 30 + "texto",
            has_urls=False,
            has_keywords=False
        )
        assert result == "spam"
    
    def test_classify_ruido(self):
        """Clasifica como ruido mensajes irrelevantes."""
        result = MessageClassifier.classify(
            text="Hola, qué tal?",
            has_urls=False,
            has_keywords=False
        )
        assert result == "ruido"


@pytest.mark.asyncio
class TestMessageListener:
    """Tests para MessageListener."""
    
    @pytest.fixture
    def listener(self):
        """Crea listener para tests."""
        return MessageListener(
            api_id=12345,
            api_hash="test_hash",
            phone="+1234567890"
        )
    
    def test_init(self, listener):
        """Verifica inicialización."""
        assert listener.phone == "+1234567890"
        assert len(listener.monitored_groups) == 0
        assert listener.stats["messages_processed"] == 0
    
    def test_detect_language_default(self, listener):
        """Detecta idioma por defecto."""
        lang = listener.detect_language(999)
        assert lang == "es"
    
    @pytest.mark.asyncio
    async def test_add_group(self, listener):
        """Añade grupo correctamente."""
        from app.telegram_exchange_bot.models import TelegramGroup
        
        group = TelegramGroup(
            id=1,
            telegram_id=12345,
            name="Test Group",
            language="es"
        )
        
        await listener.add_group(group)
        
        assert 12345 in listener.monitored_groups
        assert listener.monitored_groups[12345].name == "Test Group"
    
    def test_get_stats(self, listener):
        """Retorna estadísticas."""
        stats = listener.get_stats()
        
        assert "messages_processed" in stats
        assert "opportunities_detected" in stats
        assert "queue_size" in stats
