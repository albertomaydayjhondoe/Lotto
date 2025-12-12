"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Proposal Evaluator

Evaluador y prefiltro de propuestas que:
- Valida constraints de seguridad (sync limits, official assets)
- Estima riesgos (shadowban, correlation, policy)
- Rankea por prioridad
- Filtra propuestas antes de enviar a Supervisor (Sprint 10)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from .sat_intel_contracts import (
    ContentProposal,
    ProposalEvaluation,
    ProposalStatus,
    ProposalPriority,
    RiskLevel,
    AccountProfile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class EvaluatorConfig:
    """Configuración del evaluator"""
    
    # Security constraints
    max_simultaneous_posts: int = 3
    max_posts_per_hour: int = 10
    min_gap_minutes: int = 5
    
    # Risk thresholds
    max_risk_score: float = 0.8
    shadowban_risk_weight: float = 0.3
    correlation_risk_weight: float = 0.4
    policy_risk_weight: float = 0.3
    
    # Quality thresholds
    min_clip_score: float = 0.4
    min_timing_score: float = 0.3
    
    # Flags
    require_human_review_threshold: float = 0.7
    strict_mode: bool = False


# ============================================================================
# PROPOSAL EVALUATOR
# ============================================================================

class ProposalEvaluator:
    """
    Evaluador de propuestas con constraints y risk assessment.
    
    Responsabilidades:
    - Validar constraints de seguridad
    - Calcular risk scores
    - Filtrar propuestas inválidas
    - Rankear por prioridad
    - Generar recomendaciones de ajuste
    """
    
    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        logger.info(f"ProposalEvaluator initialized (strict_mode={self.config.strict_mode})")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def evaluate_proposal(
        self,
        proposal: ContentProposal,
        account: AccountProfile,
        active_proposals: Optional[List[ContentProposal]] = None
    ) -> ProposalEvaluation:
        """
        Evalúa una propuesta individual.
        
        Args:
            proposal: Propuesta a evaluar
            account: Perfil de la cuenta
            active_proposals: Propuestas ya activas (para sync checks)
        
        Returns:
            ProposalEvaluation con decision y scores
        """
        logger.debug(f"Evaluating proposal {proposal.proposal_id} for account {proposal.account_id}")
        
        active_proposals = active_proposals or []
        
        # 1. Safety checks
        safety_pass, safety_reason = self._check_safety(proposal, account)
        
        # 2. Sync limit checks
        sync_pass, sync_reason = self._check_sync_limits(proposal, active_proposals)
        
        # 3. Quality checks
        quality_pass, quality_reason = self._check_quality(proposal)
        
        # 4. Risk assessment
        risk_scores = self._assess_risks(proposal, account)
        total_risk = sum(risk_scores.values())
        
        # 5. Policy compliance
        policy_pass, policy_reason = self._check_policy_compliance(proposal)
        
        # Decision
        approved = (
            safety_pass and
            sync_pass and
            quality_pass and
            policy_pass and
            total_risk <= self.config.max_risk_score
        )
        
        # Rejection reason
        rejection_reason = None
        if not approved:
            reasons = []
            if not safety_pass:
                reasons.append(f"Safety: {safety_reason}")
            if not sync_pass:
                reasons.append(f"Sync: {sync_reason}")
            if not quality_pass:
                reasons.append(f"Quality: {quality_reason}")
            if not policy_pass:
                reasons.append(f"Policy: {policy_reason}")
            if total_risk > self.config.max_risk_score:
                reasons.append(f"Risk too high ({total_risk:.2f})")
            
            rejection_reason = "; ".join(reasons)
        
        # Human review flag
        requires_human_review = (
            total_risk >= self.config.require_human_review_threshold or
            proposal.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH] or
            (self.config.strict_mode and not approved)
        )
        
        # Recommended adjustments
        recommendations = self._generate_recommendations(
            proposal, account, risk_scores, approved
        )
        
        evaluation = ProposalEvaluation(
            proposal_id=proposal.proposal_id,
            evaluated_at=datetime.now(),
            approved=approved,
            rejection_reason=rejection_reason,
            safety_score=1.0 if safety_pass else 0.0,
            policy_compliance_score=1.0 if policy_pass else 0.0,
            timing_quality_score=proposal.timing_window.optimal_score,
            content_quality_score=proposal.clip_score.total_score,
            requires_human_review=requires_human_review,
            has_official_assets=self._has_official_assets(proposal),
            exceeds_sync_limit=not sync_pass,
            recommended_adjustments=recommendations,
            evaluator_id="auto"
        )
        
        logger.debug(f"Proposal {proposal.proposal_id}: approved={approved}, risk={total_risk:.2f}")
        return evaluation
    
    def batch_evaluate(
        self,
        proposals: List[ContentProposal],
        accounts: Dict[str, AccountProfile]
    ) -> List[ProposalEvaluation]:
        """Evalúa batch de propuestas"""
        evaluations = []
        active_proposals = []
        
        for proposal in proposals:
            account = accounts.get(proposal.account_id)
            if not account:
                logger.warning(f"Account {proposal.account_id} not found, skipping proposal")
                continue
            
            evaluation = self.evaluate_proposal(proposal, account, active_proposals)
            evaluations.append(evaluation)
            
            # Si es aprobada, add a active_proposals para sync checks
            if evaluation.approved:
                active_proposals.append(proposal)
        
        logger.info(f"Evaluated {len(evaluations)} proposals: "
                   f"{sum(1 for e in evaluations if e.approved)} approved")
        
        return evaluations
    
    def filter_and_rank(
        self,
        proposals: List[ContentProposal],
        accounts: Dict[str, AccountProfile],
        max_proposals: Optional[int] = None
    ) -> List[Tuple[ContentProposal, ProposalEvaluation]]:
        """
        Filtra y rankea propuestas.
        
        Returns:
            Lista de (proposal, evaluation) ordenada por prioridad/score
        """
        evaluations = self.batch_evaluate(proposals, accounts)
        
        # Pair proposals con evaluations
        paired = list(zip(proposals, evaluations))
        
        # Filtrar aprobadas
        approved = [(p, e) for p, e in paired if e.approved]
        
        # Rankear por prioridad y score
        ranked = sorted(
            approved,
            key=lambda x: (
                self._priority_to_int(x[0].priority),
                x[0].clip_score.total_score,
                -x[0].risk_score
            ),
            reverse=True
        )
        
        # Limit si se especifica
        if max_proposals:
            ranked = ranked[:max_proposals]
        
        logger.info(f"Filtered and ranked: {len(ranked)} / {len(proposals)} proposals")
        return ranked
    
    # ========================================================================
    # SAFETY CHECKS
    # ========================================================================
    
    def _check_safety(self, proposal: ContentProposal, account: AccountProfile) -> Tuple[bool, str]:
        """Valida safety constraints"""
        
        # Check shadowban signals
        if account.shadowban_signals >= 2:
            return False, f"Account has {account.shadowban_signals} shadowban signals"
        
        # Check correlation signals
        if account.correlation_signals >= 1:
            return False, f"Account has {account.correlation_signals} correlation signals"
        
        # Check warmup constraints
        if not account.warmup_completed and proposal.priority == ProposalPriority.CRITICAL:
            return False, "Cannot post CRITICAL priority during warmup"
        
        return True, ""
    
    def _check_sync_limits(
        self,
        proposal: ContentProposal,
        active_proposals: List[ContentProposal]
    ) -> Tuple[bool, str]:
        """Valida sync limits"""
        
        # Contar propuestas en la misma ventana de tiempo
        proposal_time = proposal.timing_window.start_time
        
        simultaneous_count = sum(
            1 for p in active_proposals
            if abs((p.timing_window.start_time - proposal_time).total_seconds()) < 300  # 5 min
        )
        
        if simultaneous_count >= self.config.max_simultaneous_posts:
            return False, f"Exceeds max simultaneous posts ({simultaneous_count}/{self.config.max_simultaneous_posts})"
        
        # Check posts per hour
        hour_window_start = proposal_time - timedelta(hours=1)
        posts_in_hour = sum(
            1 for p in active_proposals
            if hour_window_start <= p.timing_window.start_time <= proposal_time
        )
        
        if posts_in_hour >= self.config.max_posts_per_hour:
            return False, f"Exceeds max posts per hour ({posts_in_hour}/{self.config.max_posts_per_hour})"
        
        # Check min gap
        if active_proposals:
            closest_gap = min(
                abs((p.timing_window.start_time - proposal_time).total_seconds()) / 60
                for p in active_proposals
            )
            
            if closest_gap < self.config.min_gap_minutes:
                return False, f"Gap too small ({closest_gap:.1f} < {self.config.min_gap_minutes} min)"
        
        return True, ""
    
    def _check_quality(self, proposal: ContentProposal) -> Tuple[bool, str]:
        """Valida quality thresholds"""
        
        if proposal.clip_score.total_score < self.config.min_clip_score:
            return False, f"Clip score too low ({proposal.clip_score.total_score:.2f})"
        
        if proposal.timing_window.optimal_score < self.config.min_timing_score:
            return False, f"Timing score too low ({proposal.timing_window.optimal_score:.2f})"
        
        return True, ""
    
    def _check_policy_compliance(self, proposal: ContentProposal) -> Tuple[bool, str]:
        """Valida policy compliance"""
        
        # Check official assets flag
        if self._has_official_assets(proposal):
            if "official_assets_approved" not in proposal.metadata:
                return False, "Official assets require explicit approval flag"
        
        # Check content type restrictions (example)
        # TODO: Implement real policy checks
        
        return True, ""
    
    # ========================================================================
    # RISK ASSESSMENT
    # ========================================================================
    
    def _assess_risks(
        self,
        proposal: ContentProposal,
        account: AccountProfile
    ) -> Dict[str, float]:
        """
        Calcula risk scores por categoría.
        
        Returns:
            Dict con shadowban_risk, correlation_risk, policy_risk
        """
        # Shadowban risk
        shadowban_risk = 0.0
        if account.shadowban_signals > 0:
            shadowban_risk = min(0.5 + (account.shadowban_signals * 0.2), 1.0)
        
        # Correlation risk
        correlation_risk = 0.0
        if account.correlation_signals > 0:
            correlation_risk = min(0.4 + (account.correlation_signals * 0.3), 1.0)
        
        # Timing pattern risk
        if account.last_post_at:
            gap_hours = (proposal.timing_window.start_time - account.last_post_at).total_seconds() / 3600
            if abs(gap_hours - 24.0) < 0.5:  # Exactamente 24h
                correlation_risk += 0.2
        
        # Policy risk
        policy_risk = 0.0
        if self._has_official_assets(proposal):
            policy_risk += 0.3
        
        # Content reuse risk
        if proposal.clip_score.uniqueness_score < 0.5:
            policy_risk += 0.2
        
        return {
            "shadowban_risk": shadowban_risk,
            "correlation_risk": correlation_risk,
            "policy_risk": min(policy_risk, 1.0),
        }
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _has_official_assets(self, proposal: ContentProposal) -> bool:
        """Check si usa official assets"""
        return proposal.metadata.get("uses_official_assets", False)
    
    def _priority_to_int(self, priority: ProposalPriority) -> int:
        """Convert priority to int for sorting"""
        mapping = {
            ProposalPriority.LOW: 1,
            ProposalPriority.MEDIUM: 2,
            ProposalPriority.HIGH: 3,
            ProposalPriority.CRITICAL: 4,
        }
        return mapping.get(priority, 1)
    
    def _generate_recommendations(
        self,
        proposal: ContentProposal,
        account: AccountProfile,
        risk_scores: Dict[str, float],
        approved: bool
    ) -> List[str]:
        """Genera recomendaciones de ajuste"""
        recommendations = []
        
        if not approved:
            # Timing adjustments
            if proposal.timing_window.optimal_score < 0.5:
                recommendations.append("Consider delaying to optimal window")
            
            # Quality improvements
            if proposal.clip_score.niche_match_score < 0.4:
                recommendations.append("Content has weak niche match, consider alternative")
            
            if proposal.clip_score.uniqueness_score < 0.6:
                recommendations.append("Content recently used, consider fresh content")
            
            # Risk mitigation
            if risk_scores["shadowban_risk"] > 0.5:
                recommendations.append("High shadowban risk, pause account activity")
            
            if risk_scores["correlation_risk"] > 0.5:
                recommendations.append("High correlation risk, increase timing diversity")
        
        if not recommendations:
            recommendations.append("No adjustments needed")
        
        return recommendations


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "EvaluatorConfig",
    "ProposalEvaluator",
]
