"""
Auto Group Joiner - Sprint 7A
Búsqueda y unión automática a grupos de intercambio.
"""
import asyncio
import random
import logging
from typing import List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel, Chat
from telethon.errors import FloodWaitError, UserAlreadyParticipantError

from app.telegram_exchange_bot.models import TelegramGroup
from app.telegram_exchange_bot.captcha_resolver import CaptchaResolver

logger = logging.getLogger(__name__)


@dataclass
class GroupCandidate:
    """Candidato a grupo para unirse."""
    id: int
    username: Optional[str]
    title: str
    members_count: int
    description: Optional[str]
    language: str
    score: float  # 0-1 (confianza de que es grupo legítimo)


class GroupSearcher:
    """Buscador de grupos públicos."""
    
    # Keywords por idioma
    SEARCH_KEYWORDS = {
        "es": [
            "like x like", "sub x sub", "apoyo mutuo", "música", "musica",
            "intercambio musical", "promoción musical", "promocion musical",
            "artistas", "youtubers", "músicos", "musicos"
        ],
        "en": [
            "like for like", "sub 4 sub", "l4l", "s4s", "music promotion",
            "mutual support", "musicians", "artists", "youtubers", "music exchange"
        ],
        "pt": [
            "troca de like", "troca de sub", "apoio mútuo", "apoio mutuo",
            "música", "musica", "promoção musical", "promocao musical",
            "artistas", "músicos", "musicos"
        ],
        "it": [
            "scambio like", "scambio sub", "supporto reciproco",
            "promozione musicale", "musica", "artisti", "musicisti"
        ],
        "fr": [
            "échange like", "échange sub", "soutien mutuel",
            "promotion musicale", "musique", "artistes", "musiciens"
        ]
    }
    
    def __init__(self, client: TelegramClient):
        """
        Args:
            client: Cliente de Telethon
        """
        self.client = client
    
    async def search_groups(
        self,
        keywords: List[str],
        limit: int = 20
    ) -> List[GroupCandidate]:
        """
        Busca grupos públicos por keywords.
        
        Args:
            keywords: Lista de keywords a buscar
            limit: Máximo de resultados
            
        Returns:
            Lista de GroupCandidate
        """
        all_candidates = []
        
        for keyword in keywords:
            try:
                logger.info(f"Buscando grupos: '{keyword}'")
                
                # Búsqueda global (solo funciona con username)
                result = await self.client(SearchRequest(
                    q=keyword,
                    limit=limit
                ))
                
                # Filtrar solo chats/canales
                for chat in result.chats:
                    if isinstance(chat, (Channel, Chat)):
                        candidate = await self._create_candidate(chat, keyword)
                        if candidate:
                            all_candidates.append(candidate)
                
                # Delay anti-spam
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error buscando '{keyword}': {e}")
                continue
        
        # Deduplicar por ID
        seen_ids = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate.id not in seen_ids:
                seen_ids.add(candidate.id)
                unique_candidates.append(candidate)
        
        # Ordenar por score
        unique_candidates.sort(key=lambda c: c.score, reverse=True)
        
        logger.info(f"Encontrados {len(unique_candidates)} grupos únicos")
        return unique_candidates[:limit]
    
    async def _create_candidate(
        self,
        chat: Channel,
        keyword: str
    ) -> Optional[GroupCandidate]:
        """Crea GroupCandidate desde chat."""
        try:
            # Obtener info completa
            full_chat = await self.client.get_entity(chat)
            
            title = getattr(full_chat, 'title', '')
            username = getattr(full_chat, 'username', None)
            description = getattr(full_chat, 'about', '')
            
            # Contar miembros (aproximado)
            members_count = getattr(full_chat, 'participants_count', 0)
            
            # Detectar idioma (simple)
            text_sample = f"{title} {description}".lower()
            language = self._detect_language(text_sample)
            
            # Calcular score
            score = self._calculate_score(
                title, description, members_count, keyword
            )
            
            return GroupCandidate(
                id=full_chat.id,
                username=username,
                title=title,
                members_count=members_count,
                description=description,
                language=language,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error creando candidato: {e}")
            return None
    
    def _detect_language(self, text: str) -> str:
        """Detecta idioma del grupo (simple)."""
        for lang, keywords in self.SEARCH_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return lang
        return "es"  # Default
    
    def _calculate_score(
        self,
        title: str,
        description: str,
        members_count: int,
        keyword: str
    ) -> float:
        """
        Calcula score de confianza del grupo (0-1).
        
        Factores:
        - Keyword en título/descripción
        - Cantidad de miembros
        - No contiene spam words
        """
        score = 0.5  # Base
        
        text_combined = f"{title} {description}".lower()
        
        # Keyword match
        if keyword.lower() in text_combined:
            score += 0.2
        
        # Miembros
        if members_count > 200:
            score += 0.2
        elif members_count > 50:
            score += 0.1
        else:
            score -= 0.1  # Grupos pequeños menos confiables
        
        # Spam detection
        spam_words = ["free", "gratis", "money", "dinero", "bitcoin", "crypto"]
        if any(spam in text_combined for spam in spam_words):
            score -= 0.3
        
        return max(0, min(1, score))


class GroupValidator:
    """Validador de grupos antes de unirse."""
    
    def __init__(self, client: TelegramClient):
        """
        Args:
            client: Cliente de Telethon
        """
        self.client = client
    
    async def validate_group(
        self,
        candidate: GroupCandidate,
        min_members: int = 50,
        check_activity: bool = True
    ) -> bool:
        """
        Valida grupo antes de unirse.
        
        Args:
            candidate: Grupo candidato
            min_members: Mínimo de miembros requeridos
            check_activity: Si verificar actividad reciente
            
        Returns:
            True si es válido
        """
        # Verificar miembros mínimos
        if candidate.members_count < min_members:
            logger.info(f"Grupo {candidate.title} rechazado: pocos miembros ({candidate.members_count})")
            return False
        
        # Verificar score mínimo
        if candidate.score < 0.4:
            logger.info(f"Grupo {candidate.title} rechazado: score bajo ({candidate.score:.2f})")
            return False
        
        # Verificar actividad reciente (si es posible)
        if check_activity:
            is_active = await self._check_activity(candidate)
            if not is_active:
                logger.info(f"Grupo {candidate.title} rechazado: inactivo")
                return False
        
        logger.info(f"Grupo {candidate.title} validado ✓")
        return True
    
    async def _check_activity(self, candidate: GroupCandidate) -> bool:
        """
        Verifica actividad reciente del grupo.
        
        Returns:
            True si hay mensajes recientes
        """
        try:
            # Obtener últimos mensajes
            messages = await self.client.get_messages(
                candidate.id,
                limit=10
            )
            
            if not messages:
                return False
            
            # Verificar que hay mensajes de últimas 24h
            now = datetime.utcnow()
            recent_messages = [
                m for m in messages
                if m.date and (now - m.date).total_seconds() < 86400
            ]
            
            return len(recent_messages) > 0
            
        except Exception as e:
            logger.error(f"Error verificando actividad: {e}")
            return True  # Asumir activo si falla la verificación


class AutoGroupJoiner:
    """
    Buscador y unidor automático de grupos.
    
    Características:
    - Busca grupos públicos de intercambio
    - Valida grupos antes de unirse
    - Rate-limit: 20 joins/día
    - Delays anti-ban: 30-90 min entre joins
    - Maneja CAPTCHAs
    """
    
    def __init__(
        self,
        client: TelegramClient,
        captcha_resolver: Optional[CaptchaResolver] = None,
        max_joins_per_day: int = 20
    ):
        """
        Args:
            client: Cliente de Telethon
            captcha_resolver: Resolver de CAPTCHAs
            max_joins_per_day: Máximo de joins por día
        """
        self.client = client
        self.searcher = GroupSearcher(client)
        self.validator = GroupValidator(client)
        self.captcha_resolver = captcha_resolver or CaptchaResolver(client)
        self.max_joins_per_day = max_joins_per_day
        
        # Track joins
        self.joined_today: List[datetime] = []
        self.joined_group_ids: Set[int] = set()
        
        # Stats
        self.stats = {
            "groups_searched": 0,
            "groups_validated": 0,
            "joins_attempted": 0,
            "joins_successful": 0,
            "joins_failed": 0,
            "captchas_encountered": 0
        }
        
        logger.info(f"AutoGroupJoiner inicializado (max {max_joins_per_day} joins/día)")
    
    def can_join_more_today(self) -> bool:
        """Verifica si se pueden hacer más joins hoy."""
        # Limpiar joins antiguos (>24h)
        now = datetime.utcnow()
        self.joined_today = [
            dt for dt in self.joined_today
            if (now - dt).total_seconds() < 86400
        ]
        
        return len(self.joined_today) < self.max_joins_per_day
    
    async def search_and_join_groups(
        self,
        languages: List[str] = ["es", "en", "pt"],
        max_groups: int = 10
    ) -> List[TelegramGroup]:
        """
        Busca y se une a grupos automáticamente.
        
        Args:
            languages: Idiomas a buscar
            max_groups: Máximo de grupos a unir
            
        Returns:
            Lista de TelegramGroup unidos
        """
        joined_groups = []
        
        # Recolectar keywords de todos los idiomas
        all_keywords = []
        for lang in languages:
            all_keywords.extend(self.searcher.SEARCH_KEYWORDS.get(lang, []))
        
        # Buscar grupos
        logger.info(f"Buscando grupos en {len(languages)} idiomas...")
        candidates = await self.searcher.search_groups(
            keywords=all_keywords[:10],  # Top 10 keywords
            limit=max_groups * 3  # Buscar más para filtrar
        )
        
        self.stats["groups_searched"] = len(candidates)
        
        # Validar y unirse
        for candidate in candidates:
            # Verificar si ya estamos en el grupo
            if candidate.id in self.joined_group_ids:
                logger.info(f"Ya miembro de {candidate.title}")
                continue
            
            # Verificar límite diario
            if not self.can_join_more_today():
                logger.info(f"Límite diario alcanzado ({len(self.joined_today)}/{self.max_joins_per_day})")
                break
            
            # Validar grupo
            is_valid = await self.validator.validate_group(candidate)
            if not is_valid:
                continue
            
            self.stats["groups_validated"] += 1
            
            # Intentar unirse
            group = await self.join_group(candidate)
            if group:
                joined_groups.append(group)
                
                if len(joined_groups) >= max_groups:
                    break
                
                # Delay entre joins (30-90 min)
                delay_minutes = random.randint(30, 90)
                logger.info(f"Esperando {delay_minutes} min antes del siguiente join...")
                await asyncio.sleep(delay_minutes * 60)
        
        logger.info(f"Join completado: {len(joined_groups)} grupos unidos")
        return joined_groups
    
    async def join_group(self, candidate: GroupCandidate) -> Optional[TelegramGroup]:
        """
        Se une a un grupo.
        
        Args:
            candidate: Grupo candidato
            
        Returns:
            TelegramGroup si exitoso
        """
        self.stats["joins_attempted"] += 1
        
        try:
            logger.info(f"Uniéndose a: {candidate.title} (@{candidate.username or candidate.id})")
            
            # Unirse
            if candidate.username:
                await self.client.join_channel(candidate.username)
            else:
                # Intentar con ID (menos confiable)
                await self.client.join_channel(candidate.id)
            
            # Verificar CAPTCHA
            has_captcha = await self.captcha_resolver.detect_captcha(candidate.id)
            if has_captcha:
                self.stats["captchas_encountered"] += 1
                logger.info(f"CAPTCHA detectado en {candidate.title}")
                
                # Intentar resolver
                solved = await self.captcha_resolver.solve_captcha(candidate.id)
                if not solved:
                    logger.warning(f"No se pudo resolver CAPTCHA en {candidate.title}")
                    return None
            
            # Registrar join exitoso
            self.joined_today.append(datetime.utcnow())
            self.joined_group_ids.add(candidate.id)
            self.stats["joins_successful"] += 1
            
            # Crear TelegramGroup
            group = TelegramGroup(
                id=0,  # Se asignará en BD
                telegram_id=candidate.id,
                name=candidate.title,
                username=candidate.username,
                language=candidate.language,
                member_count=candidate.members_count,
                is_active=True,
                efficiency_ratio=0.0,  # Se calculará con el tiempo
                joined_at=datetime.utcnow()
            )
            
            logger.info(f"Unido exitosamente a {candidate.title} ✓")
            return group
            
        except UserAlreadyParticipantError:
            logger.info(f"Ya eres miembro de {candidate.title}")
            self.joined_group_ids.add(candidate.id)
            return None
            
        except FloodWaitError as e:
            logger.warning(f"FloodWaitError: esperar {e.seconds}s")
            await asyncio.sleep(e.seconds)
            return None
            
        except Exception as e:
            logger.error(f"Error uniéndose a {candidate.title}: {e}")
            self.stats["joins_failed"] += 1
            return None
    
    async def monitor_new_groups(
        self,
        interval_hours: int = 24,
        languages: List[str] = ["es", "en", "pt"]
    ):
        """
        Loop de búsqueda continua de grupos nuevos.
        
        Args:
            interval_hours: Intervalo entre búsquedas
            languages: Idiomas a monitorear
        """
        logger.info(f"Iniciando monitoreo de grupos nuevos (cada {interval_hours}h)")
        
        while True:
            try:
                # Buscar y unirse
                await self.search_and_join_groups(
                    languages=languages,
                    max_groups=5  # Conservador en loop automático
                )
                
                # Esperar intervalo
                logger.info(f"Próxima búsqueda en {interval_hours}h")
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error en monitor_new_groups: {e}", exc_info=True)
                await asyncio.sleep(3600)  # Esperar 1h en caso de error
    
    def get_stats(self) -> dict:
        """Retorna estadísticas."""
        return {
            **self.stats,
            "joins_today": len(self.joined_today),
            "total_groups_joined": len(self.joined_group_ids),
            "can_join_more": self.can_join_more_today()
        }
