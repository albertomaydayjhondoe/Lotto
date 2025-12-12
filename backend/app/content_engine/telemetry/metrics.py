"""
Metrics Collector
Telemetría y tracking de costos.
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from ..models import ContentMetrics
from ..config import ContentEngineConfig

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Colector de métricas con cost tracking.
    
    Responsabilidades:
    - Registrar métricas de ejecución
    - Trackear costos acumulados
    - Verificar límites de coste
    - Generar reportes agregados
    """
    
    def __init__(self, config: ContentEngineConfig):
        self.config = config
        self._metrics_buffer: List[ContentMetrics] = []
        self._daily_costs: Dict[str, float] = defaultdict(float)
        self._monthly_costs: Dict[str, float] = defaultdict(float)
        logger.info("MetricsCollector initialized")
    
    async def record(self, metrics: ContentMetrics) -> None:
        """Registra métricas de una request."""
        self._metrics_buffer.append(metrics)
        
        # Update cost tracking
        date_key = metrics.timestamp.strftime("%Y-%m-%d")
        month_key = metrics.timestamp.strftime("%Y-%m")
        
        self._daily_costs[date_key] += metrics.cost_eur
        self._monthly_costs[month_key] += metrics.cost_eur
        
        logger.info(
            f"Metrics recorded: request_id={metrics.request_id}, "
            f"cost={metrics.cost_eur:.4f}€, success={metrics.success}"
        )
        
        # Check limits
        await self._check_and_alert_limits(date_key, month_key)
    
    async def get_summary(self) -> Dict:
        """Retorna resumen de métricas."""
        total_requests = len(self._metrics_buffer)
        successful_requests = sum(1 for m in self._metrics_buffer if m.success)
        total_cost = sum(m.cost_eur for m in self._metrics_buffer)
        avg_execution_time = (
            sum(m.execution_time_ms for m in self._metrics_buffer) / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "total_cost_eur": total_cost,
            "avg_execution_time_ms": avg_execution_time,
            "daily_costs": dict(self._daily_costs),
            "monthly_costs": dict(self._monthly_costs)
        }
    
    async def check_cost_limits(self) -> Dict:
        """Verifica estado de límites de coste."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        this_month = datetime.utcnow().strftime("%Y-%m")
        
        daily_cost = self._daily_costs.get(today, 0.0)
        monthly_cost = self._monthly_costs.get(this_month, 0.0)
        
        return {
            "daily": {
                "current": daily_cost,
                "limit": self.config.max_daily_cost,
                "percentage": (daily_cost / self.config.max_daily_cost) * 100,
                "exceeded": daily_cost > self.config.max_daily_cost
            },
            "monthly": {
                "current": monthly_cost,
                "limit": self.config.max_monthly_cost,
                "percentage": (monthly_cost / self.config.max_monthly_cost) * 100,
                "exceeded": monthly_cost > self.config.max_monthly_cost
            }
        }
    
    async def _check_and_alert_limits(self, date_key: str, month_key: str) -> None:
        """Verifica límites y alerta si se exceden."""
        daily_cost = self._daily_costs[date_key]
        monthly_cost = self._monthly_costs[month_key]
        
        if daily_cost > self.config.max_daily_cost:
            logger.warning(
                f"⚠️  DAILY COST LIMIT EXCEEDED: {daily_cost:.2f}€ > "
                f"{self.config.max_daily_cost}€"
            )
        
        if monthly_cost > self.config.max_monthly_cost:
            logger.error(
                f"🚨 MONTHLY COST LIMIT EXCEEDED: {monthly_cost:.2f}€ > "
                f"{self.config.max_monthly_cost}€"
            )
