"""
SPRINT 12.1 - Human-Assisted Warm-Up Scheduler
Module: Warmup to Autonomy Bridge

Gestiona la transición de warmup humano → automatización completa.
Solo permite SECURED si cumple todos los criterios.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .account_models import Account, AccountState, AccountWarmupMetrics, AccountRiskProfile
from .human_action_verifier import VerificationResult

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class WarmupToAutonomyBridgeConfig:
    """Configuración del bridge"""
    
    # Minimum requirements for SECURED
    min_warmup_days: int = 7  # At least 7 days
    max_warmup_days: int = 14  # Max 14 days
    
    # Verification requirements
    min_completed_tasks: int = 5  # At least 5 successful tasks
    min_success_rate: float = 0.85  # 85% success rate
    
    # Risk thresholds
    max_total_risk: float = 0.35  # Total risk must be < 0.35
    max_shadowban_risk: float = 0.25
    max_correlation_risk: float = 0.30
    
    # Metrics thresholds
    min_maturity_score: float = 0.60
    min_readiness_level: float = 0.65
    
    # Behavioral requirements
    min_action_diversity: float = 0.50  # At least 50% action diversity
    max_mechanical_score: float = 0.30  # < 30% mechanical behavior
    
    # Fingerprint stability
    require_stable_fingerprint: bool = True
    require_stable_hours: bool = True  # Consistent activity hours


# ============================================================================
# TRANSITION DECISION
# ============================================================================

@dataclass
class TransitionDecision:
    """Decisión de transición a autonomía"""
    
    account_id: str
    can_transition: bool
    target_state: AccountState
    reason: str
    
    # Requirements check
    requirements_met: Dict[str, bool]
    requirements_scores: Dict[str, float]
    
    # Recommendations
    blockers: List[str]  # What's blocking transition
    recommendations: List[str]  # What to improve
    
    # Timeline
    estimated_days_remaining: int
    
    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "can_transition": self.can_transition,
            "new_state": self.target_state.value if self.can_transition else None,
            "reason": self.reason,
            "requirements_met": self.requirements_met,
            "requirements_scores": self.requirements_scores,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
            "estimated_days_remaining": self.estimated_days_remaining
        }


# ============================================================================
# WARMUP TO AUTONOMY BRIDGE
# ============================================================================

class WarmupToAutonomyBridge:
    """
    Bridge de transición warmup → autonomía.
    
    Responsabilidades:
    - Evaluar si cuenta está lista para SECURED
    - Validar todos los criterios
    - Proveer feedback detallado
    - Recomendar acciones para completar warmup
    
    REGLA FUNDAMENTAL:
    Solo permite automatización completa si TODOS los criterios se cumplen.
    """
    
    def __init__(self, config: Optional[WarmupToAutonomyBridgeConfig] = None):
        self.config = config or WarmupToAutonomyBridgeConfig()
        
        # Transition history
        self._transition_history: Dict[str, List[TransitionDecision]] = {}
        
        logger.info("WarmupToAutonomyBridge initialized")
    
    # ========================================================================
    # PUBLIC API - TRANSITION EVALUATION
    # ========================================================================
    
    def evaluate_transition_readiness(
        self,
        account: Account,
        metrics: AccountWarmupMetrics,
        risk_profile: AccountRiskProfile,
        verification_history: List[VerificationResult],
        task_completion_rate: float
    ) -> TransitionDecision:
        """
        Evalúa si la cuenta está lista para transición a SECURED.
        
        Args:
            account: Cuenta a evaluar
            metrics: Métricas de warmup
            risk_profile: Perfil de riesgo
            verification_history: Historial de verificaciones
            task_completion_rate: Tasa de completación de tareas (0-1)
        
        Returns:
            TransitionDecision con resultado detallado
        """
        requirements_met = {}
        requirements_scores = {}
        blockers = []
        recommendations = []
        
        # 1. Check warmup duration
        days_in_warmup = (datetime.now() - account.created_at).days
        
        if days_in_warmup < self.config.min_warmup_days:
            requirements_met["warmup_duration"] = False
            blockers.append(f"Need {self.config.min_warmup_days - days_in_warmup} more days in warmup")
        else:
            requirements_met["warmup_duration"] = True
        
        requirements_scores["warmup_days"] = days_in_warmup / self.config.min_warmup_days
        
        # 2. Check completed tasks
        completed_tasks = len([v for v in verification_history if v.verification_passed])
        
        if completed_tasks < self.config.min_completed_tasks:
            requirements_met["completed_tasks"] = False
            blockers.append(f"Need {self.config.min_completed_tasks - completed_tasks} more successful tasks")
        else:
            requirements_met["completed_tasks"] = True
        
        requirements_scores["completed_tasks"] = completed_tasks / self.config.min_completed_tasks
        
        # 3. Check success rate
        if task_completion_rate < self.config.min_success_rate:
            requirements_met["success_rate"] = False
            blockers.append(f"Success rate too low: {task_completion_rate:.1%} < {self.config.min_success_rate:.1%}")
            recommendations.append("Complete more tasks successfully")
        else:
            requirements_met["success_rate"] = True
        
        requirements_scores["success_rate"] = task_completion_rate
        
        # 4. Check total risk
        if risk_profile.total_risk_score > self.config.max_total_risk:
            requirements_met["total_risk"] = False
            blockers.append(f"Risk too high: {risk_profile.total_risk_score:.2f} > {self.config.max_total_risk:.2f}")
            recommendations.append("Reduce risky behaviors, vary timing patterns")
        else:
            requirements_met["total_risk"] = True
        
        requirements_scores["total_risk"] = 1.0 - risk_profile.total_risk_score
        
        # 5. Check shadowban risk
        if risk_profile.shadowban_risk > self.config.max_shadowban_risk:
            requirements_met["shadowban_risk"] = False
            blockers.append(f"Shadowban risk too high: {risk_profile.shadowban_risk:.2f}")
            recommendations.append("Increase engagement, diversify content")
        else:
            requirements_met["shadowban_risk"] = True
        
        # 6. Check correlation risk
        if risk_profile.correlation_risk > self.config.max_correlation_risk:
            requirements_met["correlation_risk"] = False
            blockers.append(f"Correlation risk too high: {risk_profile.correlation_risk:.2f}")
            recommendations.append("Ensure unique fingerprint and IP")
        else:
            requirements_met["correlation_risk"] = True
        
        # 7. Check maturity score
        if metrics.maturity_score < self.config.min_maturity_score:
            requirements_met["maturity_score"] = False
            blockers.append(f"Maturity too low: {metrics.maturity_score:.2f} < {self.config.min_maturity_score:.2f}")
            recommendations.append("Complete more actions, build engagement")
        else:
            requirements_met["maturity_score"] = True
        
        requirements_scores["maturity_score"] = metrics.maturity_score
        
        # 8. Check readiness level
        if metrics.readiness_level < self.config.min_readiness_level:
            requirements_met["readiness_level"] = False
            blockers.append(f"Readiness too low: {metrics.readiness_level:.2f}")
        else:
            requirements_met["readiness_level"] = True
        
        requirements_scores["readiness_level"] = metrics.readiness_level
        
        # 9. Check action diversity
        if verification_history:
            avg_diversity = sum(v.action_diversity_score for v in verification_history) / len(verification_history)
            
            if avg_diversity < self.config.min_action_diversity:
                requirements_met["action_diversity"] = False
                blockers.append(f"Action diversity too low: {avg_diversity:.2f}")
                recommendations.append("Vary your actions more (scroll, like, comment, follow)")
            else:
                requirements_met["action_diversity"] = True
            
            requirements_scores["action_diversity"] = avg_diversity
        else:
            requirements_met["action_diversity"] = False
            blockers.append("No verification history")
        
        # 10. Check mechanical score
        if verification_history:
            avg_mechanical = sum(v.mechanical_score for v in verification_history) / len(verification_history)
            
            if avg_mechanical > self.config.max_mechanical_score:
                requirements_met["mechanical_score"] = False
                blockers.append(f"Behavior too mechanical: {avg_mechanical:.2f}")
                recommendations.append("Vary timing intervals, be less predictable")
            else:
                requirements_met["mechanical_score"] = True
            
            requirements_scores["mechanical_score"] = 1.0 - avg_mechanical
        else:
            requirements_met["mechanical_score"] = False
        
        # Decision
        can_transition = all(requirements_met.values())
        
        if can_transition:
            reason = "Warm-up completed with stable human pattern"
            target_state = AccountState.SECURED
            estimated_days = 0
        else:
            failed_count = len([v for v in requirements_met.values() if not v])
            reason = f"{failed_count} requirement(s) not met"
            target_state = account.current_state
            
            # Estimate days remaining
            if days_in_warmup < self.config.min_warmup_days:
                estimated_days = self.config.min_warmup_days - days_in_warmup
            else:
                estimated_days = 1  # At least 1 more day to improve
        
        decision = TransitionDecision(
            account_id=account.account_id,
            can_transition=can_transition,
            target_state=target_state,
            reason=reason,
            requirements_met=requirements_met,
            requirements_scores=requirements_scores,
            blockers=blockers,
            recommendations=recommendations,
            estimated_days_remaining=estimated_days
        )
        
        # Store decision
        if account.account_id not in self._transition_history:
            self._transition_history[account.account_id] = []
        self._transition_history[account.account_id].append(decision)
        
        if can_transition:
            logger.info(f"✅ {account.account_id} ready for SECURED transition")
        else:
            logger.info(f"⏳ {account.account_id} not ready: {', '.join(blockers[:2])}")
        
        return decision
    
    def get_progress_summary(
        self,
        account: Account,
        metrics: AccountWarmupMetrics,
        risk_profile: AccountRiskProfile,
        verification_history: List[VerificationResult],
        task_completion_rate: float
    ) -> Dict:
        """
        Genera resumen de progreso hacia autonomía.
        
        Returns:
            Dict con porcentajes y status
        """
        # Evaluate (without storing)
        decision = self.evaluate_transition_readiness(
            account, metrics, risk_profile, verification_history, task_completion_rate
        )
        
        total_requirements = len(decision.requirements_met)
        met_requirements = sum(1 for v in decision.requirements_met.values() if v)
        
        return {
            "account_id": account.account_id,
            "overall_progress": met_requirements / total_requirements,
            "requirements_progress": {
                k: "✅" if v else "❌" for k, v in decision.requirements_met.items()
            },
            "scores": decision.requirements_scores,
            "can_transition": decision.can_transition,
            "days_remaining": decision.estimated_days_remaining,
            "next_steps": decision.recommendations[:3] if decision.recommendations else ["Keep completing daily tasks"]
        }
    
    def get_transition_history(self, account_id: str) -> List[TransitionDecision]:
        """Obtiene historial de evaluaciones"""
        return self._transition_history.get(account_id, [])


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "WarmupToAutonomyBridgeConfig",
    "TransitionDecision",
    "WarmupToAutonomyBridge",
]
