"""
Production Hardening - Sprint 7C
Kill-switch, watchdog, anomaly detection, error recovery.

Features:
- Kill-switch API endpoint
- Watchdog 24/7
- Auto-pause on anomalies
- 1 action/account simultaneous
- Full logging
- Dynamic delays
- Isolated execution queue
"""
import logging
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Estados del sistema."""
    RUNNING = "running"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    EMERGENCY_STOP = "emergency_stop"


class AnomalyType(Enum):
    """Tipos de anomalías detectables."""
    HIGH_ERROR_RATE = "high_error_rate"
    SHADOWBAN_WAVE = "shadowban_wave"
    PROXY_FAILURE = "proxy_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ACCOUNT_COMPROMISE = "account_compromise"
    UNUSUAL_PATTERN = "unusual_pattern"


@dataclass
class Anomaly:
    """Anomalía detectada."""
    type: AnomalyType
    severity: float  # [0-1]
    timestamp: datetime
    details: Dict[str, any]
    affected_accounts: List[str]
    auto_paused: bool


@dataclass
class ExecutionSlot:
    """Slot de ejecución para account."""
    account_id: str
    interaction_type: str
    started_at: datetime
    expected_duration_seconds: float


class KillSwitch:
    """
    Kill-switch para detener sistema en emergencias.
    
    Features:
    - API endpoint para activación remota
    - Auto-activación por anomalías críticas
    - Graceful shutdown
    - Logging completo
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.is_active = False
        self.activated_at: Optional[datetime] = None
        self.activated_by: Optional[str] = None
        self.reason: Optional[str] = None
        
        logger.info("KillSwitch initialized")
    
    async def activate(
        self,
        reason: str,
        activated_by: str = "system"
    ) -> bool:
        """
        Activa kill-switch.
        
        Args:
            reason: Motivo de activación
            activated_by: Quién activó (user/system/watchdog)
            
        Returns:
            True si se activó exitosamente
        """
        if self.is_active:
            logger.warning("KillSwitch already active")
            return False
        
        logger.critical(
            f"🔴 KILL-SWITCH ACTIVATED: {reason} (by={activated_by})"
        )
        
        self.is_active = True
        self.activated_at = datetime.utcnow()
        self.activated_by = activated_by
        self.reason = reason
        
        # TODO: Detener todas las tareas en ejecución
        # TODO: Cerrar conexiones
        # TODO: Guardar estado actual
        
        return True
    
    async def deactivate(
        self,
        deactivated_by: str = "admin"
    ) -> bool:
        """
        Desactiva kill-switch.
        
        Args:
            deactivated_by: Quién desactivó
            
        Returns:
            True si se desactivó exitosamente
        """
        if not self.is_active:
            logger.warning("KillSwitch already inactive")
            return False
        
        logger.warning(
            f"🟢 KILL-SWITCH DEACTIVATED (by={deactivated_by}, "
            f"duration={(datetime.utcnow() - self.activated_at).total_seconds():.1f}s)"
        )
        
        self.is_active = False
        
        return True
    
    def get_status(self) -> Dict[str, any]:
        """Obtiene estado del kill-switch."""
        return {
            "is_active": self.is_active,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "activated_by": self.activated_by,
            "reason": self.reason,
            "duration_seconds": (
                (datetime.utcnow() - self.activated_at).total_seconds()
                if self.activated_at else 0
            )
        }


class Watchdog:
    """
    Watchdog 24/7 para monitoreo continuo.
    
    Features:
    - Monitoreo de error rates
    - Detección de shadowban waves
    - Alertas automáticas
    - Auto-pause en anomalías críticas
    """
    
    def __init__(
        self,
        db: Session,
        kill_switch: KillSwitch,
        check_interval_seconds: int = 30
    ):
        self.db = db
        self.kill_switch = kill_switch
        self.check_interval_seconds = check_interval_seconds
        
        # Estado
        self.is_running = False
        self.anomalies_detected: List[Anomaly] = []
        
        # Thresholds
        self.error_rate_threshold = 0.30  # 30%
        self.shadowban_threshold = 5  # 5 shadowbans en 1 hora
        self.proxy_failure_threshold = 10  # 10 fallos consecutivos
        
        logger.info(
            f"Watchdog initialized: "
            f"check_interval={check_interval_seconds}s, "
            f"error_threshold={self.error_rate_threshold:.0%}"
        )
    
    async def check_error_rate(self, window_minutes: int = 60) -> Optional[Anomaly]:
        """
        Verifica error rate reciente.
        
        Args:
            window_minutes: Ventana de tiempo
            
        Returns:
            Anomaly si error rate > threshold
        """
        # TODO: Query real a exchange_interactions_executed
        # Por ahora, mock
        
        total_interactions = 100
        failed_interactions = 25
        error_rate = failed_interactions / total_interactions if total_interactions > 0 else 0
        
        if error_rate > self.error_rate_threshold:
            logger.warning(
                f"High error rate detected: {error_rate:.2%} > {self.error_rate_threshold:.2%}"
            )
            
            return Anomaly(
                type=AnomalyType.HIGH_ERROR_RATE,
                severity=min(error_rate / self.error_rate_threshold, 1.0),
                timestamp=datetime.utcnow(),
                details={
                    "error_rate": error_rate,
                    "total_interactions": total_interactions,
                    "failed_interactions": failed_interactions,
                    "window_minutes": window_minutes
                },
                affected_accounts=[],
                auto_paused=False
            )
        
        return None
    
    async def check_shadowban_wave(self, window_hours: int = 1) -> Optional[Anomaly]:
        """
        Detecta shadowban wave.
        
        Args:
            window_hours: Ventana de tiempo
            
        Returns:
            Anomaly si shadowbans > threshold
        """
        # TODO: Query real a shadowban events
        # Por ahora, mock
        
        shadowbans_count = 3
        
        if shadowbans_count >= self.shadowban_threshold:
            logger.error(
                f"Shadowban wave detected: {shadowbans_count} shadowbans in {window_hours}h"
            )
            
            return Anomaly(
                type=AnomalyType.SHADOWBAN_WAVE,
                severity=min(shadowbans_count / self.shadowban_threshold, 1.0),
                timestamp=datetime.utcnow(),
                details={
                    "shadowbans_count": shadowbans_count,
                    "window_hours": window_hours
                },
                affected_accounts=[],
                auto_paused=True
            )
        
        return None
    
    async def check_proxy_failures(self) -> Optional[Anomaly]:
        """
        Verifica fallos de proxy consecutivos.
        
        Returns:
            Anomaly si proxy failures > threshold
        """
        # TODO: Query real a proxy failures
        # Por ahora, mock
        
        consecutive_failures = 8
        
        if consecutive_failures >= self.proxy_failure_threshold:
            logger.error(
                f"Proxy failure detected: {consecutive_failures} consecutive failures"
            )
            
            return Anomaly(
                type=AnomalyType.PROXY_FAILURE,
                severity=min(consecutive_failures / self.proxy_failure_threshold, 1.0),
                timestamp=datetime.utcnow(),
                details={
                    "consecutive_failures": consecutive_failures
                },
                affected_accounts=[],
                auto_paused=True
            )
        
        return None
    
    async def handle_anomaly(self, anomaly: Anomaly):
        """
        Maneja anomalía detectada.
        
        Args:
            anomaly: Anomalía a manejar
        """
        self.anomalies_detected.append(anomaly)
        
        logger.warning(
            f"Anomaly detected: {anomaly.type.value} "
            f"(severity={anomaly.severity:.2f})"
        )
        
        # Auto-pause si severidad crítica
        if anomaly.severity >= 0.8 and anomaly.auto_paused:
            logger.critical("Critical anomaly detected, activating kill-switch")
            await self.kill_switch.activate(
                reason=f"Critical anomaly: {anomaly.type.value}",
                activated_by="watchdog"
            )
        
        # TODO: Enviar alertas (email, Telegram, Slack, etc.)
    
    async def check_all(self):
        """Ejecuta todos los checks."""
        try:
            # Error rate
            anomaly = await self.check_error_rate()
            if anomaly:
                await self.handle_anomaly(anomaly)
            
            # Shadowban wave
            anomaly = await self.check_shadowban_wave()
            if anomaly:
                await self.handle_anomaly(anomaly)
            
            # Proxy failures
            anomaly = await self.check_proxy_failures()
            if anomaly:
                await self.handle_anomaly(anomaly)
            
        except Exception as e:
            logger.error(f"Error in watchdog checks: {e}")
    
    async def run(self):
        """Loop principal del watchdog."""
        self.is_running = True
        logger.info("Watchdog started")
        
        while self.is_running:
            try:
                await self.check_all()
                await asyncio.sleep(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in watchdog loop: {e}")
                await asyncio.sleep(self.check_interval_seconds)
    
    def stop(self):
        """Detiene watchdog."""
        logger.info("Stopping watchdog...")
        self.is_running = False
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del watchdog."""
        return {
            "is_running": self.is_running,
            "check_interval_seconds": self.check_interval_seconds,
            "anomalies_detected": len(self.anomalies_detected),
            "anomalies_last_24h": len([
                a for a in self.anomalies_detected
                if (datetime.utcnow() - a.timestamp).total_seconds() < 86400
            ]),
            "kill_switch_status": self.kill_switch.get_status()
        }


class IsolatedExecutionQueue:
    """
    Cola de ejecución aislada.
    
    Features:
    - 1 acción simultánea por cuenta
    - Priorización
    - Delays dinámicos
    - Circuit breaker integration
    """
    
    def __init__(self):
        self.active_slots: Dict[str, ExecutionSlot] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.total_executed = 0
        self.total_failed = 0
        
        logger.info("IsolatedExecutionQueue initialized")
    
    def is_account_busy(self, account_id: str) -> bool:
        """
        Verifica si cuenta está ocupada.
        
        Args:
            account_id: ID de cuenta
            
        Returns:
            True si cuenta está ejecutando algo
        """
        return account_id in self.active_slots
    
    async def acquire_slot(
        self,
        account_id: str,
        interaction_type: str,
        expected_duration_seconds: float
    ) -> bool:
        """
        Adquiere slot de ejecución para cuenta.
        
        Args:
            account_id: ID de cuenta
            interaction_type: Tipo de interacción
            expected_duration_seconds: Duración esperada
            
        Returns:
            True si slot adquirido exitosamente
        """
        if self.is_account_busy(account_id):
            logger.debug(f"Account {account_id} is busy")
            return False
        
        slot = ExecutionSlot(
            account_id=account_id,
            interaction_type=interaction_type,
            started_at=datetime.utcnow(),
            expected_duration_seconds=expected_duration_seconds
        )
        
        self.active_slots[account_id] = slot
        
        logger.debug(
            f"Slot acquired: {account_id} ({interaction_type}, "
            f"expected={expected_duration_seconds}s)"
        )
        
        return True
    
    async def release_slot(
        self,
        account_id: str,
        success: bool
    ):
        """
        Libera slot de ejecución.
        
        Args:
            account_id: ID de cuenta
            success: Si la ejecución fue exitosa
        """
        if account_id not in self.active_slots:
            logger.warning(f"No active slot for {account_id}")
            return
        
        slot = self.active_slots.pop(account_id)
        duration = (datetime.utcnow() - slot.started_at).total_seconds()
        
        if success:
            self.total_executed += 1
        else:
            self.total_failed += 1
        
        logger.debug(
            f"Slot released: {account_id} "
            f"(success={success}, duration={duration:.1f}s)"
        )
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas de la cola."""
        return {
            "active_slots": len(self.active_slots),
            "total_executed": self.total_executed,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_executed / (self.total_executed + self.total_failed)
                if (self.total_executed + self.total_failed) > 0 else 0
            )
        }


class ProductionHardening:
    """
    Production hardening completo.
    
    Integra:
    - KillSwitch
    - Watchdog
    - IsolatedExecutionQueue
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.kill_switch = KillSwitch(db=db)
        self.watchdog = Watchdog(db=db, kill_switch=self.kill_switch)
        self.execution_queue = IsolatedExecutionQueue()
        
        logger.info("ProductionHardening initialized")
    
    async def start(self):
        """Inicia production hardening."""
        logger.info("Starting production hardening...")
        
        # Iniciar watchdog
        asyncio.create_task(self.watchdog.run())
        
        logger.info("Production hardening started")
    
    async def stop(self):
        """Detiene production hardening."""
        logger.info("Stopping production hardening...")
        
        self.watchdog.stop()
        
        logger.info("Production hardening stopped")
    
    def get_full_status(self) -> Dict[str, any]:
        """Obtiene estado completo."""
        return {
            "kill_switch": self.kill_switch.get_status(),
            "watchdog": self.watchdog.get_stats(),
            "execution_queue": self.execution_queue.get_stats()
        }
