"""
DM Negotiation Flow - Sprint 7A
Flujo conversacional de negociación privada en Telegram.
"""
import asyncio
import re
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from telethon import TelegramClient, events
from telethon.tl.types import User

from app.telegram_exchange_bot.models import (
    ExchangeMessage,
    TelegramUser,
    OurContent,
    Platform,
    InteractionType
)
from app.telegram_exchange_bot.emotional import (
    EmotionalMessageGenerator,
    MessageType
)

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Estados de una conversación DM."""
    NEW = "new"                          # Conversación nueva (no iniciada)
    INTRO_SENT = "intro_sent"            # Mensaje intro enviado
    WAITING_RESPONSE = "waiting_response"  # Esperando respuesta del usuario
    LINK_REQUESTED = "link_requested"    # Se pidió el link del usuario
    LINK_RECEIVED = "link_received"      # Usuario pasó su link
    NEGOTIATION_COMPLETED = "completed"  # Negociación completada
    REJECTED = "rejected"                # Usuario rechazó
    STALLED = "stalled"                  # Conversación abandonada


class AcceptanceSignal(str, Enum):
    """Señales de aceptación detectadas."""
    EXPLICIT_YES = "explicit_yes"        # "sí", "ok", "dale"
    SENT_LINK = "sent_link"              # Pasó su link
    CONFIRMATION = "confirmation"        # "listo", "hecho", "ya está"
    QUESTION = "question"                # Pregunta sobre el intercambio


class RejectionSignal(str, Enum):
    """Señales de rechazo detectadas."""
    EXPLICIT_NO = "explicit_no"          # "no", "no gracias"
    INSULT = "insult"                    # Insultos, spam
    IGNORE = "ignore"                    # No responde en 48h


@dataclass
class ConversationContext:
    """Contexto de una conversación."""
    user_id: int
    username: Optional[str]
    state: ConversationState
    language: str
    our_content: OurContent
    group_name: str
    messages: List[Dict]  # Historial de mensajes
    user_link: Optional[str] = None
    platform_requested: Optional[Platform] = None
    interaction_types: List[InteractionType] = None
    started_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.interaction_types is None:
            self.interaction_types = []


class ResponseAnalyzer:
    """Analizador de respuestas del usuario."""
    
    # Keywords de aceptación por idioma
    ACCEPTANCE_KEYWORDS = {
        "es": ["si", "sí", "ok", "dale", "va", "vamos", "bueno", "perfecto", 
               "genial", "listo", "hecho", "claro", "acepto", "trato"],
        "en": ["yes", "ok", "okay", "sure", "yep", "yeah", "fine", "deal", 
               "done", "cool", "great", "perfect", "sure thing"],
        "pt": ["sim", "ok", "beleza", "vai", "vamos", "bom", "perfeito", 
               "show", "pronto", "feito", "claro", "aceito"]
    }
    
    # Keywords de rechazo
    REJECTION_KEYWORDS = {
        "es": ["no", "nah", "nop", "paso", "spam", "bot", "scam", "estafa"],
        "en": ["no", "nope", "nah", "pass", "spam", "bot", "scam", "fake"],
        "pt": ["não", "nao", "não", "nah", "spam", "bot", "golpe"]
    }
    
    @classmethod
    def detect_acceptance(cls, text: str, language: str) -> Optional[AcceptanceSignal]:
        """
        Detecta señales de aceptación.
        
        Returns:
            AcceptanceSignal o None
        """
        text_lower = text.lower()
        
        # Detectar si pasó un link
        if cls._has_url(text):
            return AcceptanceSignal.SENT_LINK
        
        # Keywords de confirmación
        confirmation_words = ["listo", "hecho", "ya", "done", "ready", "pronto"]
        if any(word in text_lower for word in confirmation_words):
            return AcceptanceSignal.CONFIRMATION
        
        # Keywords de aceptación explícita
        acceptance_kw = cls.ACCEPTANCE_KEYWORDS.get(language, cls.ACCEPTANCE_KEYWORDS["es"])
        if any(word in text_lower for word in acceptance_kw):
            return AcceptanceSignal.EXPLICIT_YES
        
        # Preguntas sobre el intercambio (interés)
        question_markers = ["?", "cómo", "como", "cuál", "cual", "dónde", "donde",
                           "how", "what", "where", "when", "como", "qual", "onde"]
        if any(marker in text_lower for marker in question_markers):
            return AcceptanceSignal.QUESTION
        
        return None
    
    @classmethod
    def detect_rejection(cls, text: str, language: str) -> Optional[RejectionSignal]:
        """
        Detecta señales de rechazo.
        
        Returns:
            RejectionSignal o None
        """
        text_lower = text.lower()
        
        # Keywords explícitas de rechazo
        rejection_kw = cls.REJECTION_KEYWORDS.get(language, cls.REJECTION_KEYWORDS["es"])
        if any(word in text_lower for word in rejection_kw):
            return RejectionSignal.EXPLICIT_NO
        
        # Detectar insultos (simple)
        insults = ["fuck", "shit", "idiota", "estúpido", "imbecil", "idiota"]
        if any(insult in text_lower for insult in insults):
            return RejectionSignal.INSULT
        
        return None
    
    @staticmethod
    def _has_url(text: str) -> bool:
        """Detecta si el texto contiene URLs."""
        url_pattern = r'https?://[^\s]+'
        return bool(re.search(url_pattern, text))
    
    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extrae primera URL del texto."""
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None


class InteractionRequestBuilder:
    """Constructor de solicitudes de interacción por plataforma."""
    
    @staticmethod
    def build_request(platform: Platform, language: str = "es") -> Tuple[List[InteractionType], str]:
        """
        Construye solicitud de interacción según plataforma.
        
        Returns:
            (Lista de tipos de interacción, texto descriptivo)
        """
        requests = {
            Platform.YOUTUBE: {
                "types": [InteractionType.YOUTUBE_LIKE, InteractionType.YOUTUBE_COMMENT, 
                         InteractionType.YOUTUBE_SUBSCRIBE],
                "text": {
                    "es": "like + comment + suscripción",
                    "en": "like + comment + subscribe",
                    "pt": "like + comment + inscrição"
                }
            },
            Platform.INSTAGRAM: {
                "types": [InteractionType.INSTAGRAM_LIKE, InteractionType.INSTAGRAM_COMMENT,
                         InteractionType.INSTAGRAM_SAVE],
                "text": {
                    "es": "like + comment + guardado",
                    "en": "like + comment + save",
                    "pt": "like + comment + salvar"
                }
            },
            Platform.TIKTOK: {
                "types": [InteractionType.TIKTOK_LIKE, InteractionType.TIKTOK_COMMENT],
                "text": {
                    "es": "like + comment",
                    "en": "like + comment",
                    "pt": "like + comment"
                }
            },
            Platform.FANPAGE: {
                "types": [InteractionType.FANPAGE_LIKE, InteractionType.FANPAGE_COMMENT,
                         InteractionType.FANPAGE_SHARE],
                "text": {
                    "es": "like + comment + compartir",
                    "en": "like + comment + share",
                    "pt": "like + comment + compartilhar"
                }
            }
        }
        
        req = requests.get(platform, requests[Platform.YOUTUBE])
        text = req["text"].get(language, req["text"]["es"])
        
        return req["types"], text


class DMNegotiationFlow:
    """
    Gestor de flujo de negociación privada.
    
    Características:
    - Inicia conversaciones con usuarios detectados
    - Mantiene contexto multi-turno
    - Detecta aceptación/rechazo
    - Adapta solicitud por plataforma
    - Registra interacciones (sin ejecutar en Sprint 7A)
    - Multilenguaje
    """
    
    def __init__(
        self,
        client: TelegramClient,
        message_generator: EmotionalMessageGenerator,
        max_concurrent_conversations: int = 50
    ):
        """
        Args:
            client: Cliente de Telethon
            message_generator: Generador de mensajes
            max_concurrent_conversations: Máximo de conversaciones activas
        """
        self.client = client
        self.message_generator = message_generator
        self.max_concurrent = max_concurrent_conversations
        
        # Conversaciones activas
        self.conversations: Dict[int, ConversationContext] = {}
        
        # Stats
        self.stats = {
            "conversations_started": 0,
            "acceptances_detected": 0,
            "rejections_detected": 0,
            "negotiations_completed": 0,
            "messages_sent": 0
        }
        
        logger.info(f"DMNegotiationFlow inicializado (max concurrent: {self.max_concurrent})")
    
    async def start_negotiation(
        self,
        exchange_message: ExchangeMessage,
        our_content: OurContent,
        language: Optional[str] = None
    ) -> bool:
        """
        Inicia negociación con un usuario.
        
        Args:
            exchange_message: Mensaje detectado del usuario
            our_content: Nuestro contenido a promocionar
            language: Idioma (None = usar el del mensaje)
            
        Returns:
            True si se inició exitosamente
        """
        user_id = exchange_message.user_id
        
        # Verificar límite de conversaciones concurrentes
        active_convs = len([
            c for c in self.conversations.values()
            if c.state not in [ConversationState.NEGOTIATION_COMPLETED, 
                              ConversationState.REJECTED,
                              ConversationState.STALLED]
        ])
        
        if active_convs >= self.max_concurrent:
            logger.warning(
                f"Límite de conversaciones alcanzado ({active_convs}/{self.max_concurrent}). "
                f"Saltando usuario {user_id}"
            )
            return False
        
        # Verificar si ya existe conversación con este usuario
        if user_id in self.conversations:
            logger.info(f"Ya existe conversación con usuario {user_id}")
            return False
        
        lang = language or exchange_message.language or "es"
        
        # Crear contexto
        context = ConversationContext(
            user_id=user_id,
            username=exchange_message.username,
            state=ConversationState.NEW,
            language=lang,
            our_content=our_content,
            group_name=exchange_message.group_name,
            messages=[],
            platform_requested=our_content.platform
        )
        
        # Determinar tipos de interacción solicitados
        interaction_types, _ = InteractionRequestBuilder.build_request(
            our_content.platform,
            lang
        )
        context.interaction_types = interaction_types
        
        self.conversations[user_id] = context
        
        # Enviar mensaje intro
        success = await self.send_intro_message(context, exchange_message.message_text)
        
        if success:
            self.stats["conversations_started"] += 1
            context.state = ConversationState.INTRO_SENT
            
            logger.info(
                f"Negociación iniciada con @{exchange_message.username or user_id} "
                f"({lang}, Platform: {our_content.platform.value})"
            )
            
            # Emitir telemetría
            await self._emit_telemetry("dm_started", {
                "user_id": user_id,
                "username": exchange_message.username,
                "language": lang,
                "platform": our_content.platform.value,
                "content_url": our_content.url
            })
        
        return success
    
    async def send_intro_message(
        self,
        context: ConversationContext,
        user_original_message: Optional[str] = None
    ) -> bool:
        """
        Envía mensaje inicial de presentación.
        
        Args:
            context: Contexto de conversación
            user_original_message: Mensaje original del usuario (contexto)
            
        Returns:
            True si se envió exitosamente
        """
        try:
            # Generar mensaje intro
            message = await self.message_generator.generate_dm_intro(
                content=context.our_content,
                group_name=context.group_name,
                user_message=user_original_message,
                language=context.language
            )
            
            # Enviar DM
            await self.client.send_message(
                entity=context.user_id,
                message=message
            )
            
            # Guardar en historial
            context.messages.append({
                "sender": "bot",
                "text": message,
                "timestamp": datetime.utcnow()
            })
            context.last_activity = datetime.utcnow()
            
            self.stats["messages_sent"] += 1
            
            logger.info(f"Mensaje intro enviado a {context.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando intro a {context.user_id}: {e}")
            return False
    
    async def handle_response(
        self,
        user_id: int,
        message_text: str
    ) -> Optional[str]:
        """
        Maneja respuesta del usuario.
        
        Args:
            user_id: ID del usuario
            message_text: Texto de la respuesta
            
        Returns:
            Respuesta del bot o None
        """
        if user_id not in self.conversations:
            logger.warning(f"Respuesta de usuario {user_id} sin conversación activa")
            return None
        
        context = self.conversations[user_id]
        
        # Guardar mensaje del usuario
        context.messages.append({
            "sender": "user",
            "text": message_text,
            "timestamp": datetime.utcnow()
        })
        context.last_activity = datetime.utcnow()
        
        # Analizar respuesta
        acceptance = ResponseAnalyzer.detect_acceptance(message_text, context.language)
        rejection = ResponseAnalyzer.detect_rejection(message_text, context.language)
        
        if rejection:
            return await self._handle_rejection(context, rejection)
        
        if acceptance:
            return await self._handle_acceptance(context, acceptance, message_text)
        
        # Respuesta neutral -> followup genérico
        return await self._send_followup(context)
    
    async def _handle_acceptance(
        self,
        context: ConversationContext,
        signal: AcceptanceSignal,
        message_text: str
    ) -> str:
        """Maneja señal de aceptación."""
        self.stats["acceptances_detected"] += 1
        
        if signal == AcceptanceSignal.SENT_LINK:
            # Usuario pasó su link
            user_link = ResponseAnalyzer.extract_url(message_text)
            context.user_link = user_link
            context.state = ConversationState.LINK_RECEIVED
            
            logger.info(f"Link recibido de {context.user_id}: {user_link}")
            
            # Ofrecer más cuentas
            response = await self._generate_from_template(
                MessageType.DM_CONFIRMATION,
                context.language
            )
            
            # Registrar negociación completada
            await self._complete_negotiation(context)
            
            return response
        
        elif signal == AcceptanceSignal.EXPLICIT_YES:
            # Usuario aceptó, pedir su link
            context.state = ConversationState.LINK_REQUESTED
            
            response = await self._generate_from_template(
                MessageType.DM_REQUEST_LINK,
                context.language
            )
            
            return response
        
        elif signal == AcceptanceSignal.CONFIRMATION:
            # Usuario confirma que ya hizo su parte
            if context.state == ConversationState.LINK_REQUESTED:
                # Pedirle el link
                response = await self._generate_from_template(
                    MessageType.DM_REQUEST_LINK,
                    context.language
                )
                return response
            else:
                # Agradecer
                response = await self._generate_from_template(
                    MessageType.DM_THANKS,
                    context.language
                )
                await self._complete_negotiation(context)
                return response
        
        elif signal == AcceptanceSignal.QUESTION:
            # Usuario pregunta algo -> enviar followup
            return await self._send_followup(context)
        
        return await self._send_followup(context)
    
    async def _handle_rejection(
        self,
        context: ConversationContext,
        signal: RejectionSignal
    ) -> str:
        """Maneja señal de rechazo."""
        self.stats["rejections_detected"] += 1
        context.state = ConversationState.REJECTED
        
        logger.info(f"Rechazo detectado de {context.user_id}: {signal.value}")
        
        # Respuesta educada
        response = await self._generate_from_template(
            MessageType.DM_REJECTION,
            context.language
        )
        
        return response
    
    async def _send_followup(self, context: ConversationContext) -> str:
        """Envía mensaje de seguimiento."""
        response = await self.message_generator.generate_followup(
            content=context.our_content,
            conversation_history=[m["text"] for m in context.messages[-5:]],
            language=context.language
        )
        
        logger.info(f"Followup enviado a {context.user_id}")
        
        await self._emit_telemetry("dm_followup_sent", {
            "user_id": context.user_id,
            "state": context.state.value
        })
        
        return response
    
    async def _complete_negotiation(self, context: ConversationContext):
        """Completa negociación y registra en BD (sin ejecutar)."""
        context.state = ConversationState.NEGOTIATION_COMPLETED
        self.stats["negotiations_completed"] += 1
        
        logger.info(
            f"Negociación completada con {context.user_id}. "
            f"Link: {context.user_link}, "
            f"Platform: {context.platform_requested.value if context.platform_requested else 'N/A'}"
        )
        
        # TODO Sprint 7B: Registrar en BD para ejecución posterior
        # await self.db.create_exchange_interaction(
        #     our_content=context.our_content,
        #     user_link=context.user_link,
        #     interaction_types=context.interaction_types
        # )
        
        await self._emit_telemetry("dm_negotiation_completed", {
            "user_id": context.user_id,
            "username": context.username,
            "user_link": context.user_link,
            "platform": context.platform_requested.value if context.platform_requested else None,
            "interaction_types": [it.value for it in context.interaction_types],
            "duration_minutes": (datetime.utcnow() - context.started_at).total_seconds() / 60
        })
    
    async def _generate_from_template(
        self,
        message_type: MessageType,
        language: str
    ) -> str:
        """Helper para generar mensaje desde template."""
        return self.message_generator._generate_from_template(
            message_type,
            language,
            {}
        )
    
    async def cleanup_stalled_conversations(self, stale_hours: int = 48):
        """
        Limpia conversaciones abandonadas.
        
        Args:
            stale_hours: Horas de inactividad para marcar como stalled
        """
        now = datetime.utcnow()
        stale_threshold = timedelta(hours=stale_hours)
        
        stalled_count = 0
        
        for user_id, context in list(self.conversations.items()):
            if context.state in [ConversationState.NEGOTIATION_COMPLETED, 
                                ConversationState.REJECTED]:
                continue
            
            time_inactive = now - context.last_activity
            if time_inactive > stale_threshold:
                context.state = ConversationState.STALLED
                stalled_count += 1
                logger.info(f"Conversación {user_id} marcada como stalled ({time_inactive})")
        
        logger.info(f"Cleanup: {stalled_count} conversaciones marcadas como stalled")
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas."""
        active_states = [ConversationState.INTRO_SENT, ConversationState.WAITING_RESPONSE,
                        ConversationState.LINK_REQUESTED, ConversationState.LINK_RECEIVED]
        
        return {
            **self.stats,
            "active_conversations": len([
                c for c in self.conversations.values() if c.state in active_states
            ]),
            "total_conversations": len(self.conversations)
        }
    
    async def _emit_telemetry(self, event_name: str, data: Dict):
        """Emite evento de telemetría."""
        logger.info(f"[TELEMETRY] {event_name}: {data}")
