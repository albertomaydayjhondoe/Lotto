"""
TikTok Platform Client
Cliente para uploads a TikTok (STUB MODE - Sprint 2).

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime

from app.satellites.platforms.base_client import BasePlatformClient
from app.satellites.models import (
    UploadRequest,
    UploadResponse,
    PlatformMetrics,
    SatelliteAccount
)
from app.satellites.config import SatelliteConfig

logger = logging.getLogger(__name__)


class TikTokClient(BasePlatformClient):
    """
    Cliente para uploads a TikTok.
    
    STUB MODE (Sprint 2):
    - Simula uploads exitosos
    - Retorna responses mock
    - Incluye telemetría y cost tracking
    
    TODO Sprint 3:
    - Integrar TikTok API real
    - Implementar OAuth flow
    - Upload real de videos
    """
    
    def __init__(self, config: SatelliteConfig):
        """Inicializar TikTok client."""
        super().__init__(config)
        self.platform = "tiktok"
        self.api_base_url = "https://open-api.tiktok.com"  # Placeholder
    
    async def upload_short(
        self,
        request: UploadRequest,
        account: SatelliteAccount
    ) -> UploadResponse:
        """
        Subir video short a TikTok.
        
        STUB MODE: Simula upload exitoso con delay.
        """
        start_time = datetime.utcnow()
        
        # Validate platform
        if request.platform != "tiktok":
            raise ValueError(f"Invalid platform: {request.platform}, expected tiktok")
        
        # Check safety limits
        can_post, error_msg = self._check_safety_limits(account)
        if not can_post:
            self.logger.warning(f"Safety limit check failed: {error_msg}")
            return UploadResponse(
                success=False,
                platform="tiktok",
                account_used=account.account_id,
                content_id=request.content_id,
                upload_duration_ms=0.0,
                cost_estimate=0.0,
                error_message=error_msg
            )
        
        # Estimate cost
        cost = self._estimate_cost(request)
        
        # Log telemetry
        await self._log_telemetry("upload_start", {
            "platform": "tiktok",
            "account_id": account.account_id,
            "content_id": request.content_id,
            "dry_run": self.config.dry_run
        })
        
        # STUB: Simulate upload with delay
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Simulating TikTok upload for account {account.username}")
            await asyncio.sleep(0.5)  # Simulate API call
            post_id = f"tiktok_stub_{datetime.utcnow().timestamp()}"
            post_url = f"https://www.tiktok.com/@{account.username}/video/{post_id}"
        else:
            # TODO Sprint 3: Real TikTok API integration
            self.logger.info(f"[STUB] TikTok upload for {account.username}")
            await asyncio.sleep(1.0)
            post_id = f"tiktok_stub_{datetime.utcnow().timestamp()}"
            post_url = f"https://www.tiktok.com/@{account.username}/video/{post_id}"
        
        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log telemetry
        await self._log_telemetry("upload_complete", {
            "platform": "tiktok",
            "account_id": account.account_id,
            "post_id": post_id,
            "duration_ms": duration_ms,
            "cost": cost,
            "success": True
        })
        
        return UploadResponse(
            success=True,
            platform="tiktok",
            post_id=post_id,
            post_url=post_url,
            uploaded_at=datetime.utcnow(),
            scheduled_for=request.schedule_time,
            account_used=account.account_id,
            content_id=request.content_id,
            upload_duration_ms=duration_ms,
            cost_estimate=cost
        )
    
    async def get_metrics(
        self,
        post_id: str,
        account: SatelliteAccount
    ) -> PlatformMetrics:
        """
        Obtener métricas de post TikTok.
        
        STUB MODE: Retorna métricas simuladas.
        """
        self.logger.info(f"[STUB] Getting TikTok metrics for {post_id}")
        
        # STUB: Return mock metrics
        return PlatformMetrics(
            post_id=post_id,
            platform="tiktok",
            views=15000,
            likes=1200,
            comments=85,
            shares=320,
            saves=150,
            engagement_rate=0.117,  # (1200+85+320+150)/15000
            ctr=0.023,
            avg_watch_time_sec=12.5,
            completion_rate=0.65,
            rewatches=450,
            collected_at=datetime.utcnow()
        )
    
    async def delete_post(
        self,
        post_id: str,
        account: SatelliteAccount
    ) -> bool:
        """
        Eliminar post de TikTok.
        
        STUB MODE: Simula eliminación exitosa.
        """
        self.logger.info(f"[STUB] Deleting TikTok post {post_id}")
        await asyncio.sleep(0.5)
        return True
    
    async def validate_account(
        self,
        account: SatelliteAccount
    ) -> bool:
        """
        Validar cuenta TikTok.
        
        STUB MODE: Siempre retorna True.
        """
        self.logger.info(f"[STUB] Validating TikTok account {account.username}")
        await asyncio.sleep(0.3)
        return True
