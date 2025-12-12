"""
Upload Scheduler
Programación inteligente de uploads con safe-posting.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

import logging
import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from app.satellites.models import (
    ScheduledPost,
    UploadRequest,
    UploadResponse,
    SatelliteAccount
)
from app.satellites.config import SatelliteConfig
from app.satellites.platforms import (
    TikTokClient,
    InstagramClient,
    YouTubeClient
)

logger = logging.getLogger(__name__)


class UploadScheduler:
    """
    Scheduler para uploads programados con safe-posting.
    
    Features:
    - Scheduling con timezone support
    - Rate limiting por cuenta
    - Retry logic automático
    - Best time to post (TODO Sprint 3 - ML integration)
    - Duplicate detection
    """
    
    def __init__(self, config: SatelliteConfig):
        """
        Inicializar scheduler.
        
        Args:
            config: Configuración del Satellite Engine
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform clients
        self.clients = {
            "tiktok": TikTokClient(config),
            "instagram": InstagramClient(config),
            "youtube": YouTubeClient(config),
        }
        
        # Scheduled posts queue
        self.scheduled_posts: List[ScheduledPost] = []
        
        # Active uploads tracking
        self.active_uploads: Dict[str, asyncio.Task] = {}
        
        # Post history for duplicate detection
        self.post_history: Dict[str, List[str]] = defaultdict(list)  # account_id -> [content_ids]
    
    async def schedule_upload(
        self,
        request: UploadRequest,
        account: SatelliteAccount,
        scheduled_for: Optional[datetime] = None
    ) -> ScheduledPost:
        """
        Programar un upload.
        
        Args:
            request: Upload request
            account: Cuenta a usar
            scheduled_for: Momento programado (None = inmediato)
            
        Returns:
            ScheduledPost con estado pending
        """
        # Generate schedule ID
        schedule_id = f"sched_{datetime.utcnow().timestamp()}"
        
        # Determine scheduled time
        if scheduled_for is None:
            scheduled_for = datetime.utcnow()
        elif scheduled_for < datetime.utcnow():
            raise ValueError("Cannot schedule in the past")
        
        # Check for duplicates
        if self._is_duplicate(request.content_id, account.account_id):
            self.logger.warning(
                f"Duplicate content detected: {request.content_id} for {account.account_id}"
            )
        
        # Create scheduled post
        scheduled_post = ScheduledPost(
            schedule_id=schedule_id,
            upload_request=request,
            scheduled_for=scheduled_for,
            max_retries=self.config.max_retries
        )
        
        # Add to queue
        self.scheduled_posts.append(scheduled_post)
        
        self.logger.info(
            f"Scheduled upload {schedule_id} for {scheduled_for.isoformat()}"
        )
        
        return scheduled_post
    
    async def process_scheduled_posts(self) -> None:
        """
        Procesar posts programados (ejecutar en background).
        
        Esta función debe ejecutarse continuamente en un background task.
        """
        self.logger.info("Starting scheduled posts processor")
        
        while True:
            try:
                now = datetime.utcnow()
                
                # Find posts ready to publish
                ready_posts = [
                    post for post in self.scheduled_posts
                    if post.status == "pending" and post.scheduled_for <= now
                ]
                
                # Process ready posts (respecting concurrent limit)
                for post in ready_posts:
                    if len(self.active_uploads) >= self.config.max_concurrent_uploads:
                        self.logger.debug("Max concurrent uploads reached, waiting...")
                        break
                    
                    # Update status
                    post.status = "processing"
                    
                    # Create upload task
                    task = asyncio.create_task(
                        self._execute_upload(post)
                    )
                    self.active_uploads[post.schedule_id] = task
                
                # Clean completed tasks
                completed_ids = [
                    sched_id for sched_id, task in self.active_uploads.items()
                    if task.done()
                ]
                for sched_id in completed_ids:
                    del self.active_uploads[sched_id]
                
                # Sleep before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler: {e}", exc_info=True)
                await asyncio.sleep(30)
    
    async def _execute_upload(
        self,
        scheduled_post: ScheduledPost
    ) -> None:
        """
        Ejecutar un upload programado con retry logic.
        
        Args:
            scheduled_post: Post a ejecutar
        """
        request = scheduled_post.upload_request
        
        # Get account (TODO: integrate with account manager)
        # For now, create mock account
        account = SatelliteAccount(
            account_id=request.account_id,
            platform=request.platform,
            username=f"stub_user_{request.account_id}"
        )
        
        # Get appropriate client
        client = self.clients.get(request.platform)
        if not client:
            self.logger.error(f"No client for platform: {request.platform}")
            scheduled_post.status = "failed"
            scheduled_post.error_message = f"Unsupported platform: {request.platform}"
            return
        
        # Retry loop
        for attempt in range(scheduled_post.max_retries + 1):
            try:
                self.logger.info(
                    f"Executing upload {scheduled_post.schedule_id} "
                    f"(attempt {attempt + 1}/{scheduled_post.max_retries + 1})"
                )
                
                # Execute upload
                response = await client.upload_short(request, account)
                
                # Update scheduled post
                scheduled_post.upload_response = response
                scheduled_post.retry_count = attempt
                
                if response.success:
                    scheduled_post.status = "completed"
                    self._add_to_history(request.content_id, account.account_id)
                    self.logger.info(f"Upload {scheduled_post.schedule_id} completed successfully")
                    return
                else:
                    scheduled_post.error_message = response.error_message
                    
            except Exception as e:
                self.logger.error(
                    f"Upload {scheduled_post.schedule_id} failed (attempt {attempt + 1}): {e}",
                    exc_info=True
                )
                scheduled_post.error_message = str(e)
            
            # Retry delay if not last attempt
            if attempt < scheduled_post.max_retries:
                await asyncio.sleep(self.config.retry_delay_sec)
        
        # All retries failed
        scheduled_post.status = "failed"
        self.logger.error(
            f"Upload {scheduled_post.schedule_id} failed after "
            f"{scheduled_post.max_retries + 1} attempts"
        )
    
    def get_scheduled_posts(
        self,
        status: Optional[str] = None
    ) -> List[ScheduledPost]:
        """
        Obtener posts programados.
        
        Args:
            status: Filtrar por status (None = todos)
            
        Returns:
            Lista de ScheduledPost
        """
        if status:
            return [p for p in self.scheduled_posts if p.status == status]
        return self.scheduled_posts
    
    def cancel_scheduled_post(
        self,
        schedule_id: str
    ) -> bool:
        """
        Cancelar un post programado.
        
        Args:
            schedule_id: ID del post a cancelar
            
        Returns:
            True si cancelado exitosamente
        """
        for post in self.scheduled_posts:
            if post.schedule_id == schedule_id:
                if post.status in ["pending", "processing"]:
                    post.status = "cancelled"
                    self.logger.info(f"Cancelled scheduled post {schedule_id}")
                    return True
                else:
                    self.logger.warning(
                        f"Cannot cancel post {schedule_id} with status {post.status}"
                    )
                    return False
        
        return False
    
    def _is_duplicate(
        self,
        content_id: Optional[str],
        account_id: str
    ) -> bool:
        """
        Verificar si el contenido ya fue publicado en esta cuenta.
        
        Args:
            content_id: ID del contenido
            account_id: ID de la cuenta
            
        Returns:
            True si es duplicado
        """
        if not content_id:
            return False
        
        return content_id in self.post_history[account_id]
    
    def _add_to_history(
        self,
        content_id: Optional[str],
        account_id: str
    ) -> None:
        """
        Agregar contenido al historial de publicaciones.
        
        Args:
            content_id: ID del contenido
            account_id: ID de la cuenta
        """
        if content_id:
            self.post_history[account_id].append(content_id)
            
            # Keep only last 1000 entries per account
            if len(self.post_history[account_id]) > 1000:
                self.post_history[account_id] = self.post_history[account_id][-1000:]
