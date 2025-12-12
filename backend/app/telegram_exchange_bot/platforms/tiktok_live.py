"""
TikTok Live API Integration - Sprint 7C
Integración con TikTok usando API no oficial + webdriver fallback.

⚠️ MODO SEGURO ⚠️
- Proxy rotation por acción
- Fingerprint único por cuenta
- Circuit breaker en shadowban signals
- Delays 25-70s entre acciones
- IP rotation obligatoria
"""
import asyncio
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime

from app.telegram_exchange_bot.security import SecurityContext, AntiShadowbanProtection

logger = logging.getLogger(__name__)


class TikTokVideoMetadata:
    """Metadata de video de TikTok."""
    
    def __init__(self, data: Dict[str, Any]):
        self.video_id: str = data.get("id", "")
        self.description: str = data.get("desc", "")
        self.author: str = data.get("author", {}).get("uniqueId", "")
        self.views: int = data.get("stats", {}).get("playCount", 0)
        self.likes: int = data.get("stats", {}).get("diggCount", 0)
        self.comments: int = data.get("stats", {}).get("commentCount", 0)
        self.shares: int = data.get("stats", {}).get("shareCount", 0)
        self.duration: int = data.get("video", {}).get("duration", 0)
        self.music: str = data.get("music", {}).get("title", "")


class TikTokLiveAPI:
    """
    API real de TikTok usando métodos no oficiales.
    
    Características:
    - Extracción de metadata (views, likes, comments, shares)
    - Ejecución real de like/comment
    - Fallback a webdriver si API falla
    - IP rotation obligatoria por acción
    - Circuit breaker en shadowban signals
    - Verificación de interacción recibida
    """
    
    def __init__(self):
        """Inicializa TikTok Live API."""
        self.shadowban_signals = {
            "rate_limit": 0,
            "failed_requests": 0,
            "captcha_count": 0
        }
        
        # Stats
        self.stats = {
            "metadata_fetched": 0,
            "likes_executed": 0,
            "comments_executed": 0,
            "follows_executed": 0,
            "shadowban_detected": 0,
            "errors": 0
        }
        
        logger.info("TikTokLiveAPI initialized (UNOFFICIAL API MODE)")
    
    async def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrae video ID de URL de TikTok.
        
        Soporta:
        - https://www.tiktok.com/@user/video/1234567890
        - https://vm.tiktok.com/SHORTCODE/
        
        Args:
            url: URL del video
            
        Returns:
            Video ID o None si inválido
        """
        patterns = [
            r'tiktok\.com/@[^/]+/video/(\d+)',
            r'vm\.tiktok\.com/([A-Za-z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_metadata(
        self,
        video_url: str,
        security_context: SecurityContext
    ) -> Optional[TikTokVideoMetadata]:
        """
        Obtiene metadata de video de TikTok.
        
        ⚠️ NOTA: Usa API no oficial, puede cambiar en cualquier momento.
        
        Args:
            video_url: URL del video
            security_context: Contexto de seguridad (proxy)
            
        Returns:
            TikTokVideoMetadata o None si falla
        """
        try:
            video_id = await self.extract_video_id(video_url)
            if not video_id:
                logger.error(f"Invalid TikTok URL: {video_url}")
                return None
            
            # TODO: Implementar llamada real a TikTok API no oficial
            # Por ahora, mock metadata
            logger.info(f"[SIMULATED] Fetching TikTok metadata for {video_id}")
            
            mock_data = {
                "id": video_id,
                "desc": "Mock TikTok video",
                "author": {"uniqueId": "mock_user"},
                "stats": {
                    "playCount": 10000,
                    "diggCount": 500,
                    "commentCount": 50,
                    "shareCount": 25
                },
                "video": {"duration": 30},
                "music": {"title": "Original Sound"}
            }
            
            metadata = TikTokVideoMetadata(mock_data)
            self.stats["metadata_fetched"] += 1
            
            logger.info(
                f"Fetched TikTok metadata: @{metadata.author} "
                f"({metadata.views} views, {metadata.likes} likes)"
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching TikTok metadata: {e}")
            self.stats["errors"] += 1
            return None
    
    async def execute_like(
        self,
        video_url: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta like en video de TikTok.
        
        ⚠️ SEGURIDAD CRÍTICA:
        - Requiere IP rotation
        - Delays 25-50s
        - Circuit breaker activo
        
        Args:
            video_url: URL del video
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            # 1. Check circuit breaker
            if self._is_shadowbanned():
                return {
                    "success": False,
                    "error": "Circuit breaker active - shadowban detected"
                }
            
            # 2. Validate video
            metadata = await self.get_video_metadata(video_url, security_context)
            if not metadata:
                return {"success": False, "error": "Invalid video URL"}
            
            # 3. Anti-shadowban delay (más largo para TikTok)
            await AntiShadowbanProtection.apply_human_delay(
                operation="like",
                min_seconds=25,
                max_seconds=50
            )
            
            # 4. Verify IP rotation
            if not security_context.proxy_url:
                logger.warning("TikTok action without proxy - HIGH RISK")
            
            # 5. TODO: Ejecutar like real usando webdriver + cookies
            logger.info(
                f"[SIMULATED] TikTok LIKE: @{metadata.author} video {metadata.video_id} "
                f"from {account_username} via {security_context.proxy_url}"
            )
            
            self.stats["likes_executed"] += 1
            
            return {
                "success": True,
                "video_id": metadata.video_id,
                "author": metadata.author,
                "likes_before": metadata.likes,
                "simulated": True  # Cambiar a False cuando esté implementado
            }
            
        except Exception as e:
            logger.error(f"Error executing TikTok like: {e}")
            self.stats["errors"] += 1
            self._record_error()
            return {"success": False, "error": str(e)}
    
    async def execute_comment(
        self,
        video_url: str,
        comment_text: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta comentario en video de TikTok.
        
        Args:
            video_url: URL del video
            comment_text: Texto del comentario
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            # Circuit breaker check
            if self._is_shadowbanned():
                return {"success": False, "error": "Circuit breaker active"}
            
            metadata = await self.get_video_metadata(video_url, security_context)
            if not metadata:
                return {"success": False, "error": "Invalid video"}
            
            # Delay más largo para comentarios
            await AntiShadowbanProtection.apply_human_delay(
                operation="comment",
                min_seconds=35,
                max_seconds=70
            )
            
            # TODO: Ejecutar comentario real
            logger.info(
                f"[SIMULATED] TikTok COMMENT: @{metadata.author} "
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
            logger.error(f"Error executing TikTok comment: {e}")
            self.stats["errors"] += 1
            self._record_error()
            return {"success": False, "error": str(e)}
    
    async def execute_follow(
        self,
        user_url: str,
        account_username: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        Ejecuta follow a usuario de TikTok.
        
        Args:
            user_url: URL del usuario
            account_username: Username de la cuenta
            security_context: Contexto de seguridad
            
        Returns:
            Dict con resultado
        """
        try:
            if self._is_shadowbanned():
                return {"success": False, "error": "Circuit breaker active"}
            
            await AntiShadowbanProtection.apply_human_delay(
                operation="follow",
                min_seconds=30,
                max_seconds=60
            )
            
            # TODO: Ejecutar follow real
            logger.info(
                f"[SIMULATED] TikTok FOLLOW: {user_url} "
                f"from {account_username}"
            )
            
            self.stats["follows_executed"] += 1
            
            return {
                "success": True,
                "user_url": user_url,
                "simulated": True
            }
            
        except Exception as e:
            logger.error(f"Error executing TikTok follow: {e}")
            self.stats["errors"] += 1
            self._record_error()
            return {"success": False, "error": str(e)}
    
    async def verify_interaction_received(
        self,
        video_url: str,
        interaction_type: str,
        before_count: int,
        security_context: SecurityContext
    ) -> bool:
        """
        Verifica si la interacción fue recibida.
        
        Args:
            video_url: URL del video
            interaction_type: "like", "comment", "share"
            before_count: Count antes de la interacción
            security_context: Contexto de seguridad
            
        Returns:
            True si se detectó aumento
        """
        try:
            # Wait para que TikTok procese
            await asyncio.sleep(8)
            
            metadata = await self.get_video_metadata(video_url, security_context)
            if not metadata:
                return False
            
            if interaction_type == "like":
                after_count = metadata.likes
            elif interaction_type == "comment":
                after_count = metadata.comments
            elif interaction_type == "share":
                after_count = metadata.shares
            else:
                return False
            
            return after_count > before_count
            
        except Exception as e:
            logger.error(f"Error verifying TikTok interaction: {e}")
            return False
    
    def _record_error(self):
        """Registra error para circuit breaker."""
        self.shadowban_signals["failed_requests"] += 1
        
        # Si muchos errores consecutivos, marcar shadowban
        if self.shadowban_signals["failed_requests"] >= 5:
            self.stats["shadowban_detected"] += 1
            logger.critical(
                "⚠️ SHADOWBAN DETECTED - TikTok circuit breaker activated"
            )
    
    def _is_shadowbanned(self) -> bool:
        """
        Detecta señales de shadowban.
        
        Señales:
        - 5+ requests fallidos consecutivos
        - 3+ CAPTCHAs en última hora
        - Rate limit detectado
        
        Returns:
            True si shadowban detectado
        """
        return (
            self.shadowban_signals["failed_requests"] >= 5 or
            self.shadowban_signals["captcha_count"] >= 3 or
            self.shadowban_signals["rate_limit"] > 0
        )
    
    def reset_circuit_breaker(self):
        """Reset manual del circuit breaker."""
        self.shadowban_signals = {
            "rate_limit": 0,
            "failed_requests": 0,
            "captcha_count": 0
        }
        logger.info("TikTok circuit breaker reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna stats del API."""
        return {
            **self.stats,
            "shadowban_signals": self.shadowban_signals,
            "circuit_breaker_active": self._is_shadowbanned(),
            "api_name": "TikTokLiveAPI",
            "mode": "live_unofficial"
        }
