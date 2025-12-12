"""
Message Listener - Sprint 7A
Monitorea grupos de Telegram, detecta oportunidades de intercambio.
"""
import re
import asyncio
import logging
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass

from telethon import TelegramClient, events
from telethon.tl.types import Message, User, Channel
from langdetect import detect, LangDetectException

from app.telegram_exchange_bot.models import (
    ExchangeMessage,
    TelegramGroup,
    TelegramUser,
    Platform,
    MessageStatus
)

logger = logging.getLogger(__name__)


@dataclass
class OpportunityQueue:
    """Cola de oportunidades detectadas."""
    message: ExchangeMessage
    priority: int  # 1-10 (10 = máxima prioridad)
    detected_at: datetime


class URLDetector:
    """Detector de URLs de plataformas sociales."""
    
    # Patterns regex para cada plataforma
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)',
    ]
    
    INSTAGRAM_PATTERNS = [
        r'(?:https?://)?(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/reel/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9_\.]+)/?$',
    ]
    
    TIKTOK_PATTERNS = [
        r'(?:https?://)?(?:www\.)?tiktok\.com/@([a-zA-Z0-9_\.]+)/video/(\d+)',
        r'(?:https?://)?vm\.tiktok\.com/([a-zA-Z0-9]+)',
        r'(?:https?://)?(?:www\.)?tiktok\.com/@([a-zA-Z0-9_\.]+)',
    ]
    
    @classmethod
    def extract_urls(cls, text: str) -> Dict[Platform, List[str]]:
        """
        Extrae URLs de todas las plataformas.
        
        Returns:
            Dict con Platform -> [urls]
        """
        results = {}
        
        # YouTube
        youtube_urls = []
        for pattern in cls.YOUTUBE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                youtube_urls.append(match.group(0))
        if youtube_urls:
            results[Platform.YOUTUBE] = youtube_urls
        
        # Instagram
        instagram_urls = []
        for pattern in cls.INSTAGRAM_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                instagram_urls.append(match.group(0))
        if instagram_urls:
            results[Platform.INSTAGRAM] = instagram_urls
        
        # TikTok
        tiktok_urls = []
        for pattern in cls.TIKTOK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tiktok_urls.append(match.group(0))
        if tiktok_urls:
            results[Platform.TIKTOK] = tiktok_urls
        
        return results
    
    @classmethod
    def has_any_url(cls, text: str) -> bool:
        """Verifica si hay alguna URL de plataformas."""
        urls = cls.extract_urls(text)
        return len(urls) > 0


class KeywordMatcher:
    """Matcher de keywords de intercambio por idioma."""
    
    KEYWORDS = {
        "es": [
            "like x like", "like por like", "l4l", "lxl",
            "sub x sub", "sub por sub", "s4s", "sxs",
            "apoyo mutuo", "apoyo musical", "ayuda mutua",
            "intercambio", "promoción musical", "intercambio musical",
            "crecimiento mutuo", "colaboración", "colaboracion",
            "suscripción por suscripción", "suscripcion por suscripcion"
        ],
        "en": [
            "like for like", "like 4 like", "l4l",
            "sub for sub", "sub 4 sub", "s4s",
            "mutual support", "music promotion", "mutual help",
            "exchange", "grow together", "collaboration",
            "subscribe for subscribe", "help each other"
        ],
        "pt": [
            "troca de like", "like por like", "l4l",
            "troca de sub", "sub por sub", "s4s",
            "apoio mútuo", "apoio mutuo", "apoio musical",
            "troca", "promoção musical", "promocao musical",
            "crescimento mútuo", "crescimento mutuo",
            "colaboração", "colaboracao",
            "inscrição por inscrição", "inscricao por inscricao"
        ]
    }
    
    @classmethod
    def match(cls, text: str, language: Optional[str] = None) -> bool:
        """
        Verifica si el texto contiene keywords de intercambio.
        
        Args:
            text: Texto a analizar
            language: Idioma (None = busca en todos)
            
        Returns:
            True si contiene keywords
        """
        text_lower = text.lower()
        
        if language:
            keywords = cls.KEYWORDS.get(language, [])
            return any(kw in text_lower for kw in keywords)
        else:
            # Buscar en todos los idiomas
            for keywords in cls.KEYWORDS.values():
                if any(kw in text_lower for kw in keywords):
                    return True
            return False
    
    @classmethod
    def get_matched_keywords(cls, text: str) -> List[str]:
        """Retorna lista de keywords que matchearon."""
        text_lower = text.lower()
        matched = []
        
        for lang, keywords in cls.KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched.append(kw)
        
        return matched


class MessageClassifier:
    """Clasificador de mensajes."""
    
    @staticmethod
    def classify(
        text: str,
        has_urls: bool,
        has_keywords: bool
    ) -> str:
        """
        Clasifica mensaje en: oportunidad | ruido | spam
        
        Args:
            text: Texto del mensaje
            has_urls: Si contiene URLs de plataformas
            has_keywords: Si contiene keywords de intercambio
            
        Returns:
            Clasificación
        """
        # Spam detection simple
        if len(text) > 1000:
            return "spam"
        
        # Detectar spam obvio (muchos emojis, caps)
        emoji_count = sum(1 for c in text if ord(c) > 0x1F300)
        if emoji_count > 20:
            return "spam"
        
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.7 and len(text) > 20:
            return "spam"
        
        # Oportunidad si tiene keywords + URLs
        if has_keywords and has_urls:
            return "oportunidad"
        
        # Oportunidad si solo tiene keywords (esperamos que pase link después)
        if has_keywords:
            return "oportunidad"
        
        # Si solo tiene URLs sin keywords -> posible contenido a interceptar
        if has_urls:
            return "oportunidad"
        
        # Resto es ruido
        return "ruido"


class MessageListener:
    """
    Monitor de grupos de Telegram.
    
    Características:
    - Monitorea hasta 200 grupos simultáneamente
    - Detecta keywords de intercambio en 3 idiomas
    - Extrae URLs (YouTube/Instagram/TikTok)
    - Clasifica mensajes
    - Detecta idioma del grupo
    - Encola oportunidades para announcer/dm_flow
    """
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_name: str = "telegram_exchange_bot"
    ):
        """
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Número de teléfono
            session_name: Nombre de sesión
        """
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.phone = phone
        
        # Estado interno
        self.monitored_groups: Dict[int, TelegramGroup] = {}
        self.opportunity_queue: deque = deque(maxlen=1000)
        self.processed_messages: Set[int] = set()  # Dedup
        
        # Estadísticas
        self.stats = {
            "messages_processed": 0,
            "opportunities_detected": 0,
            "urls_detected": 0,
            "groups_active": 0
        }
        
        # Límite de mensajes recientes por grupo (para detectar idioma)
        self.recent_messages: Dict[int, deque] = {}
        
        logger.info(f"MessageListener inicializado para {phone}")
    
    async def start(self):
        """Inicia cliente de Telegram."""
        await self.client.start(phone=self.phone)
        me = await self.client.get_me()
        logger.info(f"Conectado como: {me.first_name} (@{me.username})")
    
    async def stop(self):
        """Detiene cliente."""
        await self.client.disconnect()
        logger.info("Cliente de Telegram desconectado")
    
    async def add_group(self, group: TelegramGroup):
        """
        Añade grupo para monitorear.
        
        Args:
            group: TelegramGroup a monitorear
        """
        self.monitored_groups[group.telegram_id] = group
        self.recent_messages[group.telegram_id] = deque(maxlen=50)
        
        logger.info(
            f"Grupo añadido: {group.name} (ID: {group.telegram_id}). "
            f"Total: {len(self.monitored_groups)}"
        )
    
    async def remove_group(self, telegram_id: int):
        """Remueve grupo del monitoreo."""
        if telegram_id in self.monitored_groups:
            group = self.monitored_groups.pop(telegram_id)
            self.recent_messages.pop(telegram_id, None)
            logger.info(f"Grupo removido: {group.name}")
    
    def detect_language(self, group_id: int) -> str:
        """
        Detecta idioma predominante del grupo.
        
        Args:
            group_id: ID del grupo
            
        Returns:
            Código de idioma (es/en/pt)
        """
        if group_id not in self.recent_messages:
            return "es"
        
        recent = list(self.recent_messages[group_id])
        if not recent:
            return "es"
        
        # Concatenar últimos 10 mensajes
        sample_text = " ".join(recent[-10:])
        
        try:
            lang = detect(sample_text)
            if lang in ["es", "en", "pt"]:
                return lang
            elif lang in ["fr", "it", "ca"]:
                return "es"  # Fallback latino
            else:
                return "es"
        except LangDetectException:
            return "es"
    
    async def monitor_groups(self):
        """
        Loop principal de monitoreo.
        Escucha mensajes nuevos en todos los grupos.
        """
        @self.client.on(events.NewMessage())
        async def handler(event: events.NewMessage.Event):
            await self._handle_new_message(event)
        
        logger.info(f"Monitoreando {len(self.monitored_groups)} grupos...")
        
        # Actualizar stats
        self.stats["groups_active"] = len(self.monitored_groups)
        
        # Mantener cliente vivo
        await self.client.run_until_disconnected()
    
    async def _handle_new_message(self, event: events.NewMessage.Event):
        """
        Handler de mensajes nuevos.
        
        Args:
            event: Evento de Telethon
        """
        try:
            message: Message = event.message
            
            # Ignorar mensajes propios
            if message.out:
                return
            
            # Verificar que es de un grupo monitoreado
            chat = await event.get_chat()
            if not isinstance(chat, Channel):
                return
            
            group_id = chat.id
            if group_id not in self.monitored_groups:
                return
            
            # Dedup
            if message.id in self.processed_messages:
                return
            self.processed_messages.add(message.id)
            
            # Limpiar set si crece mucho
            if len(self.processed_messages) > 10000:
                self.processed_messages.clear()
            
            # Procesar mensaje
            await self._process_message(message, group_id)
            
            self.stats["messages_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
    
    async def _process_message(self, message: Message, group_id: int):
        """
        Procesa mensaje individual.
        
        Args:
            message: Mensaje de Telethon
            group_id: ID del grupo
        """
        text = message.text or ""
        
        if not text:
            return
        
        # Guardar para detección de idioma
        if group_id in self.recent_messages:
            self.recent_messages[group_id].append(text)
        
        # Detectar URLs
        urls_by_platform = URLDetector.extract_urls(text)
        has_urls = len(urls_by_platform) > 0
        
        if has_urls:
            self.stats["urls_detected"] += 1
        
        # Detectar keywords
        has_keywords = KeywordMatcher.match(text)
        matched_keywords = KeywordMatcher.get_matched_keywords(text) if has_keywords else []
        
        # Clasificar mensaje
        classification = MessageClassifier.classify(text, has_urls, has_keywords)
        
        # Solo procesar oportunidades
        if classification != "oportunidad":
            return
        
        # Detectar idioma del grupo
        language = self.detect_language(group_id)
        
        # Obtener info del usuario
        sender = await message.get_sender()
        user_id = sender.id if sender else 0
        username = getattr(sender, 'username', None)
        first_name = getattr(sender, 'first_name', '')
        
        # Crear modelo de mensaje
        group = self.monitored_groups[group_id]
        
        exchange_msg = ExchangeMessage(
            id=0,  # Se asignará en BD
            telegram_message_id=message.id,
            group_id=group_id,
            group_name=group.name,
            user_id=user_id,
            username=username,
            user_first_name=first_name,
            message_text=text,
            detected_platforms=list(urls_by_platform.keys()),
            detected_urls={
                platform.value: urls 
                for platform, urls in urls_by_platform.items()
            },
            keywords_matched=matched_keywords,
            language=language,
            status=MessageStatus.PENDING,
            detected_at=datetime.utcnow()
        )
        
        # Calcular prioridad
        priority = self._calculate_priority(exchange_msg, group)
        
        # Encolar oportunidad
        opportunity = OpportunityQueue(
            message=exchange_msg,
            priority=priority,
            detected_at=datetime.utcnow()
        )
        
        self.opportunity_queue.append(opportunity)
        self.stats["opportunities_detected"] += 1
        
        logger.info(
            f"Oportunidad detectada: Grupo={group.name}, "
            f"User=@{username or user_id}, "
            f"Platforms={[p.value for p in urls_by_platform.keys()]}, "
            f"Keywords={len(matched_keywords)}, "
            f"Lang={language}, Priority={priority}"
        )
        
        # Emitir telemetría
        await self._emit_telemetry("exchange_opportunity_detected", {
            "group_id": group_id,
            "group_name": group.name,
            "user_id": user_id,
            "username": username,
            "platforms": [p.value for p in urls_by_platform.keys()],
            "keywords": matched_keywords,
            "language": language,
            "priority": priority
        })
    
    def _calculate_priority(
        self,
        message: ExchangeMessage,
        group: TelegramGroup
    ) -> int:
        """
        Calcula prioridad de la oportunidad (1-10).
        
        Factores:
        - Plataforma (YouTube=10, Instagram=7, TikTok=5)
        - Eficiencia del grupo
        - Cantidad de keywords
        - Si tiene URLs
        
        Returns:
            Prioridad 1-10
        """
        priority = 5  # Base
        
        # Boost por plataforma
        if Platform.YOUTUBE in message.detected_platforms:
            priority += 3
        elif Platform.INSTAGRAM in message.detected_platforms:
            priority += 2
        elif Platform.TIKTOK in message.detected_platforms:
            priority += 1
        
        # Boost por keywords
        if len(message.keywords_matched) >= 3:
            priority += 1
        
        # Boost por eficiencia del grupo
        if group.efficiency_ratio > 0.5:
            priority += 1
        
        # Cap a 10
        return min(priority, 10)
    
    async def get_next_opportunity(self) -> Optional[OpportunityQueue]:
        """
        Obtiene siguiente oportunidad de la cola (FIFO).
        
        Returns:
            Oportunidad o None si cola vacía
        """
        if not self.opportunity_queue:
            return None
        
        return self.opportunity_queue.popleft()
    
    async def get_opportunities_sorted(self, limit: int = 10) -> List[OpportunityQueue]:
        """
        Obtiene oportunidades ordenadas por prioridad.
        
        Args:
            limit: Máximo número de oportunidades
            
        Returns:
            Lista ordenada por prioridad (mayor a menor)
        """
        # Convertir deque a lista y ordenar
        opportunities = sorted(
            list(self.opportunity_queue),
            key=lambda x: x.priority,
            reverse=True
        )
        
        return opportunities[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del listener."""
        return {
            **self.stats,
            "queue_size": len(self.opportunity_queue),
            "monitored_groups": len(self.monitored_groups)
        }
    
    async def _emit_telemetry(self, event_name: str, data: Dict[str, Any]):
        """
        Emite evento de telemetría.
        
        Args:
            event_name: Nombre del evento
            data: Datos del evento
        """
        # TODO: Integrar con sistema de telemetría central
        logger.info(f"[TELEMETRY] {event_name}: {data}")
