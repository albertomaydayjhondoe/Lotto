"""
Satellite Engine Configuration
Configuración de límites, quotas y plataformas.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SatelliteConfig(BaseModel):
    """Configuración del Satellite Engine."""
    
    # Cost limits (EUR)
    max_cost_per_upload: float = Field(
        default=0.02,
        ge=0.0,
        description="Máximo coste por upload (EUR)"
    )
    max_daily_cost: float = Field(
        default=1.0,
        ge=0.0,
        description="Máximo coste diario total (EUR)"
    )
    max_monthly_cost: float = Field(
        default=10.0,
        ge=0.0,
        description="Máximo coste mensual (EUR)"
    )
    
    # Upload limits
    max_concurrent_uploads: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Máximo uploads concurrentes"
    )
    upload_timeout_sec: int = Field(
        default=300,
        ge=60,
        le=600,
        description="Timeout por upload (segundos)"
    )
    
    # Retry logic
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Máximo reintentos por upload"
    )
    retry_delay_sec: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Delay entre reintentos (segundos)"
    )
    
    # Safety - rate limiting
    daily_post_limit_per_account: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Límite diario posts por cuenta"
    )
    min_time_between_posts_sec: int = Field(
        default=1800,  # 30 minutes
        ge=300,
        le=7200,
        description="Tiempo mínimo entre posts (segundos)"
    )
    
    # Platform configs
    enable_tiktok: bool = Field(True, description="Habilitar TikTok")
    enable_instagram: bool = Field(True, description="Habilitar Instagram")
    enable_youtube: bool = Field(True, description="Habilitar YouTube Shorts")
    
    # Telemetry
    enable_telemetry: bool = Field(True, description="Habilitar telemetría")
    enable_metrics_collection: bool = Field(True, description="Recoger métricas engagement")
    metrics_collection_interval_sec: int = Field(
        default=3600,  # 1 hour
        ge=300,
        le=86400,
        description="Intervalo recogida métricas (segundos)"
    )
    
    # GoLogin / Account Management
    enable_gologin: bool = Field(False, description="Usar GoLogin para cuentas")
    gologin_api_token: Optional[str] = Field(None, description="Token API GoLogin")
    
    # Proxy settings
    use_proxies: bool = Field(False, description="Usar proxies para uploads")
    proxy_rotation: bool = Field(False, description="Rotar proxies automáticamente")
    
    # Storage
    video_storage_path: str = Field(
        default="/tmp/satellite_uploads",
        description="Path temporal para videos"
    )
    keep_uploaded_videos: bool = Field(
        False,
        description="Mantener videos tras upload"
    )
    
    # Debug
    dry_run: bool = Field(
        False,
        description="Modo dry-run (simular uploads sin publicar)"
    )
    debug_mode: bool = Field(
        False,
        description="Modo debug con logging verbose"
    )
    
    @classmethod
    def from_env(cls) -> "SatelliteConfig":
        """Cargar config desde environment variables."""
        return cls(
            max_cost_per_upload=float(os.getenv("SATELLITE_MAX_COST_PER_UPLOAD", "0.02")),
            max_daily_cost=float(os.getenv("SATELLITE_MAX_DAILY_COST", "1.0")),
            max_monthly_cost=float(os.getenv("SATELLITE_MAX_MONTHLY_COST", "10.0")),
            max_concurrent_uploads=int(os.getenv("SATELLITE_MAX_CONCURRENT", "3")),
            daily_post_limit_per_account=int(os.getenv("SATELLITE_DAILY_LIMIT", "5")),
            enable_tiktok=os.getenv("SATELLITE_ENABLE_TIKTOK", "true").lower() == "true",
            enable_instagram=os.getenv("SATELLITE_ENABLE_INSTAGRAM", "true").lower() == "true",
            enable_youtube=os.getenv("SATELLITE_ENABLE_YOUTUBE", "true").lower() == "true",
            enable_gologin=os.getenv("SATELLITE_ENABLE_GOLOGIN", "false").lower() == "true",
            gologin_api_token=os.getenv("GOLOGIN_API_TOKEN"),
            dry_run=os.getenv("SATELLITE_DRY_RUN", "false").lower() == "true",
            debug_mode=os.getenv("SATELLITE_DEBUG", "false").lower() == "true",
        )
    
    def get_cost_limits(self) -> Dict[str, float]:
        """Retornar límites de coste como dict."""
        return {
            "per_upload": self.max_cost_per_upload,
            "daily": self.max_daily_cost,
            "monthly": self.max_monthly_cost,
        }
    
    def get_platform_status(self) -> Dict[str, bool]:
        """Retornar estado de plataformas habilitadas."""
        return {
            "tiktok": self.enable_tiktok,
            "instagram": self.enable_instagram,
            "youtube": self.enable_youtube,
        }
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
