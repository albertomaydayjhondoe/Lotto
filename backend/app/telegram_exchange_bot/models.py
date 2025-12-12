"""
📊 MODELOS DE DATOS - TELEGRAM EXCHANGE BOT
Sprint 7: Sistema de intercambio multiplataforma

Modelos para tracking de intercambios, grupos, usuarios y métricas.

Autor: STAKAZO Development Team
Fecha: Diciembre 2025
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS - Definiciones de tipos
# ============================================================================

class Platform(str, Enum):
    """Plataformas soportadas para intercambio."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class InteractionType(str, Enum):
    """Tipos de interacciones posibles."""
    # YouTube
    YOUTUBE_LIKE = "youtube_like"
    YOUTUBE_COMMENT = "youtube_comment"
    YOUTUBE_SUBSCRIBE = "youtube_subscribe"
    YOUTUBE_VIEW = "youtube_view"  # 30-60s mínimo
    
    # Instagram
    INSTAGRAM_LIKE = "instagram_like"
    INSTAGRAM_SAVE = "instagram_save"
    INSTAGRAM_COMMENT = "instagram_comment"
    INSTAGRAM_FOLLOW = "instagram_follow"
    INSTAGRAM_STORY_MENTION = "instagram_story_mention"
    INSTAGRAM_POST_MENTION = "instagram_post_mention"
    
    # TikTok
    TIKTOK_LIKE = "tiktok_like"
    TIKTOK_COMMENT = "tiktok_comment"
    TIKTOK_FOLLOW = "tiktok_follow"
    TIKTOK_SHARE = "tiktok_share"


class MessageStatus(str, Enum):
    """Estados de mensajes detectados."""
    DETECTED = "detected"  # Link detectado
    QUEUED = "queued"  # En cola para apoyo
    PROCESSING = "processing"  # Ejecutando apoyo
    COMPLETED = "completed"  # Apoyo completado
    FAILED = "failed"  # Falló
    SKIPPED = "skipped"  # Saltado (no cumple criterios)


class AccountRole(str, Enum):
    """Roles de cuentas en el sistema."""
    OFFICIAL = "official"  # Cuenta oficial del artista (NUNCA usada por bot)
    SUPPORT = "support"  # Cuenta de apoyo no oficial
    FANPAGE = "fanpage"  # Fanpage satélite
    EXCHANGE = "exchange"  # Cuenta exclusiva para intercambios


class PriorityLevel(int, Enum):
    """Niveles de prioridad para contenido."""
    CRITICAL = 1  # Lanzamiento nuevo
    HIGH = 2  # Microoportunidad detectada
    MEDIUM = 3  # Contenido regular de última publicación
    LOW = 4  # Contenido satélite de apoyo


# ============================================================================
# MODELOS DE BASE DE DATOS
# ============================================================================

class TelegramGroup(BaseModel):
    """Grupo de Telegram monitoreado."""
    group_id: str = Field(..., description="ID único del grupo")
    group_name: str
    group_username: Optional[str] = None
    
    # Estado
    is_active: bool = True
    is_monitored: bool = True
    
    # Métricas
    members_count: Optional[int] = None
    message_count: int = 0
    exchange_count: int = 0
    
    # Eficiencia
    support_given: int = 0  # Apoyos dados por nosotros
    support_received: int = 0  # Apoyos recibidos
    efficiency_ratio: float = 0.0  # support_received / support_given
    
    # ROI
    avg_response_time_minutes: Optional[float] = None
    active_users_count: int = 0
    
    # Control de límites
    daily_messages_sent: int = 0
    last_message_at: Optional[datetime] = None
    
    # Metadata
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": "-1001234567890",
                "group_name": "Apoyo Mutuo Artistas",
                "is_active": True,
                "efficiency_ratio": 1.2,
                "support_given": 50,
                "support_received": 60
            }
        }


class TelegramUser(BaseModel):
    """Usuario de Telegram en grupos de apoyo."""
    user_id: str = Field(..., description="ID de Telegram")
    username: Optional[str] = None
    first_name: Optional[str] = None
    
    # Estado
    is_active: bool = True
    is_trusted: bool = False  # Usuario que cumple consistentemente
    is_blocked: bool = False  # Usuario que no cumple
    
    # Métricas de intercambio
    exchanges_completed: int = 0
    exchanges_failed: int = 0
    success_rate: float = 0.0
    
    # Tracking
    support_given: int = 0
    support_received: int = 0
    
    # Análisis de valor
    avg_interaction_quality: float = 0.0  # 0-1
    response_time_avg_minutes: Optional[float] = None
    
    # Trust score
    trust_score: float = 0.5  # 0-1, empieza en 0.5
    
    # Metadata
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123456789",
                "username": "musicfan99",
                "is_trusted": True,
                "success_rate": 0.85,
                "trust_score": 0.9
            }
        }


class ExchangeMessage(BaseModel):
    """Mensaje de intercambio detectado."""
    message_id: str = Field(..., description="ID único del mensaje")
    
    # Contexto
    group_id: str
    user_id: str
    
    # Contenido
    message_text: str
    detected_platform: Platform
    detected_url: str
    
    # Clasificación
    status: MessageStatus = MessageStatus.DETECTED
    priority: Optional[PriorityLevel] = None
    
    # Decisión del bot
    should_support: bool = False
    support_reason: Optional[str] = None
    skip_reason: Optional[str] = None
    
    # Tracking de ejecución
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resultados
    interactions_executed: List[InteractionType] = []
    success: bool = False
    error_message: Optional[str] = None
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_12345",
                "group_id": "-1001234567890",
                "user_id": "987654321",
                "detected_platform": "youtube",
                "detected_url": "https://youtube.com/watch?v=abc123",
                "status": "queued",
                "should_support": True
            }
        }


class ExchangeInteraction(BaseModel):
    """Interacción individual ejecutada."""
    interaction_id: str = Field(..., description="ID único")
    
    # Contexto
    exchange_message_id: str
    group_id: str
    target_user_id: str  # Usuario al que apoyamos
    
    # Tipo
    interaction_type: InteractionType
    platform: Platform
    target_url: str
    
    # Ejecución
    account_used: str  # ID de cuenta de apoyo usada
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Resultado
    success: bool
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    execution_time_seconds: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "interaction_id": "int_12345",
                "exchange_message_id": "msg_12345",
                "interaction_type": "youtube_like",
                "platform": "youtube",
                "target_url": "https://youtube.com/watch?v=abc123",
                "account_used": "support_account_1",
                "success": True
            }
        }


class OurContent(BaseModel):
    """Contenido nuestro para promocionar."""
    content_id: str = Field(..., description="ID único del contenido")
    
    # Tipo
    platform: Platform
    url: str
    
    # Clasificación
    priority: PriorityLevel
    is_launch: bool = False  # True si es lanzamiento nuevo
    
    # Descripción
    title: str
    description: Optional[str] = None
    
    # Estrategia
    target_interactions: List[InteractionType]
    target_count: int = 100  # Meta de interacciones
    current_count: int = 0
    
    # Role assignment
    account_roles_allowed: List[AccountRole] = [AccountRole.SUPPORT, AccountRole.FANPAGE]
    
    # Temporalidad
    active_from: datetime = Field(default_factory=datetime.utcnow)
    active_until: Optional[datetime] = None
    is_active: bool = True
    
    # Resultados
    total_supports_received: int = 0
    total_groups_promoted: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "orchestrator"
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "content_12345",
                "platform": "youtube",
                "url": "https://youtube.com/watch?v=xyz789",
                "priority": 1,
                "is_launch": True,
                "title": "Nuevo videoclip - Estrellas",
                "target_interactions": ["youtube_like", "youtube_comment", "youtube_subscribe"],
                "target_count": 500
            }
        }


# ============================================================================
# MODELOS DE CONFIGURACIÓN
# ============================================================================

class BotConfig(BaseModel):
    """Configuración del bot."""
    # Límites de seguridad
    max_groups_monitored: int = 200
    max_messages_per_group_per_day: int = 10
    max_interactions_per_hour: int = 50
    
    # Delays anti-spam
    min_delay_seconds: int = 3
    max_delay_seconds: int = 20
    
    # Prioridades
    youtube_priority_multiplier: float = 1.5
    instagram_priority_multiplier: float = 1.0
    fanpage_priority_multiplier: float = 0.7
    
    # Eficiencia
    min_group_efficiency_ratio: float = 0.3  # Mínimo 30% de retorno
    min_user_trust_score: float = 0.3
    
    # Gemini
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.8  # Creatividad para mensajes
    
    # Modo
    mode: str = "live"  # "live" o "stub"
    manual_approval: bool = False  # Si True, requiere aprobación manual
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_groups_monitored": 200,
                "max_messages_per_group_per_day": 10,
                "youtube_priority_multiplier": 1.5,
                "mode": "live"
            }
        }


# ============================================================================
# MODELOS DE RESPUESTA
# ============================================================================

class ExchangeStats(BaseModel):
    """Estadísticas del sistema de intercambio."""
    # Grupos
    total_groups: int
    active_groups: int
    avg_group_efficiency: float
    
    # Usuarios
    total_users: int
    trusted_users: int
    blocked_users: int
    
    # Intercambios
    total_exchanges: int
    successful_exchanges: int
    failed_exchanges: int
    success_rate: float
    
    # Interacciones
    total_interactions: int
    interactions_today: int
    interactions_this_week: int
    
    # ROI
    support_given: int
    support_received: int
    global_efficiency_ratio: float
    
    # Temporal
    period_start: datetime
    period_end: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_groups": 50,
                "active_groups": 45,
                "success_rate": 0.82,
                "global_efficiency_ratio": 1.15
            }
        }


class BotStatus(BaseModel):
    """Estado del bot."""
    is_running: bool
    mode: str
    uptime_hours: float
    
    # Aislamiento
    isolation_configured: bool
    proxy_status: str
    fingerprint_status: str
    
    # Límites
    groups_monitored: int
    interactions_today: int
    rate_limit_remaining: int
    
    # Última actividad
    last_message_processed: Optional[datetime] = None
    last_interaction_executed: Optional[datetime] = None
    
    # Errores
    errors_last_hour: int
    last_error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "mode": "live",
                "isolation_configured": True,
                "groups_monitored": 45,
                "interactions_today": 127
            }
        }
