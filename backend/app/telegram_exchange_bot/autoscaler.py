"""
Account Auto-Scaler - Sprint 7C
Auto-scaling inteligente basado en carga y salud de cuentas.

Triggers:
- Carga del pool >70% → Activa nuevas cuentas
- Health score <0.3 → Cooldown automático
- Max 10 nuevas cuentas/día
- Proxy+Fingerprint únicos por cuenta
"""
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccountsPool,
    AccountHealthMonitor
)
from app.telegram_exchange_bot.security import (
    TelegramBotSecurityLayer,
    SecurityContext
)

logger = logging.getLogger(__name__)


class ScalingTrigger(Enum):
    """Razones para escalar."""
    HIGH_LOAD = "high_load"
    LOW_HEALTH = "low_health"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


@dataclass
class ScalingEvent:
    """Evento de scaling."""
    trigger: ScalingTrigger
    timestamp: datetime
    accounts_before: int
    accounts_after: int
    accounts_added: int
    reason: str
    success: bool


class AccountAutoScaler:
    """
    Auto-scaler para pool de cuentas.
    
    Features:
    - Monitoreo continuo de carga del pool
    - Activación automática de nuevas cuentas
    - Cooldown basado en health score
    - Rate limiting (max 10 nuevas/día)
    - Proxy+Fingerprint únicos
    """
    
    def __init__(
        self,
        pool: NonOfficialAccountsPool,
        health_monitor: AccountHealthMonitor,
        security_layer: TelegramBotSecurityLayer,
        db: Session
    ):
        self.pool = pool
        self.health_monitor = health_monitor
        self.security_layer = security_layer
        self.db = db
        
        # Configuración
        self.high_load_threshold = 0.70  # 70%
        self.low_health_threshold = 0.30  # health < 0.3
        self.max_new_accounts_per_day = 10
        self.check_interval_seconds = 60  # Revisar cada 60s
        
        # Estado
        self.scaling_events: List[ScalingEvent] = []
        self.new_accounts_today = 0
        self.last_daily_reset = datetime.utcnow().date()
        self.is_running = False
        
        logger.info(
            "AccountAutoScaler initialized: "
            f"load_threshold={self.high_load_threshold}, "
            f"health_threshold={self.low_health_threshold}, "
            f"max_new_per_day={self.max_new_accounts_per_day}"
        )
    
    def calculate_pool_load(self) -> float:
        """
        Calcula carga actual del pool.
        
        Load = (active_accounts + queued_tasks) / total_healthy_accounts
        
        Returns:
            Load ratio [0.0 - 1.0+]
        """
        try:
            # Cuentas activas
            active_accounts = len([
                acc for acc in self.pool.accounts.values()
                if acc.is_active and not acc.is_cooling_down
            ])
            
            # Cuentas saludables disponibles
            healthy_accounts = len([
                acc for acc in self.pool.accounts.values()
                if self.health_monitor.get_health_score(acc.account_id) > self.low_health_threshold
            ])
            
            if healthy_accounts == 0:
                return 1.0  # Critical: no healthy accounts
            
            # TODO: Integrar con queue de tareas pendientes
            queued_tasks = 0  # Placeholder
            
            load = (active_accounts + queued_tasks) / healthy_accounts
            
            logger.debug(
                f"Pool load: {load:.2f} "
                f"(active={active_accounts}, healthy={healthy_accounts}, queued={queued_tasks})"
            )
            
            return min(load, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating pool load: {e}")
            return 0.0
    
    def get_unhealthy_accounts(self) -> List[str]:
        """
        Obtiene cuentas con health score bajo.
        
        Returns:
            Lista de account_ids con health < threshold
        """
        unhealthy = []
        
        for account_id in self.pool.accounts.keys():
            health_score = self.health_monitor.get_health_score(account_id)
            
            if health_score < self.low_health_threshold:
                unhealthy.append(account_id)
                logger.warning(
                    f"Unhealthy account detected: {account_id} "
                    f"(health={health_score:.2f})"
                )
        
        return unhealthy
    
    async def activate_new_accounts(
        self,
        count: int,
        trigger: ScalingTrigger,
        reason: str
    ) -> Tuple[int, List[str]]:
        """
        Activa nuevas cuentas en el pool.
        
        Args:
            count: Número de cuentas a activar
            trigger: Razón del scaling
            reason: Descripción detallada
            
        Returns:
            (activated_count, new_account_ids)
        """
        # Rate limiting diario
        if self.new_accounts_today >= self.max_new_accounts_per_day:
            logger.warning(
                f"Daily limit reached: {self.new_accounts_today}/{self.max_new_accounts_per_day}"
            )
            return 0, []
        
        # Limitar por cuota diaria
        available_quota = self.max_new_accounts_per_day - self.new_accounts_today
        count = min(count, available_quota)
        
        logger.info(f"Activating {count} new accounts (trigger={trigger.value}, reason={reason})")
        
        activated = []
        
        for i in range(count):
            try:
                # Generar datos para nueva cuenta
                account_id = f"auto_scaled_{datetime.utcnow().timestamp()}_{i}"
                username = f"user_{account_id[-8:]}"
                
                # Asignar proxy+fingerprint únicos
                security_context = await self.security_layer.prepare_security_context(
                    account_id=account_id,
                    target_url="https://telegram.org",  # Placeholder
                    interaction_type="telegram_join"
                )
                
                if not security_context:
                    logger.error(f"Failed to prepare security context for {account_id}")
                    continue
                
                # Crear cuenta en el pool
                # TODO: Integrar con sistema de registro real de cuentas no oficiales
                logger.info(
                    f"New account created: {account_id} "
                    f"(proxy={security_context.proxy.host}, "
                    f"fingerprint={security_context.fingerprint[:8]}...)"
                )
                
                activated.append(account_id)
                self.new_accounts_today += 1
                
                # Delay anti-detección
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error activating account {i+1}/{count}: {e}")
                continue
        
        # Registrar evento
        event = ScalingEvent(
            trigger=trigger,
            timestamp=datetime.utcnow(),
            accounts_before=len(self.pool.accounts),
            accounts_after=len(self.pool.accounts) + len(activated),
            accounts_added=len(activated),
            reason=reason,
            success=len(activated) > 0
        )
        self.scaling_events.append(event)
        
        logger.info(
            f"Scaling complete: {len(activated)}/{count} accounts activated "
            f"(total_today={self.new_accounts_today})"
        )
        
        return len(activated), activated
    
    async def apply_cooldown(self, account_ids: List[str]) -> int:
        """
        Aplica cooldown a cuentas unhealthy.
        
        Args:
            account_ids: IDs de cuentas a poner en cooldown
            
        Returns:
            Número de cuentas enfriadas
        """
        cooled_count = 0
        
        for account_id in account_ids:
            try:
                account = self.pool.accounts.get(account_id)
                if not account:
                    continue
                
                # Calcular duración del cooldown basado en health
                health_score = self.health_monitor.get_health_score(account_id)
                cooldown_hours = int((1 - health_score) * 24)  # 0-24h
                cooldown_until = datetime.utcnow() + timedelta(hours=cooldown_hours)
                
                account.is_cooling_down = True
                account.cooldown_until = cooldown_until
                account.is_active = False
                
                logger.info(
                    f"Cooldown applied: {account_id} "
                    f"(health={health_score:.2f}, duration={cooldown_hours}h)"
                )
                
                cooled_count += 1
                
            except Exception as e:
                logger.error(f"Error applying cooldown to {account_id}: {e}")
                continue
        
        return cooled_count
    
    async def check_and_scale(self) -> Optional[ScalingEvent]:
        """
        Verifica condiciones y escala si es necesario.
        
        Returns:
            ScalingEvent si se realizó scaling, None si no
        """
        try:
            # Reset daily counter
            today = datetime.utcnow().date()
            if today > self.last_daily_reset:
                logger.info(
                    f"Daily reset: {self.new_accounts_today} accounts activated yesterday"
                )
                self.new_accounts_today = 0
                self.last_daily_reset = today
            
            # 1. Verificar cuentas unhealthy
            unhealthy = self.get_unhealthy_accounts()
            if unhealthy:
                cooled = await self.apply_cooldown(unhealthy)
                logger.info(f"Applied cooldown to {cooled}/{len(unhealthy)} unhealthy accounts")
            
            # 2. Verificar carga del pool
            current_load = self.calculate_pool_load()
            
            if current_load > self.high_load_threshold:
                # High load detected
                logger.warning(
                    f"High load detected: {current_load:.2%} > {self.high_load_threshold:.2%}"
                )
                
                # Calcular cuántas cuentas necesitamos
                needed_accounts = max(1, int((current_load - self.high_load_threshold) * 10))
                
                activated, new_ids = await self.activate_new_accounts(
                    count=needed_accounts,
                    trigger=ScalingTrigger.HIGH_LOAD,
                    reason=f"Pool load {current_load:.2%} exceeded threshold"
                )
                
                if activated > 0:
                    return self.scaling_events[-1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error in check_and_scale: {e}")
            return None
    
    async def run_autoscaler(self):
        """
        Loop principal del auto-scaler.
        """
        self.is_running = True
        logger.info(
            f"Auto-scaler started: check_interval={self.check_interval_seconds}s"
        )
        
        while self.is_running:
            try:
                await self.check_and_scale()
                await asyncio.sleep(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in autoscaler loop: {e}")
                await asyncio.sleep(self.check_interval_seconds)
    
    def stop(self):
        """Detiene el auto-scaler."""
        logger.info("Stopping auto-scaler...")
        self.is_running = False
    
    def get_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas del auto-scaler.
        
        Returns:
            Stats dict
        """
        return {
            "is_running": self.is_running,
            "current_load": self.calculate_pool_load(),
            "new_accounts_today": self.new_accounts_today,
            "max_new_accounts_per_day": self.max_new_accounts_per_day,
            "total_scaling_events": len(self.scaling_events),
            "scaling_events_today": len([
                e for e in self.scaling_events
                if e.timestamp.date() == datetime.utcnow().date()
            ]),
            "unhealthy_accounts": len(self.get_unhealthy_accounts())
        }
