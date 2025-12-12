"""
Tests para DMNegotiationFlow - Sprint 7A
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.telegram_exchange_bot.dm_flow import (
    DMNegotiationFlow,
    ConversationState,
    AcceptanceSignal,
    RejectionSignal,
    ResponseAnalyzer,
    InteractionRequestBuilder
)
from app.telegram_exchange_bot.models import (
    Platform,
    InteractionType,
    ExchangeMessage,
    OurContent,
    PriorityLevel
)


class TestResponseAnalyzer:
    """Tests para ResponseAnalyzer."""
    
    def test_detect_acceptance_explicit_spanish(self):
        """Detecta aceptación explícita en español."""
        assert ResponseAnalyzer.detect_acceptance("sí, dale", "es") == AcceptanceSignal.EXPLICIT_YES
        assert ResponseAnalyzer.detect_acceptance("ok perfecto", "es") == AcceptanceSignal.EXPLICIT_YES
        assert ResponseAnalyzer.detect_acceptance("bueno, va", "es") == AcceptanceSignal.EXPLICIT_YES
    
    def test_detect_acceptance_explicit_english(self):
        """Detecta aceptación explícita en inglés."""
        assert ResponseAnalyzer.detect_acceptance("yes sure", "en") == AcceptanceSignal.EXPLICIT_YES
        assert ResponseAnalyzer.detect_acceptance("ok cool", "en") == AcceptanceSignal.EXPLICIT_YES
    
    def test_detect_acceptance_link(self):
        """Detecta cuando usuario pasa link."""
        text = "Aquí está https://youtube.com/watch?v=abc123"
        assert ResponseAnalyzer.detect_acceptance(text, "es") == AcceptanceSignal.SENT_LINK
    
    def test_detect_acceptance_confirmation(self):
        """Detecta confirmación."""
        assert ResponseAnalyzer.detect_acceptance("listo, ya está", "es") == AcceptanceSignal.CONFIRMATION
        assert ResponseAnalyzer.detect_acceptance("done!", "en") == AcceptanceSignal.CONFIRMATION
    
    def test_detect_acceptance_question(self):
        """Detecta preguntas (interés)."""
        assert ResponseAnalyzer.detect_acceptance("¿cómo funciona?", "es") == AcceptanceSignal.QUESTION
        assert ResponseAnalyzer.detect_acceptance("what do I need to do?", "en") == AcceptanceSignal.QUESTION
    
    def test_detect_rejection_explicit_spanish(self):
        """Detecta rechazo explícito en español."""
        assert ResponseAnalyzer.detect_rejection("no gracias", "es") == RejectionSignal.EXPLICIT_NO
        assert ResponseAnalyzer.detect_rejection("nop, paso", "es") == RejectionSignal.EXPLICIT_NO
    
    def test_detect_rejection_explicit_english(self):
        """Detecta rechazo explícito en inglés."""
        assert ResponseAnalyzer.detect_rejection("no thanks", "en") == RejectionSignal.EXPLICIT_NO
        assert ResponseAnalyzer.detect_rejection("nope", "en") == RejectionSignal.EXPLICIT_NO
    
    def test_detect_rejection_insult(self):
        """Detecta insultos."""
        assert ResponseAnalyzer.detect_rejection("fuck off", "en") == RejectionSignal.INSULT
        assert ResponseAnalyzer.detect_rejection("idiota spam", "es") == RejectionSignal.INSULT
    
    def test_extract_url(self):
        """Extrae URL de texto."""
        text = "Aquí mi video https://youtube.com/watch?v=abc123 míralo"
        url = ResponseAnalyzer.extract_url(text)
        assert url == "https://youtube.com/watch?v=abc123"
    
    def test_extract_url_none(self):
        """Retorna None si no hay URL."""
        assert ResponseAnalyzer.extract_url("Sin URLs aquí") is None


class TestInteractionRequestBuilder:
    """Tests para InteractionRequestBuilder."""
    
    def test_build_request_youtube(self):
        """Construye solicitud para YouTube."""
        types, text = InteractionRequestBuilder.build_request(Platform.YOUTUBE, "es")
        
        assert InteractionType.YOUTUBE_LIKE in types
        assert InteractionType.YOUTUBE_COMMENT in types
        assert InteractionType.YOUTUBE_SUBSCRIBE in types
        assert "like" in text.lower()
        assert "comment" in text.lower() or "coment" in text.lower()
    
    def test_build_request_instagram(self):
        """Construye solicitud para Instagram."""
        types, text = InteractionRequestBuilder.build_request(Platform.INSTAGRAM, "en")
        
        assert InteractionType.INSTAGRAM_LIKE in types
        assert InteractionType.INSTAGRAM_COMMENT in types
        assert InteractionType.INSTAGRAM_SAVE in types
        assert "save" in text.lower()
    
    def test_build_request_tiktok(self):
        """Construye solicitud para TikTok."""
        types, text = InteractionRequestBuilder.build_request(Platform.TIKTOK, "pt")
        
        assert InteractionType.TIKTOK_LIKE in types
        assert InteractionType.TIKTOK_COMMENT in types
        assert "like" in text.lower()
    
    def test_build_request_multilanguage(self):
        """Soporta múltiples idiomas."""
        _, text_es = InteractionRequestBuilder.build_request(Platform.YOUTUBE, "es")
        _, text_en = InteractionRequestBuilder.build_request(Platform.YOUTUBE, "en")
        _, text_pt = InteractionRequestBuilder.build_request(Platform.YOUTUBE, "pt")
        
        assert text_es != text_en
        assert text_en != text_pt


@pytest.mark.asyncio
class TestDMNegotiationFlow:
    """Tests para DMNegotiationFlow."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock de TelegramClient."""
        client = Mock()
        client.send_message = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_generator(self):
        """Mock de EmotionalMessageGenerator."""
        generator = Mock()
        generator.generate_dm_intro = AsyncMock(return_value="Hola! Mensaje intro")
        generator.generate_followup = AsyncMock(return_value="Followup")
        generator._generate_from_template = Mock(return_value="Template message")
        return generator
    
    @pytest.fixture
    def dm_flow(self, mock_client, mock_generator):
        """Crea DMNegotiationFlow para tests."""
        return DMNegotiationFlow(
            client=mock_client,
            message_generator=mock_generator,
            max_concurrent_conversations=10
        )
    
    @pytest.fixture
    def sample_exchange_message(self):
        """Mensaje de intercambio de prueba."""
        return ExchangeMessage(
            id=1,
            telegram_message_id=12345,
            group_id=999,
            group_name="Test Group",
            user_id=777,
            username="testuser",
            user_first_name="Test",
            message_text="like x like https://youtube.com/test",
            detected_platforms=[Platform.YOUTUBE],
            detected_urls={"youtube": ["https://youtube.com/test"]},
            keywords_matched=["like x like"],
            language="es",
            detected_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_content(self):
        """Contenido de prueba."""
        return OurContent(
            id=1,
            url="https://youtube.com/watch?v=our_video",
            platform=Platform.YOUTUBE,
            title="Our Video",
            priority=PriorityLevel.HIGH
        )
    
    def test_init(self, dm_flow):
        """Verifica inicialización."""
        assert dm_flow.max_concurrent == 10
        assert len(dm_flow.conversations) == 0
        assert dm_flow.stats["conversations_started"] == 0
    
    @pytest.mark.asyncio
    async def test_start_negotiation_success(
        self,
        dm_flow,
        sample_exchange_message,
        sample_content
    ):
        """Inicia negociación exitosamente."""
        success = await dm_flow.start_negotiation(
            exchange_message=sample_exchange_message,
            our_content=sample_content,
            language="es"
        )
        
        assert success is True
        assert sample_exchange_message.user_id in dm_flow.conversations
        assert dm_flow.stats["conversations_started"] == 1
    
    @pytest.mark.asyncio
    async def test_start_negotiation_duplicate(
        self,
        dm_flow,
        sample_exchange_message,
        sample_content
    ):
        """No permite duplicar conversación."""
        await dm_flow.start_negotiation(
            sample_exchange_message,
            sample_content,
            "es"
        )
        
        # Intentar de nuevo
        success = await dm_flow.start_negotiation(
            sample_exchange_message,
            sample_content,
            "es"
        )
        
        assert success is False
        assert dm_flow.stats["conversations_started"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_acceptance_with_link(
        self,
        dm_flow,
        sample_exchange_message,
        sample_content
    ):
        """Maneja aceptación con link."""
        # Iniciar conversación
        await dm_flow.start_negotiation(
            sample_exchange_message,
            sample_content,
            "es"
        )
        
        # Usuario responde con link
        response = await dm_flow.handle_response(
            user_id=sample_exchange_message.user_id,
            message_text="Aquí está https://youtube.com/user_video"
        )
        
        assert response is not None
        context = dm_flow.conversations[sample_exchange_message.user_id]
        assert context.user_link == "https://youtube.com/user_video"
        assert context.state == ConversationState.LINK_RECEIVED
    
    @pytest.mark.asyncio
    async def test_handle_rejection(
        self,
        dm_flow,
        sample_exchange_message,
        sample_content
    ):
        """Maneja rechazo."""
        await dm_flow.start_negotiation(
            sample_exchange_message,
            sample_content,
            "es"
        )
        
        response = await dm_flow.handle_response(
            user_id=sample_exchange_message.user_id,
            message_text="no gracias"
        )
        
        assert response is not None
        context = dm_flow.conversations[sample_exchange_message.user_id]
        assert context.state == ConversationState.REJECTED
        assert dm_flow.stats["rejections_detected"] == 1
    
    def test_get_stats(self, dm_flow):
        """Retorna estadísticas."""
        stats = dm_flow.get_stats()
        
        assert "conversations_started" in stats
        assert "acceptances_detected" in stats
        assert "active_conversations" in stats
