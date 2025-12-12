"""
Group Announcer - Sprint 7A
Publica anuncios controlados en grupos de Telegram.
"""
import asyncio
import random
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from telethon import TelegramClient
from telethon.tl.types import Channel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.telegram_exchange_bot.models import (
    TelegramGroup,
    OurContent,
    Platform,
    PriorityLevel
)
from app.telegram_exchange_bot.emotional import (
    EmotionalMessageGenerator,
    MessageType
)

logger = logging.getLogger(__name__)


class RateLimitManager:
    """
    Gestor de rate-limits por grupo.
    
    Regla: Máximo 1 anuncio cada 120-180 min por grupo.
    """
    
    def __init__(
        self,
        min_delay_minutes: int = 120,
        max_delay_minutes: int = 180
    ):
        """
        Args:
            min_delay_minutes: Delay mínimo entre anuncios
            max_delay_minutes: Delay máximo entre anuncios
        """
        self.min_delay = timedelta(minutes=min_delay_minutes)
        self.max_delay = timedelta(minutes=max_delay_minutes)
        
        # Track último anuncio por grupo
        self.last_announcement: Dict[int, datetime] = {}
        
        logger.info(
            f"RateLimitManager: delay {min_delay_minutes}-{max_delay_minutes} min"
        )
    
    def can_announce(self, group_id: int) -> bool:
        """
        Verifica si se puede anunciar en el grupo.
        
        Args:
            group_id: ID del grupo
            
        Returns:
            True si pasó el cooldown
        """
        if group_id not in self.last_announcement:
            return True
        
        last_time = self.last_announcement[group_id]
        time_passed = datetime.utcnow() - last_time
        
        # Delay aleatorio entre min y max
        required_delay = self.min_delay + timedelta(
            minutes=random.randint(0, (self.max_delay - self.min_delay).seconds // 60)
        )
        
        return time_passed >= required_delay
    
    def record_announcement(self, group_id: int):
        """Registra que se hizo un anuncio."""
        self.last_announcement[group_id] = datetime.utcnow()
        logger.info(f"Anuncio registrado para grupo {group_id}")
    
    def get_next_available_time(self, group_id: int) -> Optional[datetime]:
        """
        Obtiene cuándo se podrá anunciar nuevamente.
        
        Returns:
            Datetime del próximo anuncio disponible o None si ya está disponible
        """
        if group_id not in self.last_announcement:
            return None
        
        last_time = self.last_announcement[group_id]
        next_time = last_time + self.max_delay
        
        if datetime.utcnow() >= next_time:
            return None
        
        return next_time
    
    def get_cooldown_remaining(self, group_id: int) -> Optional[timedelta]:
        """
        Obtiene tiempo restante de cooldown.
        
        Returns:
            Timedelta o None si no hay cooldown
        """
        next_time = self.get_next_available_time(group_id)
        if not next_time:
            return None
        
        remaining = next_time - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else None


class GroupAnnouncer:
    """
    Publicador de anuncios en grupos de Telegram.
    
    Características:
    - Rate-limit: 1 anuncio cada 120-180 min por grupo
    - Templates multilinguaje variables
    - Prioriza YouTube cuando hay contenido en impulso
    - Adaptación al idioma del grupo
    """
    
    def __init__(
        self,
        client: TelegramClient,
        message_generator: EmotionalMessageGenerator,
        rate_limit_manager: Optional[RateLimitManager] = None
    ):
        """
        Args:
            client: Cliente de Telethon
            message_generator: Generador de mensajes
            rate_limit_manager: Gestor de rate-limits (se crea si no se proporciona)
        """
        self.client = client
        self.message_generator = message_generator
        self.rate_limit_manager = rate_limit_manager or RateLimitManager()
        
        # Stats
        self.stats = {
            "announcements_sent": 0,
            "announcements_failed": 0,
            "rate_limited": 0
        }
        
        logger.info("GroupAnnouncer inicializado")
    
    async def schedule_announcement(
        self,
        group: TelegramGroup,
        content: OurContent,
        language: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """
        Planifica y ejecuta anuncio en un grupo.
        
        Args:
            group: Grupo donde anunciar
            content: Contenido a promocionar
            language: Idioma del grupo (autodetecta si es None)
            force: Si True, ignora rate-limit (usar con cuidado)
            
        Returns:
            True si se publicó exitosamente
        """
        # Verificar rate-limit
        if not force and not self.rate_limit_manager.can_announce(group.telegram_id):
            cooldown = self.rate_limit_manager.get_cooldown_remaining(group.telegram_id)
            logger.info(
                f"Rate-limited: Grupo {group.name}. "
                f"Próximo anuncio en {cooldown}"
            )
            self.stats["rate_limited"] += 1
            return False
        
        # Publicar anuncio
        success = await self.publish_announcement(group, content, language)
        
        if success:
            # Registrar timestamp
            self.rate_limit_manager.record_announcement(group.telegram_id)
        
        return success
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish_announcement(
        self,
        group: TelegramGroup,
        content: OurContent,
        language: Optional[str] = None
    ) -> bool:
        """
        Publica anuncio en el grupo.
        
        Args:
            group: Grupo Telegram
            content: Contenido a promocionar
            language: Idioma (None = usar el del grupo)
            
        Returns:
            True si se publicó exitosamente
        """
        lang = language or group.language or "es"
        
        try:
            # Generar mensaje
            message = await self.message_generator.generate_announcement(
                content=content,
                group_name=group.name,
                language=lang
            )
            
            logger.info(
                f"Publicando anuncio en {group.name} ({lang}): "
                f"{message[:50]}..."
            )
            
            # Enviar mensaje
            await self.client.send_message(
                entity=group.telegram_id,
                message=message
            )
            
            self.stats["announcements_sent"] += 1
            
            logger.info(f"Anuncio publicado exitosamente en {group.name}")
            
            # Emitir telemetría
            await self._emit_telemetry("group_announcement_sent", {
                "group_id": group.telegram_id,
                "group_name": group.name,
                "content_id": content.id,
                "content_url": content.url,
                "platform": content.platform.value,
                "language": lang
            })
            
            return True
            
        except Exception as e:
            logger.error(
                f"Error publicando anuncio en {group.name}: {e}",
                exc_info=True
            )
            self.stats["announcements_failed"] += 1
            raise
    
    async def get_priority_content(
        self,
        available_content: List[OurContent]
    ) -> Optional[OurContent]:
        """
        Selecciona contenido prioritario para anunciar.
        
        Priorización:
        1. YouTube con priority=HIGH
        2. Instagram con priority=HIGH
        3. YouTube con priority=MEDIUM
        4. Resto
        
        Args:
            available_content: Lista de contenido disponible
            
        Returns:
            Contenido seleccionado o None
        """
        if not available_content:
            return None
        
        # Filtrar y ordenar
        youtube_high = [
            c for c in available_content
            if c.platform == Platform.YOUTUBE and c.priority == PriorityLevel.HIGH
        ]
        if youtube_high:
            return random.choice(youtube_high)
        
        instagram_high = [
            c for c in available_content
            if c.platform == Platform.INSTAGRAM and c.priority == PriorityLevel.HIGH
        ]
        if instagram_high:
            return random.choice(instagram_high)
        
        youtube_medium = [
            c for c in available_content
            if c.platform == Platform.YOUTUBE and c.priority == PriorityLevel.MEDIUM
        ]
        if youtube_medium:
            return random.choice(youtube_medium)
        
        # Si no hay prioridades, seleccionar cualquiera priorizando YouTube
        youtube_any = [c for c in available_content if c.platform == Platform.YOUTUBE]
        if youtube_any:
            return random.choice(youtube_any)
        
        # Fallback a cualquier contenido
        return random.choice(available_content)
    
    async def announce_to_multiple_groups(
        self,
        groups: List[TelegramGroup],
        content: OurContent,
        delay_between_groups: tuple = (30, 90)
    ) -> Dict[int, bool]:
        """
        Anuncia en múltiples grupos con delays.
        
        Args:
            groups: Lista de grupos
            content: Contenido a anunciar
            delay_between_groups: (min, max) segundos de delay entre grupos
            
        Returns:
            Dict con group_id -> success
        """
        results = {}
        
        for i, group in enumerate(groups):
            # Verificar rate-limit
            if not self.rate_limit_manager.can_announce(group.telegram_id):
                logger.info(f"Saltando {group.name} (rate-limited)")
                results[group.telegram_id] = False
                continue
            
            # Publicar
            success = await self.schedule_announcement(
                group=group,
                content=content,
                language=group.language
            )
            
            results[group.telegram_id] = success
            
            # Delay entre grupos (anti-spam)
            if i < len(groups) - 1:
                delay = random.randint(*delay_between_groups)
                logger.info(f"Esperando {delay}s antes del siguiente grupo...")
                await asyncio.sleep(delay)
        
        logger.info(
            f"Anuncios completados: "
            f"{sum(results.values())}/{len(groups)} exitosos"
        )
        
        return results
    
    async def smart_announce(
        self,
        groups: List[TelegramGroup],
        available_content: List[OurContent],
        max_groups: int = 10
    ) -> Dict[int, bool]:
        """
        Anuncio inteligente: selecciona contenido prioritario y grupos efectivos.
        
        Args:
            groups: Lista de grupos disponibles
            available_content: Contenido disponible para anunciar
            max_groups: Máximo número de grupos a anunciar
            
        Returns:
            Dict con group_id -> success
        """
        # Seleccionar contenido prioritario
        content = await self.get_priority_content(available_content)
        if not content:
            logger.warning("No hay contenido disponible para anunciar")
            return {}
        
        # Filtrar grupos:
        # 1. Sin rate-limit
        # 2. Ordenar por efficiency_ratio
        eligible_groups = [
            g for g in groups
            if self.rate_limit_manager.can_announce(g.telegram_id)
        ]
        
        if not eligible_groups:
            logger.info("No hay grupos elegibles (todos en rate-limit)")
            return {}
        
        # Ordenar por eficiencia
        eligible_groups.sort(key=lambda g: g.efficiency_ratio, reverse=True)
        
        # Tomar top N
        target_groups = eligible_groups[:max_groups]
        
        logger.info(
            f"Smart announce: Contenido={content.url}, "
            f"Grupos={len(target_groups)}/{len(groups)}"
        )
        
        # Anunciar
        return await self.announce_to_multiple_groups(target_groups, content)
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del announcer."""
        return {
            **self.stats,
            "groups_in_cooldown": len([
                gid for gid in self.rate_limit_manager.last_announcement
                if not self.rate_limit_manager.can_announce(gid)
            ])
        }
    
    async def _emit_telemetry(self, event_name: str, data: Dict):
        """Emite evento de telemetría."""
        # TODO: Integrar con sistema de telemetría central
        logger.info(f"[TELEMETRY] {event_name}: {data}")
