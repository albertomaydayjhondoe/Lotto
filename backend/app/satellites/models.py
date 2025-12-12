"""
Satellite Engine Models
Estructuras de datos para publicación multi-plataforma.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, validator


# Platform types
PlatformType = Literal["tiktok", "instagram", "youtube"]


class UploadRequest(BaseModel):
    """Request para subir video a plataforma satélite."""
    
    video_path: str = Field(..., description="Path al archivo de video")
    caption: str = Field(..., max_length=2200, description="Caption del post")
    tags: List[str] = Field(default_factory=list, description="Hashtags y tags")
    platform: PlatformType = Field(..., description="Plataforma destino")
    
    # Metadata
    account_id: str = Field(..., description="ID de cuenta satélite")
    content_id: Optional[str] = Field(None, description="ID del contenido original")
    
    # Advanced options
    schedule_time: Optional[datetime] = Field(None, description="Hora programada (UTC)")
    is_draft: bool = Field(False, description="Guardar como borrador")
    enable_comments: bool = Field(True, description="Permitir comentarios")
    enable_duet: bool = Field(True, description="Permitir duets (TikTok)")
    enable_stitch: bool = Field(True, description="Permitir stitch (TikTok)")
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validar formato de tags."""
        return [tag.lstrip("#") for tag in v]
    
    @validator("caption")
    def validate_caption(cls, v, values):
        """Validar caption según plataforma."""
        platform = values.get("platform")
        if platform == "tiktok" and len(v) > 2200:
            raise ValueError("TikTok caption max 2200 chars")
        if platform == "instagram" and len(v) > 2200:
            raise ValueError("Instagram caption max 2200 chars")
        if platform == "youtube" and len(v) > 5000:
            raise ValueError("YouTube description max 5000 chars")
        return v


class UploadResponse(BaseModel):
    """Response de upload exitoso."""
    
    success: bool = Field(..., description="Upload exitoso")
    platform: PlatformType = Field(..., description="Plataforma")
    post_id: Optional[str] = Field(None, description="ID del post en plataforma")
    post_url: Optional[str] = Field(None, description="URL pública del post")
    
    # Timing
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = Field(None, description="Programado para")
    
    # Metadata
    account_used: str = Field(..., description="Cuenta utilizada")
    content_id: Optional[str] = Field(None, description="ID contenido original")
    
    # Telemetry
    upload_duration_ms: float = Field(..., description="Duración del upload (ms)")
    cost_estimate: float = Field(0.0, description="Costo estimado (EUR)")
    
    # Error info (if any)
    error_message: Optional[str] = Field(None, description="Mensaje de error")
    retry_count: int = Field(0, description="Intentos de retry")


class PlatformMetrics(BaseModel):
    """Métricas de engagement por plataforma."""
    
    post_id: str = Field(..., description="ID del post")
    platform: PlatformType = Field(..., description="Plataforma")
    
    # Core metrics
    views: int = Field(0, ge=0, description="Visualizaciones")
    likes: int = Field(0, ge=0, description="Likes")
    comments: int = Field(0, ge=0, description="Comentarios")
    shares: int = Field(0, ge=0, description="Compartidos")
    saves: int = Field(0, ge=0, description="Guardados")
    
    # Engagement ratios
    engagement_rate: float = Field(0.0, ge=0.0, le=1.0, description="Tasa engagement")
    ctr: float = Field(0.0, ge=0.0, le=1.0, description="Click-through rate")
    
    # Retention
    avg_watch_time_sec: float = Field(0.0, ge=0.0, description="Tiempo promedio visto")
    completion_rate: float = Field(0.0, ge=0.0, le=1.0, description="% completado")
    rewatches: int = Field(0, ge=0, description="Re-visualizaciones")
    
    # Timestamps
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    post_published_at: Optional[datetime] = Field(None)


class SatelliteAccount(BaseModel):
    """Configuración de cuenta satélite."""
    
    account_id: str = Field(..., description="ID único de cuenta")
    platform: PlatformType = Field(..., description="Plataforma")
    username: str = Field(..., description="Username de la cuenta")
    
    # Status
    is_active: bool = Field(True, description="Cuenta activa")
    is_verified: bool = Field(False, description="Cuenta verificada")
    
    # Safety limits
    daily_post_limit: int = Field(5, ge=1, le=50, description="Límite diario posts")
    posts_today: int = Field(0, ge=0, description="Posts hoy")
    last_post_at: Optional[datetime] = Field(None, description="Último post")
    
    # Proxy/GoLogin config
    proxy_config: Optional[Dict[str, Any]] = Field(None, description="Config proxy")
    gologin_profile_id: Optional[str] = Field(None, description="GoLogin profile ID")
    
    # Credentials (encrypted in production)
    credentials: Dict[str, str] = Field(default_factory=dict, description="Auth data")
    
    # Performance
    success_rate: float = Field(1.0, ge=0.0, le=1.0, description="Tasa éxito uploads")
    total_uploads: int = Field(0, ge=0, description="Total uploads realizados")
    failed_uploads: int = Field(0, ge=0, description="Uploads fallidos")


class ScheduledPost(BaseModel):
    """Post programado para publicación."""
    
    schedule_id: str = Field(..., description="ID único del schedule")
    upload_request: UploadRequest = Field(..., description="Request de upload")
    
    # Timing
    scheduled_for: datetime = Field(..., description="Momento programado (UTC)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    status: Literal["pending", "processing", "completed", "failed", "cancelled"] = Field(
        "pending", description="Estado del scheduled post"
    )
    
    # Retry logic
    retry_count: int = Field(0, ge=0, description="Intentos realizados")
    max_retries: int = Field(3, ge=0, le=10, description="Máximo reintentos")
    
    # Results
    upload_response: Optional[UploadResponse] = Field(None, description="Response si completado")
    error_message: Optional[str] = Field(None, description="Error si falla")


class MetricsSnapshot(BaseModel):
    """Snapshot de métricas agregadas."""
    
    snapshot_id: str = Field(..., description="ID del snapshot")
    platform: PlatformType = Field(..., description="Plataforma")
    
    # Aggregated metrics
    total_posts: int = Field(0, ge=0, description="Total posts activos")
    total_views: int = Field(0, ge=0, description="Total views")
    total_engagement: int = Field(0, ge=0, description="Total interactions")
    
    avg_engagement_rate: float = Field(0.0, ge=0.0, le=1.0, description="Media engagement")
    avg_completion_rate: float = Field(0.0, ge=0.0, le=1.0, description="Media completion")
    
    # Time range
    from_date: datetime = Field(..., description="Fecha inicio")
    to_date: datetime = Field(..., description="Fecha fin")
    collected_at: datetime = Field(default_factory=datetime.utcnow)
