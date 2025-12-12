"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Orchestrator BirthFlow Bridge

Puente entre Orchestrator y Account BirthFlow.
El Orchestrator NO puede actuar sin consultar esta capa.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .account_models import (
    Account,
    AccountState,
    ActionType,
    can_automate,
    get_daily_limit,
)
from .account_birthflow import AccountBirthFlowStateMachine
from .warmup_policy_engine import WarmupPolicyEngine
from .account_security_layer import AccountSecurityLayer
from .account_metrics_collector import AccountMetricsCollector

logger = logging.getLogger(__name__)


# ============================================================================
# BRIDGE RESPONSES
# ============================================================================

@dataclass
class BridgeActionResponse:
    """Respuesta del bridge sobre una acción"""
    
    allowed: bool
    reason: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BridgeLimitsResponse:
    """Respuesta con límites diarios"""
    
    daily_limits: Dict[ActionType, int]
    current_counts: Dict[ActionType, int]
    remaining: Dict[ActionType, int]


# ============================================================================
# ORCHESTRATOR BIRTHFLOW BRIDGE
# ============================================================================

class OrchestratorBirthFlowBridge:
    """
    Puente de autorización entre Orchestrator y Account BirthFlow.
    
    Responsabilidades:
    - Validar si una acción está permitida
    - Retornar límites diarios disponibles
    - Validar si puede cambiar estado
    - Proveer recomendaciones
    
    REGLA FUNDAMENTAL:
    El Orchestrator NO puede ejecutar NINGUNA acción sin llamar a este bridge.
    """
    
    def __init__(
        self,
        state_machine: AccountBirthFlowStateMachine,
        warmup_engine: WarmupPolicyEngine,
        security_layer: AccountSecurityLayer,
        metrics_collector: AccountMetricsCollector
    ):
        self.state_machine = state_machine
        self.warmup_engine = warmup_engine
        self.security_layer = security_layer
        self.metrics_collector = metrics_collector
        
        logger.info("OrchestratorBirthFlowBridge initialized")
    
    # ========================================================================
    # PUBLIC API - ACTION AUTHORIZATION
    # ========================================================================
    
    def can_perform_action(
        self,
        account_id: str,
        action_type: ActionType
    ) -> BridgeActionResponse:
        """
        Valida si una acción puede ejecutarse AHORA.
        
        Checks:
        - Cuenta existe y no está locked
        - Estado permite esta acción
        - No excede límite diario
        - Security checks passed
        - Warmup policy OK
        
        Returns:
            BridgeActionResponse
        """
        # Get account
        account = self.state_machine.get_account(account_id)
        if not account:
            return BridgeActionResponse(
                allowed=False,
                reason="Account not found"
            )
        
        # Check if locked
        if account.metadata.get("locked", False):
            return BridgeActionResponse(
                allowed=False,
                reason="Account is locked"
            )
        
        # Check if requires manual review
        if account.requires_manual_review:
            return BridgeActionResponse(
                allowed=False,
                reason="Account requires manual review"
            )
        
        # Check state allows automation
        if not can_automate(account.current_state):
            return BridgeActionResponse(
                allowed=False,
                reason=f"State {account.current_state.value} does not allow automation"
            )
        
        # Check daily limits
        daily_limit = get_daily_limit(account.current_state, action_type)
        # TODO: Get actual current count from metrics
        # For now, assume we can check
        
        if daily_limit == 0:
            return BridgeActionResponse(
                allowed=False,
                reason=f"Action {action_type.value} not allowed in state {account.current_state.value}"
            )
        
        # Check warmup policy
        can_execute, warmup_reason = self.warmup_engine.can_execute_action(
            account_id,
            action_type,
            account.current_state
        )
        
        if not can_execute:
            return BridgeActionResponse(
                allowed=False,
                reason=f"Warmup policy: {warmup_reason}"
            )
        
        # Check security
        all_passed, risk_level, reasons = self.security_layer.run_full_security_check(
            account_id,
            proxy_id=account.proxy_id,
            fingerprint_id=account.fingerprint_id
        )
        
        if not all_passed:
            return BridgeActionResponse(
                allowed=False,
                reason=f"Security check failed: {', '.join(reasons)}",
                metadata={"risk_level": risk_level.value}
            )
        
        # All checks passed
        return BridgeActionResponse(
            allowed=True,
            reason="OK",
            metadata={
                "daily_limit": daily_limit,
                "state": account.current_state.value
            }
        )
    
    def get_allowed_actions(
        self,
        account_id: str
    ) -> List[ActionType]:
        """
        Retorna las acciones permitidas para una cuenta en este momento.
        
        Returns:
            Lista de ActionType permitidos
        """
        account = self.state_machine.get_account(account_id)
        if not account:
            return []
        
        allowed = []
        
        for action_type in ActionType:
            response = self.can_perform_action(account_id, action_type)
            if response.allowed:
                allowed.append(action_type)
        
        return allowed
    
    def get_daily_limits(
        self,
        account_id: str
    ) -> Optional[BridgeLimitsResponse]:
        """
        Retorna límites diarios y conteo actual.
        
        Returns:
            BridgeLimitsResponse con límites, conteos y remaining
        """
        account = self.state_machine.get_account(account_id)
        if not account:
            return None
        
        metrics = self.state_machine.get_metrics(account_id)
        if not metrics:
            return None
        
        # Get daily limits
        daily_limits = {}
        current_counts = {}
        remaining = {}
        
        for action_type in ActionType:
            limit = get_daily_limit(account.current_state, action_type)
            daily_limits[action_type] = limit
            
            # Get current count (from metrics)
            if action_type == ActionType.VIEW:
                count = metrics.views_performed
            elif action_type == ActionType.LIKE:
                count = metrics.likes_performed
            elif action_type == ActionType.COMMENT:
                count = metrics.comments_performed
            elif action_type == ActionType.FOLLOW:
                count = metrics.follows_performed
            elif action_type == ActionType.POST:
                count = metrics.posts_performed
            else:
                count = 0
            
            current_counts[action_type] = count
            remaining[action_type] = max(0, limit - count)
        
        return BridgeLimitsResponse(
            daily_limits=daily_limits,
            current_counts=current_counts,
            remaining=remaining
        )
    
    def request_state_change(
        self,
        account_id: str,
        target_state: AccountState,
        reason: str = "orchestrator_request"
    ) -> Tuple[bool, str]:
        """
        El Orchestrator solicita un cambio de estado.
        
        NO ejecuta directamente, solo valida y si es válido, lo ejecuta.
        
        Returns:
            (success, message)
        """
        logger.info(f"Orchestrator requests state change for {account_id}: {target_state.value}")
        
        # Validate transition
        valid, msg = self.state_machine.validate_transition(account_id, target_state)
        
        if not valid:
            logger.warning(f"State change rejected: {msg}")
            return False, msg
        
        # Execute (using internal state machine method)
        success, msg = self.state_machine._execute_transition(
            account_id,
            target_state,
            f"orchestrator: {reason}"
        )
        
        if success:
            logger.info(f"✅ State change approved and executed: {target_state.value}")
        else:
            logger.error(f"❌ State change execution failed: {msg}")
        
        return success, msg
    
    # ========================================================================
    # PUBLIC API - RECOMMENDATIONS
    # ========================================================================
    
    def get_next_action_recommendation(
        self,
        account_id: str
    ) -> Optional[Tuple[ActionType, datetime]]:
        """
        Retorna la próxima acción recomendada y cuándo ejecutarla.
        
        Returns:
            (action_type, next_time) o None
        """
        account = self.state_machine.get_account(account_id)
        if not account:
            return None
        
        # Get allowed actions
        allowed = self.get_allowed_actions(account_id)
        if not allowed:
            return None
        
        # Get recommended actions from warmup engine
        recommended = self.warmup_engine.get_recommended_actions(account.current_state)
        
        # Find first allowed & recommended
        for action_type in recommended:
            if action_type in allowed:
                # Get next time
                next_time = self.warmup_engine.get_next_action_time(
                    account_id,
                    action_type,
                    account.current_state
                )
                
                return action_type, next_time
        
        return None
    
    def should_advance_state(
        self,
        account_id: str
    ) -> Tuple[bool, str]:
        """
        Indica si la cuenta debería avanzar de estado.
        
        Returns:
            (should_advance, reason)
        """
        account = self.state_machine.get_account(account_id)
        if not account:
            return False, "Account not found"
        
        # Check if in terminal state
        if account.current_state in [AccountState.RETIRED, AccountState.PAUSED]:
            return False, "Terminal or paused state"
        
        # Check time in state
        days_in_state = (datetime.now() - account.state_entered_at).days
        
        # Check with warmup engine
        can_advance, reason = self.warmup_engine.can_advance_to_next_phase(
            account_id,
            account.current_state,
            days_in_state
        )
        
        return can_advance, reason
    
    # ========================================================================
    # PUBLIC API - POST-ACTION RECORDING
    # ========================================================================
    
    def record_action_executed(
        self,
        account_id: str,
        action_type: ActionType,
        success: bool = True
    ):
        """
        Registra que una acción fue ejecutada.
        
        IMPORTANTE: El Orchestrator DEBE llamar esto después de cada acción.
        """
        # Record in warmup engine
        self.warmup_engine.record_action(account_id, action_type, success)
        
        # Record in security layer
        self.security_layer.record_action(account_id)
        
        # Record in metrics
        metrics = self.state_machine.get_metrics(account_id)
        if metrics:
            self.metrics_collector.record_action_performed(
                metrics,
                action_type.value.lower(),
                success
            )
        
        logger.debug(f"Recorded action: {account_id} {action_type.value} {'✓' if success else '✗'}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_orchestrator_bridge(
    state_machine: AccountBirthFlowStateMachine,
    warmup_engine: WarmupPolicyEngine,
    security_layer: AccountSecurityLayer,
    metrics_collector: AccountMetricsCollector
) -> OrchestratorBirthFlowBridge:
    """Helper para crear bridge con todos los componentes"""
    
    return OrchestratorBirthFlowBridge(
        state_machine=state_machine,
        warmup_engine=warmup_engine,
        security_layer=security_layer,
        metrics_collector=metrics_collector
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "BridgeActionResponse",
    "BridgeLimitsResponse",
    "OrchestratorBirthFlowBridge",
    "create_orchestrator_bridge",
]
