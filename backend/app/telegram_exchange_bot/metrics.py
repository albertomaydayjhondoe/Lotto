"""
Metrics System - Sprint 7B
Sistema completo de métricas y ROI para Telegram Exchange Bot.

⚠️ SEGUIMIENTO COMPLETO ⚠️
1. Registra TODAS las interacciones ejecutadas
2. Calcula ROI por grupo/usuario/plataforma
3. Exporta métricas a BrainOrchestrator
4. Dashboard interno de performance
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.telegram_exchange_bot.models import (
    Platform,
    InteractionType,
    PriorityLevel
)
from app.telegram_exchange_bot.executor import ExecutionResult, ExecutionStatus
from app.brain.brain_orchestrator_stub import get_brain_orchestrator

logger = logging.getLogger(__name__)


class MetricPeriod(str, Enum):
    """Período de agregación de métricas."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


@dataclass
class InteractionMetric:
    """
    Métrica de una interacción ejecutada.
    
    Registra TODO lo necesario para análisis ROI.
    """
    # Identificación
    interaction_id: str
    executed_at: datetime
    
    # Contexto
    interaction_type: InteractionType
    platform: Platform
    target_url: str
    
    # Cuenta usada
    account_id: str
    account_username: str
    
    # Usuario objetivo
    target_user_id: Optional[str] = None
    target_username: Optional[str] = None
    
    # Origen
    telegram_group_id: Optional[str] = None
    telegram_group_name: Optional[str] = None
    
    # Resultado
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    execution_time_seconds: float = 0.0
    error: Optional[str] = None
    
    # Seguridad
    vpn_active: bool = False
    proxy_used: Optional[str] = None
    fingerprint_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ROIMetrics:
    """
    Métricas de ROI para análisis.
    
    Calcula retorno de inversión por:
    - Grupo de Telegram
    - Usuario externo
    - Plataforma
    """
    entity_id: str  # group_id, user_id, o platform
    entity_type: str  # "group", "user", "platform"
    period: MetricPeriod
    
    # Interacciones
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    
    # Breakdown por tipo
    likes_given: int = 0
    comments_given: int = 0
    subscribes_given: int = 0
    
    # Reciprocidad (solo para grupos/usuarios)
    support_given: int = 0  # Apoyos dados por nosotros
    support_received: int = 0  # Apoyos recibidos de ellos
    
    # ROI
    roi_ratio: float = 0.0  # support_received / support_given
    success_rate: float = 0.0  # successful / total
    
    # Costos (estimado)
    estimated_cost_eur: float = 0.0
    
    # Temporal
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None


@dataclass
class PerformanceDashboard:
    """Dashboard de performance general."""
    period: MetricPeriod
    generated_at: datetime
    
    # Totales
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    
    # Por plataforma
    youtube_executions: int = 0
    instagram_executions: int = 0
    tiktok_executions: int = 0
    
    # Top performers
    top_groups: List[Dict[str, Any]] = field(default_factory=list)
    top_users: List[Dict[str, Any]] = field(default_factory=list)
    
    # Costos
    total_cost_eur: float = 0.0
    avg_cost_per_interaction: float = 0.0
    
    # ROI general
    global_roi: float = 0.0
    
    # Health
    health_status: str = "healthy"  # healthy, warning, critical
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    """
    Colector de métricas del Telegram Exchange Bot.
    
    Funciones:
    1. Registrar todas las interacciones ejecutadas
    2. Calcular ROI por entidad (grupo/usuario/plataforma)
    3. Generar dashboards de performance
    4. Exportar a BrainOrchestrator para feedback ML
    5. Detectar anomalías y recomendar ajustes
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: Sesión de BD
        """
        self.db = db
        self.brain = get_brain_orchestrator()
        
        # Buffer en memoria (antes de flush a BD)
        self._buffer: List[InteractionMetric] = []
        self._buffer_size = 50  # Flush cada 50 métricas
        
        # Costos estimados por interacción
        self.interaction_costs = {
            InteractionType.YOUTUBE_LIKE: 0.02,
            InteractionType.YOUTUBE_COMMENT: 0.05,
            InteractionType.YOUTUBE_SUBSCRIBE: 0.08,
            InteractionType.INSTAGRAM_LIKE: 0.015,
            InteractionType.INSTAGRAM_COMMENT: 0.04,
            InteractionType.INSTAGRAM_FOLLOW: 0.06,
            InteractionType.TIKTOK_LIKE: 0.018,
            InteractionType.TIKTOK_COMMENT: 0.045,
            InteractionType.TIKTOK_FOLLOW: 0.07,
        }
        
        logger.info("MetricsCollector inicializado")
    
    async def record_execution(
        self,
        execution_result: ExecutionResult,
        telegram_group_id: Optional[str] = None,
        telegram_group_name: Optional[str] = None,
        target_user_id: Optional[str] = None,
        target_username: Optional[str] = None
    ):
        """
        Registra resultado de ejecución.
        
        Args:
            execution_result: Resultado del executor
            telegram_group_id: ID del grupo origen
            telegram_group_name: Nombre del grupo
            target_user_id: ID del usuario objetivo
            target_username: Username del usuario
        """
        metric = InteractionMetric(
            interaction_id=f"int_{datetime.utcnow().timestamp()}",
            executed_at=execution_result.executed_at,
            interaction_type=execution_result.interaction_type,
            platform=self._get_platform_from_interaction(execution_result.interaction_type),
            target_url=execution_result.target_url,
            account_id=execution_result.account_used.account_id if execution_result.account_used else "",
            account_username=execution_result.account_used.username if execution_result.account_used else "",
            target_user_id=target_user_id,
            target_username=target_username,
            telegram_group_id=telegram_group_id,
            telegram_group_name=telegram_group_name,
            status=execution_result.status,
            execution_time_seconds=execution_result.execution_time_seconds,
            error=execution_result.error,
            metadata=execution_result.metadata
        )
        
        # Add to buffer
        self._buffer.append(metric)
        
        # Flush si llegamos al límite
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Guarda buffer en BD."""
        if not self._buffer:
            return
        
        try:
            # TODO: INSERT bulk a BD
            # Por ahora, solo log
            logger.info(f"Flushing {len(self._buffer)} metrics to DB")
            
            # Exportar a Brain cada flush
            await self._export_to_brain(self._buffer)
            
            self._buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
    
    async def calculate_roi(
        self,
        entity_id: str,
        entity_type: str,
        period: MetricPeriod = MetricPeriod.DAILY
    ) -> ROIMetrics:
        """
        Calcula ROI para una entidad.
        
        Args:
            entity_id: ID de grupo/usuario/plataforma
            entity_type: "group", "user", "platform"
            period: Período de agregación
            
        Returns:
            ROIMetrics
        """
        metrics = ROIMetrics(
            entity_id=entity_id,
            entity_type=entity_type,
            period=period
        )
        
        # TODO: Query BD para interacciones
        # Por ahora, valores mock
        
        metrics.total_interactions = 45
        metrics.successful_interactions = 40
        metrics.failed_interactions = 5
        
        metrics.likes_given = 25
        metrics.comments_given = 10
        metrics.subscribes_given = 5
        
        # Calcular success rate
        if metrics.total_interactions > 0:
            metrics.success_rate = (
                metrics.successful_interactions / metrics.total_interactions
            )
        
        # Calcular ROI (solo para grupos/usuarios)
        if entity_type in ["group", "user"]:
            metrics.support_given = 40
            metrics.support_received = 28  # Mock: Recibimos menos de lo que damos
            
            if metrics.support_given > 0:
                metrics.roi_ratio = metrics.support_received / metrics.support_given
        
        # Estimar costo
        metrics.estimated_cost_eur = self._estimate_total_cost(metrics)
        
        return metrics
    
    async def generate_dashboard(
        self,
        period: MetricPeriod = MetricPeriod.DAILY
    ) -> PerformanceDashboard:
        """
        Genera dashboard de performance general.
        
        Args:
            period: Período de agregación
            
        Returns:
            PerformanceDashboard
        """
        dashboard = PerformanceDashboard(
            period=period,
            generated_at=datetime.utcnow()
        )
        
        # TODO: Consultar BD para métricas agregadas
        # Por ahora, valores mock
        
        dashboard.total_executions = 120
        dashboard.successful_executions = 105
        dashboard.failed_executions = 15
        dashboard.success_rate = 0.875
        
        dashboard.youtube_executions = 50
        dashboard.instagram_executions = 45
        dashboard.tiktok_executions = 25
        
        # Top groups (mock)
        dashboard.top_groups = [
            {"group_id": "group_001", "group_name": "Músicos Indie", "roi": 1.35, "interactions": 40},
            {"group_id": "group_002", "group_name": "Promo YouTube", "roi": 0.92, "interactions": 35},
            {"group_id": "group_003", "group_name": "Apoyo Mutuo", "roi": 1.18, "interactions": 28},
        ]
        
        # Top users (mock)
        dashboard.top_users = [
            {"user_id": "user_001", "username": "@indie_artist", "roi": 1.50, "reliability": 0.95},
            {"user_id": "user_002", "username": "@youtube_creator", "roi": 1.20, "reliability": 0.88},
        ]
        
        # Costos
        dashboard.total_cost_eur = 3.85
        dashboard.avg_cost_per_interaction = 0.032
        
        # ROI general
        dashboard.global_roi = 1.12  # Recibimos 12% más de lo que damos
        
        # Health check
        dashboard.health_status = self._assess_health(dashboard)
        dashboard.recommendations = self._generate_recommendations(dashboard)
        
        return dashboard
    
    async def export_to_orchestrator(
        self,
        period: MetricPeriod = MetricPeriod.DAILY
    ) -> Dict[str, Any]:
        """
        Exporta métricas al BrainOrchestrator.
        
        Args:
            period: Período de exportación
            
        Returns:
            Resultado de la exportación
        """
        dashboard = await self.generate_dashboard(period)
        
        export_data = {
            "module": "telegram_exchange_bot",
            "period": period.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_executions": dashboard.total_executions,
                "success_rate": dashboard.success_rate,
                "global_roi": dashboard.global_roi,
                "total_cost_eur": dashboard.total_cost_eur,
                "platform_breakdown": {
                    "youtube": dashboard.youtube_executions,
                    "instagram": dashboard.instagram_executions,
                    "tiktok": dashboard.tiktok_executions
                },
                "top_performers": {
                    "groups": dashboard.top_groups[:5],
                    "users": dashboard.top_users[:5]
                }
            },
            "health": {
                "status": dashboard.health_status,
                "recommendations": dashboard.recommendations
            }
        }
        
        # TODO: Enviar al Brain
        logger.info(f"Exporting metrics to BrainOrchestrator: {period.value}")
        
        return {
            "exported": True,
            "timestamp": datetime.utcnow(),
            "brain_mode": self.brain.get_orchestrator_status().get("mode", "stub")
        }
    
    async def _export_to_brain(self, metrics: List[InteractionMetric]):
        """Exporta batch de métricas al Brain."""
        try:
            # TODO: Implementar exportación real
            logger.debug(f"Exporting {len(metrics)} metrics to Brain")
        except Exception as e:
            logger.error(f"Error exporting to brain: {e}")
    
    def _get_platform_from_interaction(
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
            return Platform.YOUTUBE  # Default
    
    def _estimate_total_cost(self, metrics: ROIMetrics) -> float:
        """Estima costo total de las interacciones."""
        cost = 0.0
        
        cost += metrics.likes_given * 0.02
        cost += metrics.comments_given * 0.045
        cost += metrics.subscribes_given * 0.07
        
        return round(cost, 3)
    
    def _assess_health(self, dashboard: PerformanceDashboard) -> str:
        """Evalúa health status del sistema."""
        if dashboard.success_rate < 0.7 or dashboard.global_roi < 0.5:
            return "critical"
        elif dashboard.success_rate < 0.85 or dashboard.global_roi < 0.9:
            return "warning"
        else:
            return "healthy"
    
    def _generate_recommendations(
        self,
        dashboard: PerformanceDashboard
    ) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        recommendations = []
        
        if dashboard.success_rate < 0.85:
            recommendations.append(
                f"Success rate bajo ({dashboard.success_rate:.2%}). "
                "Revisar accounts_pool y security layer."
            )
        
        if dashboard.global_roi < 0.9:
            recommendations.append(
                f"ROI global bajo ({dashboard.global_roi:.2f}). "
                "Priorizar grupos con mejor reciprocidad."
            )
        
        if dashboard.failed_executions > 20:
            recommendations.append(
                f"{dashboard.failed_executions} ejecuciones fallidas. "
                "Verificar proxies y cuentas bloqueadas."
            )
        
        if dashboard.total_cost_eur > 10.0:
            recommendations.append(
                f"Costo alto (€{dashboard.total_cost_eur:.2f}). "
                "Ajustar rate limits y priorización."
            )
        
        if not recommendations:
            recommendations.append("Sistema operando óptimamente. No hay recomendaciones.")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna stats del metrics collector."""
        return {
            "buffer_size": len(self._buffer),
            "buffer_capacity": self._buffer_size,
            "interaction_costs": {k.value: v for k, v in self.interaction_costs.items()}
        }
