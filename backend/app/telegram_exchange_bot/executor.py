"""
Interaction Executor - Sprint 7B
Ejecutor de interacciones reales desde cuentas NO oficiales.

⚠️ REGLAS CRÍTICAS ⚠️
1. Las cuentas NO oficiales DAN apoyo (ejecutan likes/comments/subs)
2. Las cuentas NO oficiales NUNCA reciben apoyo
3. El bot PIDE apoyo hacia cuentas OFICIALES solamente
4. Toda interacción DEBE pasar por SecurityLayer
5. Toda interacción DEBE registrarse en Metrics
"""
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.orm import Session

from app.telegram_exchange_bot.models import (
    Platform,
    InteractionType,
    OurContent
)
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccountsPool,
    NonOfficialAccount
)
from app.telegram_exchange_bot.security import (
    TelegramBotSecurityLayer,
    SecurityContext,
    SecurityException,
    AntiShadowbanProtection
)

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Estado de ejecución de una interacción."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    ABORTED = "aborted"


class ExecutionResult:
    """Resultado de una ejecución."""
    
    def __init__(
        self,
        status: ExecutionStatus,
        interaction_type: InteractionType,
        target_url: str,
        account_used: NonOfficialAccount,
        execution_time_seconds: float,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.status = status
        self.interaction_type = interaction_type
        self.target_url = target_url
        self.account_used = account_used
        self.execution_time_seconds = execution_time_seconds
        self.error = error
        self.metadata = metadata or {}
        self.executed_at = datetime.utcnow()
    
    @property
    def was_successful(self) -> bool:
        """Verifica si fue exitoso."""
        return self.status == ExecutionStatus.SUCCESS


class PlatformExecutor:
    """
    Ejecutor base para plataformas.
    
    Subclases: YouTubeExecutor, InstagramExecutor, TikTokExecutor
    """
    
    def __init__(self, platform: Platform):
        self.platform = platform
    
    async def execute_like(
        self,
        target_url: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """
        Ejecuta like en la plataforma.
        
        Args:
            target_url: URL del contenido a darle like
            account: Cuenta NO oficial que ejecuta
            security_context: Contexto de seguridad
            
        Returns:
            ExecutionResult
        """
        raise NotImplementedError
    
    async def execute_comment(
        self,
        target_url: str,
        comment_text: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """
        Ejecuta comentario en la plataforma.
        
        Args:
            target_url: URL del contenido a comentar
            comment_text: Texto del comentario
            account: Cuenta NO oficial que ejecuta
            security_context: Contexto de seguridad
            
        Returns:
            ExecutionResult
        """
        raise NotImplementedError
    
    async def execute_subscribe(
        self,
        target_url: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """
        Ejecuta suscripción/follow en la plataforma.
        
        Args:
            target_url: URL del canal/perfil
            account: Cuenta NO oficial que ejecuta
            security_context: Contexto de seguridad
            
        Returns:
            ExecutionResult
        """
        raise NotImplementedError


class YouTubeExecutor(PlatformExecutor):
    """Ejecutor para YouTube (usando APIs no oficiales)."""
    
    def __init__(self):
        super().__init__(Platform.YOUTUBE)
    
    async def execute_like(
        self,
        target_url: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """
        Ejecuta like en video de YouTube.
        
        IMPORTANTE: Usa cuenta NO oficial para dar like.
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Ejecutando YouTube LIKE: {target_url} "
                f"desde cuenta {account.username}"
            )
            
            # TODO: Implementar con yt-dlp o API no oficial
            # Por ahora, simulación
            await asyncio.sleep(2)  # Simular latencia
            
            # SIMULACIÓN: Marcar como exitoso
            success = True
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_LIKE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                metadata={"simulated": True}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error ejecutando YouTube like: {e}")
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_LIKE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                error=str(e)
            )
    
    async def execute_comment(
        self,
        target_url: str,
        comment_text: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """Ejecuta comentario en video de YouTube."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Ejecutando YouTube COMMENT: {target_url} "
                f"desde {account.username}: '{comment_text[:30]}...'"
            )
            
            # TODO: Implementar con API no oficial
            await asyncio.sleep(3)
            success = True
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_COMMENT,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                metadata={"comment": comment_text, "simulated": True}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_COMMENT,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                error=str(e)
            )
    
    async def execute_subscribe(
        self,
        target_url: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """Ejecuta suscripción a canal de YouTube."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Ejecutando YouTube SUBSCRIBE: {target_url} "
                f"desde {account.username}"
            )
            
            # TODO: Implementar con API no oficial
            await asyncio.sleep(2)
            success = True
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_SUBSCRIBE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                metadata={"simulated": True}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                interaction_type=InteractionType.YOUTUBE_SUBSCRIBE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                error=str(e)
            )


class InstagramExecutor(PlatformExecutor):
    """Ejecutor para Instagram (usando instagrapi)."""
    
    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
    
    async def execute_like(
        self,
        target_url: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """Ejecuta like en post de Instagram."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Ejecutando Instagram LIKE: {target_url} "
                f"desde {account.username}"
            )
            
            # TODO: Implementar con instagrapi
            await asyncio.sleep(2)
            success = True
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                interaction_type=InteractionType.INSTAGRAM_LIKE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                metadata={"simulated": True}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                interaction_type=InteractionType.INSTAGRAM_LIKE,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                error=str(e)
            )
    
    async def execute_comment(
        self,
        target_url: str,
        comment_text: str,
        account: NonOfficialAccount,
        security_context: SecurityContext
    ) -> ExecutionResult:
        """Ejecuta comentario en Instagram."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Ejecutando Instagram COMMENT: {target_url} "
                f"desde {account.username}"
            )
            
            # TODO: Implementar con instagrapi
            await asyncio.sleep(3)
            success = True
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                interaction_type=InteractionType.INSTAGRAM_COMMENT,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                metadata={"comment": comment_text, "simulated": True}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                interaction_type=InteractionType.INSTAGRAM_COMMENT,
                target_url=target_url,
                account_used=account,
                execution_time_seconds=execution_time,
                error=str(e)
            )


class InteractionExecutor:
    """
    Ejecutor principal de interacciones.
    
    Características:
    - Ejecuta interacciones desde cuentas NO oficiales
    - Validación de seguridad obligatoria
    - Retry logic con backoff
    - Rate limiting automático
    - Registro en métricas
    """
    
    def __init__(
        self,
        accounts_pool: NonOfficialAccountsPool,
        security_layer: TelegramBotSecurityLayer,
        db: Session
    ):
        """
        Args:
            accounts_pool: Pool de cuentas NO oficiales
            security_layer: Capa de seguridad
            db: Sesión de BD
        """
        self.accounts_pool = accounts_pool
        self.security_layer = security_layer
        self.db = db
        
        # Ejecutores por plataforma
        self.executors = {
            Platform.YOUTUBE: YouTubeExecutor(),
            Platform.INSTAGRAM: InstagramExecutor(),
            # Platform.TIKTOK: TikTokExecutor(),  # TODO
        }
        
        # Stats
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "retries": 0
        }
        
        logger.info("InteractionExecutor inicializado")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        reraise=True
    )
    async def execute_interaction(
        self,
        interaction_type: InteractionType,
        target_url: str,
        comment_text: Optional[str] = None
    ) -> ExecutionResult:
        """
        Ejecuta interacción en plataforma.
        
        ⚠️ IMPORTANTE: target_url es el contenido A APOYAR (usuario del grupo)
        NO es contenido oficial.
        
        Args:
            interaction_type: Tipo de interacción
            target_url: URL a darle apoyo (like/comment/sub)
            comment_text: Texto del comentario (si aplica)
            
        Returns:
            ExecutionResult
        """
        self.stats["total_executions"] += 1
        
        # 1. Determinar plataforma
        platform = self._get_platform_from_interaction_type(interaction_type)
        
        if platform not in self.executors:
            logger.error(f"No hay ejecutor para {platform.value}")
            return self._create_failed_result(
                interaction_type,
                target_url,
                "Platform not supported"
            )
        
        # 2. Obtener cuenta NO oficial
        account = await self.accounts_pool.get_account(platform.value)
        if not account:
            logger.error(f"No hay cuentas disponibles para {platform.value}")
            return self._create_failed_result(
                interaction_type,
                target_url,
                "No accounts available"
            )
        
        # 3. Obtener contexto de seguridad
        try:
            security_context = await self.security_layer.get_security_context(
                account=account,
                operation=interaction_type.value
            )
        except SecurityException as e:
            logger.error(f"Falló validación de seguridad: {e}")
            return self._create_failed_result(
                interaction_type,
                target_url,
                f"Security validation failed: {e}"
            )
        
        # 4. Aplicar delay humano (anti-shadowban)
        await AntiShadowbanProtection.apply_human_delay(
            operation=interaction_type.value,
            min_seconds=15,
            max_seconds=45
        )
        
        # 5. Ejecutar según tipo
        executor = self.executors[platform]
        
        if interaction_type in [
            InteractionType.YOUTUBE_LIKE,
            InteractionType.INSTAGRAM_LIKE,
            InteractionType.TIKTOK_LIKE
        ]:
            result = await executor.execute_like(target_url, account, security_context)
        
        elif interaction_type in [
            InteractionType.YOUTUBE_COMMENT,
            InteractionType.INSTAGRAM_COMMENT,
            InteractionType.TIKTOK_COMMENT
        ]:
            if not comment_text:
                return self._create_failed_result(
                    interaction_type,
                    target_url,
                    "Comment text required"
                )
            result = await executor.execute_comment(
                target_url, comment_text, account, security_context
            )
        
        elif interaction_type == InteractionType.YOUTUBE_SUBSCRIBE:
            result = await executor.execute_subscribe(target_url, account, security_context)
        
        else:
            return self._create_failed_result(
                interaction_type,
                target_url,
                "Interaction type not implemented"
            )
        
        # 6. Registrar resultado en pool
        await self.accounts_pool.mark_used(
            account=account,
            success=result.was_successful
        )
        
        # 7. Actualizar stats
        if result.was_successful:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
        
        # 8. TODO: Registrar en metrics.py
        
        return result
    
    async def execute_batch(
        self,
        interactions: List[Dict]
    ) -> List[ExecutionResult]:
        """
        Ejecuta batch de interacciones con delays.
        
        Args:
            interactions: Lista de dicts con:
                - interaction_type
                - target_url
                - comment_text (opcional)
        
        Returns:
            Lista de ExecutionResult
        """
        results = []
        
        for i, interaction in enumerate(interactions):
            result = await self.execute_interaction(
                interaction_type=interaction["interaction_type"],
                target_url=interaction["target_url"],
                comment_text=interaction.get("comment_text")
            )
            
            results.append(result)
            
            # Delay entre interacciones del batch
            if i < len(interactions) - 1:
                await asyncio.sleep(60)  # 1 min entre cada una
        
        return results
    
    def _get_platform_from_interaction_type(
        self,
        interaction_type: InteractionType
    ) -> Platform:
        """Obtiene plataforma del tipo de interacción."""
        if "YOUTUBE" in interaction_type.value:
            return Platform.YOUTUBE
        elif "INSTAGRAM" in interaction_type.value:
            return Platform.INSTAGRAM
        elif "TIKTOK" in interaction_type.value:
            return Platform.TIKTOK
        else:
            return Platform.FANPAGE
    
    def _create_failed_result(
        self,
        interaction_type: InteractionType,
        target_url: str,
        error: str
    ) -> ExecutionResult:
        """Crea ExecutionResult de fallo."""
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            interaction_type=interaction_type,
            target_url=target_url,
            account_used=None,  # type: ignore
            execution_time_seconds=0.0,
            error=error
        )
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del executor."""
        success_rate = 0.0
        if self.stats["total_executions"] > 0:
            success_rate = (
                self.stats["successful_executions"] / 
                self.stats["total_executions"]
            )
        
        return {
            **self.stats,
            "success_rate": success_rate
        }
