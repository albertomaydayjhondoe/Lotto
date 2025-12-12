"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Account BirthFlow State Machine

Máquina de estados completa para el ciclo de vida de cuentas satélite.
Maneja transiciones, validaciones, rollback y bloqueo por violaciones.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .account_models import (
    Account,
    AccountState,
    AccountWarmupMetrics,
    AccountRiskProfile,
    AccountLifecycleLog,
    AccountRiskLevel,
    is_warmup_state,
    can_automate,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class BirthFlowConfig:
    """Configuración de la máquina de estados"""
    
    # State transition thresholds
    w1_3_min_days: int = 3
    w4_7_min_days: int = 4
    w8_14_min_days: int = 7
    secured_min_days: int = 15
    
    # Metrics thresholds for progression
    min_maturity_score: float = 0.6
    min_readiness_level: float = 0.7
    max_risk_score: float = 0.6
    
    # Risk thresholds
    cooldown_threshold: float = 0.6
    pause_threshold: float = 0.8
    
    # Rollback settings
    enable_auto_rollback: bool = True
    rollback_on_risk_spike: bool = True
    risk_spike_threshold: float = 0.3  # Increase in 30min
    
    # Lock settings
    lock_on_critical_risk: bool = True
    lock_on_max_violations: int = 3


# ============================================================================
# ALLOWED TRANSITIONS
# ============================================================================

ALLOWED_TRANSITIONS = {
    AccountState.CREATED: [AccountState.W1_3, AccountState.PAUSED],
    AccountState.W1_3: [AccountState.W4_7, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.W4_7: [AccountState.W8_14, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.W8_14: [AccountState.SECURED, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.SECURED: [AccountState.ACTIVE, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.ACTIVE: [AccountState.SCALING, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.SCALING: [AccountState.ACTIVE, AccountState.COOLDOWN, AccountState.PAUSED],
    AccountState.COOLDOWN: [AccountState.W1_3, AccountState.W4_7, AccountState.W8_14, 
                           AccountState.SECURED, AccountState.ACTIVE, AccountState.PAUSED],
    AccountState.PAUSED: [AccountState.W1_3, AccountState.RETIRED],
    AccountState.RETIRED: [],  # Terminal state
}


# ============================================================================
# ACCOUNT BIRTHFLOW STATE MACHINE
# ============================================================================

class AccountBirthFlowStateMachine:
    """
    Máquina de estados para el ciclo de vida de cuentas.
    
    Responsabilidades:
    - Validar y ejecutar transiciones de estado
    - Verificar métricas y riesgo antes de avanzar
    - Rollback automático en caso de problemas
    - Bloquear cuentas que violen políticas
    - Registrar todas las transiciones (audit log)
    """
    
    def __init__(self, config: Optional[BirthFlowConfig] = None):
        self.config = config or BirthFlowConfig()
        
        # In-memory storage (TODO: replace with DB)
        self._accounts: Dict[str, Account] = {}
        self._metrics: Dict[str, AccountWarmupMetrics] = {}
        self._risk_profiles: Dict[str, AccountRiskProfile] = {}
        self._logs: List[AccountLifecycleLog] = []
        
        logger.info("AccountBirthFlowStateMachine initialized")
    
    # ========================================================================
    # PUBLIC API - STATE TRANSITIONS
    # ========================================================================
    
    def advance_state(
        self,
        account_id: str,
        force: bool = False,
        reason: str = ""
    ) -> Tuple[bool, str]:
        """
        Avanza el estado de una cuenta al siguiente estado válido.
        
        Args:
            account_id: ID de la cuenta
            force: Si True, omite validaciones (solo para admin)
            reason: Razón del avance (opcional)
        
        Returns:
            (success, message)
        """
        account = self._accounts.get(account_id)
        if not account:
            return False, f"Account {account_id} not found"
        
        logger.info(f"Attempting to advance state for {account_id} from {account.current_state.value}")
        
        # Determine next state
        next_state = self._determine_next_state(account)
        if not next_state:
            return False, f"No valid next state from {account.current_state.value}"
        
        # Validate transition (unless forced)
        if not force:
            valid, msg = self.validate_transition(account_id, next_state)
            if not valid:
                logger.warning(f"Transition validation failed: {msg}")
                return False, msg
        
        # Execute transition
        success, msg = self._execute_transition(account_id, next_state, reason or "auto_advance")
        
        if success:
            logger.info(f"✅ Advanced {account_id}: {account.current_state.value} → {next_state.value}")
        else:
            logger.error(f"❌ Failed to advance {account_id}: {msg}")
        
        return success, msg
    
    def validate_transition(
        self,
        account_id: str,
        target_state: AccountState
    ) -> Tuple[bool, str]:
        """
        Valida si una transición es permitida.
        
        Checks:
        - Estado destino es válido
        - Métricas cumplen requisitos
        - Riesgo está bajo control
        - Tiempo mínimo en estado actual
        
        Returns:
            (is_valid, reason)
        """
        account = self._accounts.get(account_id)
        if not account:
            return False, "Account not found"
        
        # Check if transition is allowed
        if target_state not in ALLOWED_TRANSITIONS.get(account.current_state, []):
            return False, f"Transition {account.current_state.value} → {target_state.value} not allowed"
        
        # Check if account is locked
        if account.metadata.get("locked", False):
            return False, "Account is locked"
        
        # Special case: transitions to COOLDOWN/PAUSED/RETIRED always allowed
        if target_state in [AccountState.COOLDOWN, AccountState.PAUSED, AccountState.RETIRED]:
            return True, "Emergency transition allowed"
        
        # Check time in current state
        time_in_state = (datetime.now() - account.state_entered_at).days
        
        if account.current_state == AccountState.W1_3:
            if time_in_state < self.config.w1_3_min_days:
                return False, f"Must stay in W1_3 for at least {self.config.w1_3_min_days} days"
        
        elif account.current_state == AccountState.W4_7:
            if time_in_state < self.config.w4_7_min_days:
                return False, f"Must stay in W4_7 for at least {self.config.w4_7_min_days} days"
        
        elif account.current_state == AccountState.W8_14:
            if time_in_state < self.config.w8_14_min_days:
                return False, f"Must stay in W8_14 for at least {self.config.w8_14_min_days} days"
        
        # Check metrics (if available)
        metrics = self._metrics.get(account_id)
        if metrics and target_state in [AccountState.SECURED, AccountState.ACTIVE, AccountState.SCALING]:
            if metrics.maturity_score < self.config.min_maturity_score:
                return False, f"Maturity score too low: {metrics.maturity_score:.2f} < {self.config.min_maturity_score}"
            
            if metrics.readiness_level < self.config.min_readiness_level:
                return False, f"Readiness level too low: {metrics.readiness_level:.2f} < {self.config.min_readiness_level}"
        
        # Check risk
        risk_profile = self._risk_profiles.get(account_id)
        if risk_profile:
            if risk_profile.total_risk_score > self.config.max_risk_score:
                return False, f"Risk score too high: {risk_profile.total_risk_score:.2f} > {self.config.max_risk_score}"
            
            if risk_profile.risk_level in [AccountRiskLevel.HIGH, AccountRiskLevel.CRITICAL]:
                return False, f"Risk level too high: {risk_profile.risk_level.value}"
        
        return True, "Validation passed"
    
    def rollback_on_risk(
        self,
        account_id: str,
        reason: str = "risk_detected"
    ) -> Tuple[bool, str]:
        """
        Rollback de estado por detección de riesgo.
        
        Retrocede al estado anterior seguro o COOLDOWN.
        """
        if not self.config.enable_auto_rollback:
            return False, "Auto-rollback disabled"
        
        account = self._accounts.get(account_id)
        if not account:
            return False, "Account not found"
        
        logger.warning(f"⚠️ Rollback triggered for {account_id}: {reason}")
        
        # Determine rollback state
        current = account.current_state
        
        if current in [AccountState.ACTIVE, AccountState.SCALING]:
            rollback_state = AccountState.SECURED
        elif current == AccountState.SECURED:
            rollback_state = AccountState.W8_14
        elif current in [AccountState.W8_14, AccountState.W4_7, AccountState.W1_3]:
            rollback_state = AccountState.COOLDOWN
        else:
            rollback_state = AccountState.COOLDOWN
        
        # Execute rollback
        return self._execute_transition(
            account_id,
            rollback_state,
            f"rollback: {reason}"
        )
    
    def lock_state_on_violation(
        self,
        account_id: str,
        violation_reason: str
    ) -> Tuple[bool, str]:
        """
        Bloquea una cuenta por violación de políticas.
        
        Pausa la cuenta y marca como locked.
        """
        account = self._accounts.get(account_id)
        if not account:
            return False, "Account not found"
        
        logger.error(f"🔒 Locking account {account_id}: {violation_reason}")
        
        # Set lock flag
        account.metadata["locked"] = True
        account.metadata["lock_reason"] = violation_reason
        account.metadata["locked_at"] = datetime.now().isoformat()
        account.requires_manual_review = True
        
        # Transition to PAUSED
        success, msg = self._execute_transition(
            account_id,
            AccountState.PAUSED,
            f"locked: {violation_reason}"
        )
        
        if success:
            # Log critical event
            self._log_event(
                account_id=account_id,
                event_type="lock_violation",
                reason=violation_reason,
                from_state=account.current_state,
                to_state=AccountState.PAUSED,
                triggered_by="policy"
            )
        
        return success, msg
    
    # ========================================================================
    # ACCOUNT MANAGEMENT
    # ========================================================================
    
    def create_account(
        self,
        account_id: str,
        platform: str,
        **kwargs
    ) -> Account:
        """
        Crea una nueva cuenta en estado CREATED.
        
        Args:
            account_id: ID único
            platform: Plataforma (tiktok, instagram, youtube_shorts)
            **kwargs: Campos adicionales
        
        Returns:
            Account creada
        """
        from .account_models import PlatformType
        
        # Convert platform string to enum
        platform_enum = PlatformType(platform)
        
        account = Account(
            account_id=account_id,
            platform=platform_enum,
            current_state=AccountState.CREATED,
            state_entered_at=datetime.now(),
            **kwargs
        )
        
        self._accounts[account_id] = account
        
        # Initialize metrics
        self._metrics[account_id] = AccountWarmupMetrics(
            account_id=account_id,
            warmup_day=0,
            warmup_phase=AccountState.CREATED
        )
        
        # Initialize risk profile
        self._risk_profiles[account_id] = AccountRiskProfile(
            account_id=account_id
        )
        
        # Log creation
        self._log_event(
            account_id=account_id,
            event_type="account_created",
            to_state=AccountState.CREATED,
            reason="initial_creation"
        )
        
        logger.info(f"✅ Created account {account_id} ({platform})")
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        return self._accounts.get(account_id)
    
    def get_metrics(self, account_id: str) -> Optional[AccountWarmupMetrics]:
        """Get warmup metrics for account"""
        return self._metrics.get(account_id)
    
    def get_risk_profile(self, account_id: str) -> Optional[AccountRiskProfile]:
        """Get risk profile for account"""
        return self._risk_profiles.get(account_id)
    
    def get_lifecycle_logs(
        self,
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AccountLifecycleLog]:
        """Get lifecycle logs (all or for specific account)"""
        if account_id:
            logs = [log for log in self._logs if log.account_id == account_id]
        else:
            logs = self._logs
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    # ========================================================================
    # INTERNAL - TRANSITION EXECUTION
    # ========================================================================
    
    def _determine_next_state(self, account: Account) -> Optional[AccountState]:
        """Determina el siguiente estado válido"""
        current = account.current_state
        
        # Normal progression path
        progression = {
            AccountState.CREATED: AccountState.W1_3,
            AccountState.W1_3: AccountState.W4_7,
            AccountState.W4_7: AccountState.W8_14,
            AccountState.W8_14: AccountState.SECURED,
            AccountState.SECURED: AccountState.ACTIVE,
            AccountState.ACTIVE: AccountState.SCALING,
        }
        
        return progression.get(current)
    
    def _execute_transition(
        self,
        account_id: str,
        target_state: AccountState,
        reason: str
    ) -> Tuple[bool, str]:
        """Ejecuta la transición de estado"""
        account = self._accounts.get(account_id)
        if not account:
            return False, "Account not found"
        
        from_state = account.current_state
        
        # Update account state
        account.current_state = target_state
        account.state_entered_at = datetime.now()
        
        # Update warmup day if entering warmup state
        if target_state == AccountState.W1_3:
            account.warmup_day = 1
        elif target_state == AccountState.W4_7:
            account.warmup_day = 4
        elif target_state == AccountState.W8_14:
            account.warmup_day = 8
        elif target_state == AccountState.SECURED:
            account.secured_at = datetime.now()
        
        # Update metrics
        metrics = self._metrics.get(account_id)
        if metrics:
            metrics.warmup_phase = target_state
            if target_state == AccountState.SECURED:
                metrics.warmup_completed = True
        
        # Log transition
        self._log_event(
            account_id=account_id,
            event_type="state_transition",
            from_state=from_state,
            to_state=target_state,
            reason=reason
        )
        
        return True, f"Transitioned to {target_state.value}"
    
    def _log_event(
        self,
        account_id: str,
        event_type: str,
        reason: str = "",
        from_state: Optional[AccountState] = None,
        to_state: Optional[AccountState] = None,
        triggered_by: str = "system"
    ):
        """Registra un evento en el audit log"""
        
        # Get current risk score
        risk_profile = self._risk_profiles.get(account_id)
        risk_score = risk_profile.total_risk_score if risk_profile else 0.0
        
        # Get metrics snapshot
        metrics = self._metrics.get(account_id)
        metrics_snapshot = {}
        if metrics:
            metrics_snapshot = {
                "maturity_score": metrics.maturity_score,
                "readiness_level": metrics.readiness_level,
                "warmup_day": metrics.warmup_day,
            }
        
        log = AccountLifecycleLog(
            log_id=f"log_{uuid.uuid4().hex[:12]}",
            account_id=account_id,
            timestamp=datetime.now(),
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            risk_score=risk_score,
            metrics_snapshot=metrics_snapshot,
            triggered_by=triggered_by
        )
        
        self._logs.append(log)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_test_account(
    account_id: str = "test_acc_001",
    platform: str = "tiktok"
) -> Tuple[AccountBirthFlowStateMachine, Account]:
    """Helper para crear cuenta de prueba"""
    
    machine = AccountBirthFlowStateMachine()
    account = machine.create_account(account_id, platform)
    
    return machine, account


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "BirthFlowConfig",
    "ALLOWED_TRANSITIONS",
    "AccountBirthFlowStateMachine",
    "create_test_account",
]
