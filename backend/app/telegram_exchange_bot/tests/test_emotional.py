"""
Tests para EmotionalMessageGenerator - Sprint 7A
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from app.telegram_exchange_bot.emotional import (
    EmotionalMessageGenerator,
    MessageType
)
from app.telegram_exchange_bot.models import OurContent, Platform, PriorityLevel


@pytest.fixture
def message_generator():
    """Crea generador sin Gemini (solo templates)."""
    return EmotionalMessageGenerator(
        use_gemini=False  # Deshabilitar Gemini para tests
    )


@pytest.fixture
def sample_content():
    """Contenido de prueba."""
    return OurContent(
        id=1,
        url="https://youtube.com/watch?v=test123",
        platform=Platform.YOUTUBE,
        title="Test Video",
        priority=PriorityLevel.HIGH
    )


class TestEmotionalMessageGenerator:
    """Tests para EmotionalMessageGenerator."""
    
    def test_init(self, message_generator):
        """Verifica inicialización."""
        assert message_generator.use_gemini is False
        assert len(message_generator.templates) > 0
        assert "es" in message_generator.templates
        assert "en" in message_generator.templates
        assert "pt" in message_generator.templates
    
    def test_detect_language_spanish(self, message_generator):
        """Detecta español correctamente."""
        text = "Hola, cómo estás? Busco apoyo mutuo"
        lang = message_generator.detect_language(text)
        assert lang == "es"
    
    def test_detect_language_english(self, message_generator):
        """Detecta inglés correctamente."""
        text = "Hello, how are you? Looking for mutual support"
        lang = message_generator.detect_language(text)
        assert lang == "en"
    
    def test_detect_language_portuguese(self, message_generator):
        """Detecta portugués correctamente."""
        text = "Olá, como você está? Procurando apoio mútuo"
        lang = message_generator.detect_language(text)
        assert lang == "pt"
    
    def test_detect_language_default(self, message_generator):
        """Usa español como default."""
        text = "12345 @#$%"
        lang = message_generator.detect_language(text, default="es")
        assert lang == "es"
    
    @pytest.mark.asyncio
    async def test_generate_announcement_spanish(
        self,
        message_generator,
        sample_content
    ):
        """Genera anuncio en español."""
        message = await message_generator.generate_announcement(
            content=sample_content,
            group_name="Test Group",
            language="es"
        )
        
        assert message is not None
        assert len(message) > 0
        assert sample_content.url in message
    
    @pytest.mark.asyncio
    async def test_generate_announcement_english(
        self,
        message_generator,
        sample_content
    ):
        """Genera anuncio en inglés."""
        message = await message_generator.generate_announcement(
            content=sample_content,
            group_name="Test Group",
            language="en"
        )
        
        assert message is not None
        assert sample_content.url in message
    
    @pytest.mark.asyncio
    async def test_generate_dm_intro(
        self,
        message_generator,
        sample_content
    ):
        """Genera mensaje DM intro."""
        message = await message_generator.generate_dm_intro(
            content=sample_content,
            group_name="Test Group",
            user_message="like x like",
            language="es"
        )
        
        assert message is not None
        assert sample_content.url in message
        assert "Test Group" in message
    
    @pytest.mark.asyncio
    async def test_generate_comment_fallback(
        self,
        message_generator
    ):
        """Genera comentario con fallback."""
        comment = await message_generator.generate_comment(
            target_content="Video de música urbana",
            platform=Platform.YOUTUBE,
            language="es"
        )
        
        assert comment is not None
        assert len(comment) > 0
        # Debe contener emoji
        assert any(ord(c) > 0x1F000 for c in comment)
    
    @pytest.mark.asyncio
    async def test_defend_fan_role(self, message_generator):
        """Genera respuesta de defensa."""
        response = await message_generator.defend_fan_role(language="es")
        
        assert response is not None
        assert len(response) > 0
    
    def test_generate_from_template_announcement(
        self,
        message_generator
    ):
        """Genera desde template announcement."""
        message = message_generator._generate_from_template(
            MessageType.ANNOUNCEMENT,
            "es",
            {"link": "https://youtube.com/test"}
        )
        
        assert message is not None
        assert "https://youtube.com/test" in message
    
    def test_generate_from_template_dm_intro(
        self,
        message_generator
    ):
        """Genera desde template DM intro."""
        message = message_generator._generate_from_template(
            MessageType.DM_INTRO,
            "en",
            {
                "link": "https://youtube.com/test",
                "group_name": "Music Exchange"
            }
        )
        
        assert message is not None
        assert "https://youtube.com/test" in message
        assert "Music Exchange" in message
    
    def test_templates_loaded(self, message_generator):
        """Verifica que templates se cargaron."""
        es_templates = message_generator.templates.get("es")
        
        assert es_templates is not None
        assert "announcement_variants" in es_templates
        assert "dm_intro_variants" in es_templates
        assert "dm_followup" in es_templates
        assert "dm_thanks" in es_templates
        assert "defense_role" in es_templates
        
        # Verificar que hay variantes
        assert len(es_templates["announcement_variants"]) > 0
        assert len(es_templates["dm_intro_variants"]) > 0
    
    def test_template_variation(self, message_generator):
        """Verifica variación en templates."""
        # Generar múltiples mensajes
        messages = []
        for _ in range(10):
            msg = message_generator._generate_from_template(
                MessageType.ANNOUNCEMENT,
                "es",
                {"link": "https://test.com"}
            )
            messages.append(msg)
        
        # Debe haber variación (no todos iguales)
        unique_messages = set(messages)
        assert len(unique_messages) > 1
