"""
YouTube Live API Integration - Sprint 7C
Integración real con yt-dlp + YouTube Data API v3.

⚠️ MODO SEGURO ⚠️
- Delays 15-45s entre acciones
- Rotación de fingerprint
- Verificación de interacción recibida
- Circuit breaker en shadowban
"""
import asyncio
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime
import yt_dlp

from app.telegram_exchange_bot.security import SecurityContext, AntiShadowbanProtection

logger = logging.getLogger(__name__)


class YouTubeVideoMetadata:
    """Metadata de video de YouTube."""
    
    def __init__(self, data: Dict[str, Any]):
        self.video_id: str = data.get("id", "")
        self.title: str = data.get("title", "")
        self.channel: str = data.get("channel", "")
        self.channel_id: str = data.get("channel_id", "")
        self.views: int = data.get("view_count", 0)
        self.likes: int = data.get("like_count", 0)
        self.comments: int = data.get("comment_count", 0)
        self.duration: int = data.get("duration", 0)
        self.upload_date: str = data.get("upload_date", "")
        self.description: str = data.get("description", "")
        self.tags: list = data.get("tags", [])


class YouTubeLiveAPI:
    """
    API real de YouTube usando yt-dlp.
    
    Características:
    - Extracción de metadata (views, likes, comments)
    - Validación de URLs
    - Canonicalization de video IDs
    - Delays anti-shadowban
    - Circuit breaker
    """
    
    def __init__(self):
        """Inicializa YouTube Live API."""
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        
        # Stats
        self.stats = {
            "metadata_fetched": 0,
            "likes_executed": 0,
            "comments_executed": 0,
            "subscribes_executed": 0,
            "errors": 0
        }
        
        logger.info("YouTubeLiveAPI initialized")
    
    async def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrae video ID de URL de YouTube.
        
        Soporta:
        - https://youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID
        
        Args:
            url: URL del video
            
        Returns:
            Video ID o None si inválido
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_metadata(self, video_url: str) -> Optional[YouTubeVideoMetadata]:
        """
        Obtiene metadata de video usando yt-dlp.
        
        Args:
            video_url: URL del video
            
        Returns:
            YouTubeVideoMetadata o None si falla
        """
        try:
            video_id = await self.extract_video_id(video_url)
            if not video_id:
                logger.error(f"Invalid YouTube URL: {video_url}")
                return None
            
            # Ejecutar yt-dlp en thread pool (blocking I/O)
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._fetch_video_info,
                f"https://youtube.com/watch?v={video_id}"
            )
            
            if not info:
                return None
            
            metadata = YouTubeVideoMetadata(info)
            self.stats["metadata_fetched"] += 1
            
            logger.info(
                f"Fetched metadata: {metadata.title} "
                f"({metadata.views} views, {metadata.likes} likes)"
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching YouTube metadata: {e}")
            self.stats["errors"] += 1
            return None
    
    def _fetch_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch video info usando yt-dlp (blocking)."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None
    
    async def execute_like(
        self,
        video_url: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta like en video de YouTube.
        
        ⚠️ NOTA: Requiere sesión autenticada (cookies/oauth)
        Sprint 7C implementa validación, ejecución real pendiente de sesión.
        
        Args:
            video_url: URL del video
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            # 1. Validar video
            metadata = await self.get_video_metadata(video_url)
            if not metadata:
                return {
                    "success": False,
                    "error": "Invalid video URL or unavailable"
                }
            
            # 2. Apply anti-shadowban delay
            await AntiShadowbanProtection.apply_human_delay(
                operation="like",
                min_seconds=15,
                max_seconds=45
            )
            
            # 3. TODO: Ejecutar like real usando selenium + cookies
            # Por ahora, simulación con validación
            logger.info(
                f"[SIMULATED] YouTube LIKE: {metadata.title} "
                f"from {account_username} via {security_context.proxy_url}"
            )
            
            self.stats["likes_executed"] += 1
            
            return {
                "success": True,
                "video_id": metadata.video_id,
                "video_title": metadata.title,
                "channel": metadata.channel,
                "current_likes": metadata.likes,
                "simulated": True  # Cambiar a False cuando esté implementado
            }
            
        except Exception as e:
            logger.error(f"Error executing YouTube like: {e}")
            self.stats["errors"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_comment(
        self,
        video_url: str,
        comment_text: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta comentario en video de YouTube.
        
        Args:
            video_url: URL del video
            comment_text: Texto del comentario
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            metadata = await self.get_video_metadata(video_url)
            if not metadata:
                return {"success": False, "error": "Invalid video"}
            
            # Anti-shadowban delay (más largo para comentarios)
            await AntiShadowbanProtection.apply_human_delay(
                operation="comment",
                min_seconds=25,
                max_seconds=60
            )
            
            # TODO: Ejecutar comentario real
            logger.info(
                f"[SIMULATED] YouTube COMMENT: {metadata.title} "
                f"from {account_username}: '{comment_text[:30]}...'"
            )
            
            self.stats["comments_executed"] += 1
            
            return {
                "success": True,
                "video_id": metadata.video_id,
                "comment": comment_text,
                "simulated": True
            }
            
        except Exception as e:
            logger.error(f"Error executing YouTube comment: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    async def execute_subscribe(
        self,
        channel_url: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta suscripción a canal de YouTube.
        
        Args:
            channel_url: URL del canal
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            # Anti-shadowban delay
            await AntiShadowbanProtection.apply_human_delay(
                operation="subscribe",
                min_seconds=20,
                max_seconds=50
            )
            
            # TODO: Ejecutar suscripción real
            logger.info(
                f"[SIMULATED] YouTube SUBSCRIBE: {channel_url} "
                f"from {account_username}"
            )
            
            self.stats["subscribes_executed"] += 1
            
            return {
                "success": True,
                "channel_url": channel_url,
                "simulated": True
            }
            
        except Exception as e:
            logger.error(f"Error executing YouTube subscribe: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    async def verify_interaction_received(
        self,
        video_url: str,
        interaction_type: str,
        before_count: int
    ) -> bool:
        """
        Verifica si la interacción fue recibida.
        
        Args:
            video_url: URL del video
            interaction_type: "like", "comment", "subscribe"
            before_count: Count antes de la interacción
            
        Returns:
            True si se detectó aumento
        """
        try:
            # Wait para que YouTube procese
            await asyncio.sleep(5)
            
            metadata = await self.get_video_metadata(video_url)
            if not metadata:
                return False
            
            if interaction_type == "like":
                after_count = metadata.likes
            elif interaction_type == "comment":
                after_count = metadata.comments
            else:
                return False  # Subscribe no se puede verificar así
            
            return after_count > before_count
            
        except Exception as e:
            logger.error(f"Error verifying interaction: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna stats del API."""
        return {
            **self.stats,
            "api_name": "YouTubeLiveAPI",
            "mode": "live"
        }
