"""
Base Platform Client
Clase abstracta para clientes de plataformas satélite.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from app.satellites.models import (
    UploadRequest,
    UploadResponse,
    PlatformMetrics,
    SatelliteAccount
)
from app.satellites.config import SatelliteConfig

logger = logging.getLogger(__name__)


class BasePlatformClient(ABC):
    """
    Interfaz base para clientes de plataformas satélite.
    
    Todos los platform clients deben heredar esta clase e implementar
    los métodos abstractos.
    """
    
    def __init__(self, config: SatelliteConfig):
        """
        Inicializar cliente.
        
        Args:
            config: Configuración del Satellite Engine
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def upload_short(
        self,
        request: UploadRequest,
        account: SatelliteAccount
    ) -> UploadResponse:
        """
        Subir video short a la plataforma.
        
        Args:
            request: Request con video path, caption, tags, etc.
            account: Cuenta satélite a usar
            
        Returns:
            UploadResponse con resultado del upload
            
        Raises:
            UploadError: Si el upload falla
            QuotaExceededError: Si se exceden límites
        """
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        post_id: str,
        account: SatelliteAccount
    ) -> PlatformMetrics:
        """
        Obtener métricas de un post publicado.
        
        Args:
            post_id: ID del post en la plataforma
            account: Cuenta asociada al post
            
        Returns:
            PlatformMetrics con engagement data
        """
        pass
    
    @abstractmethod
    async def delete_post(
        self,
        post_id: str,
        account: SatelliteAccount
    ) -> bool:
        """
        Eliminar un post publicado.
        
        Args:
            post_id: ID del post en la plataforma
            account: Cuenta asociada al post
            
        Returns:
            True si eliminado exitosamente
        """
        pass
    
    @abstractmethod
    async def validate_account(
        self,
        account: SatelliteAccount
    ) -> bool:
        """
        Validar que la cuenta está activa y funcionando.
        
        Args:
            account: Cuenta a validar
            
        Returns:
            True si cuenta válida
        """
        pass
    
    def _check_safety_limits(
        self,
        account: SatelliteAccount
    ) -> tuple[bool, Optional[str]]:
        """
        Verificar límites de seguridad antes de upload.
        
        Args:
            account: Cuenta a verificar
            
        Returns:
            (puede_publicar, mensaje_error)
        """
        # Check daily limit
        if account.posts_today >= account.daily_post_limit:
            return False, f"Daily limit reached: {account.posts_today}/{account.daily_post_limit}"
        
        # Check time between posts
        if account.last_post_at:
            time_since_last = (datetime.utcnow() - account.last_post_at).total_seconds()
            min_time = self.config.min_time_between_posts_sec
            
            if time_since_last < min_time:
                return False, f"Too soon since last post: {time_since_last:.0f}s < {min_time}s"
        
        return True, None
    
    def _estimate_cost(self, request: UploadRequest) -> float:
        """
        Estimar coste del upload.
        
        Args:
            request: Upload request
            
        Returns:
            Coste estimado en EUR
        """
        # Base cost for upload API call
        base_cost = 0.01
        
        # Add cost for scheduled posts (requires storage)
        if request.schedule_time:
            base_cost += 0.005
        
        return base_cost
    
    async def _log_telemetry(
        self,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Log telemetry event.
        
        Args:
            event: Event name
            data: Event data
        """
        if not self.config.enable_telemetry:
            return
        
        self.logger.info(
            f"TELEMETRY [{event}]",
            extra={
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                **data
            }
        )
