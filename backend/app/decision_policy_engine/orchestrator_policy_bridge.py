"""
Sprint 15: Decision Policy Engine - Orchestrator Bridge

Main interface between the Orchestrator and the Policy Engine.
No action executes without passing through this bridge.

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

from .decision_policy_models import (
    Policy,
    PolicyScope,
    PolicyActionType,
    SuccessSignal,
    AccountState
)
from .policy_registry import PolicyRegistry
from .policy_evaluator import PolicyEvaluator, PolicyEvaluationResult
from .policy_execution_guard import PolicyExecutionGuard, GuardResult
from .policy_learning_feedback import PolicyLearningFeedback


class ActionDecision(Enum):
    """Decision outcomes from the bridge"""
    APPROVED = "approved"
    REJECTED = "rejected"
    ABSTAINED = "abstained"
    REQUIRES_REVIEW = "requires_review"
    BLOCKED = "blocked"


@dataclass
class ActionRequest:
    """Request for action from Orchestrator"""
    request_id: str
    account_id: str
    platform: str
    content_id: Optional[str]
    desired_action_type: Optional[PolicyActionType]
    context: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ActionResponse:
    """Response from the bridge to Orchestrator"""
    request_id: str
    decision: ActionDecision
    selected_policy: Optional[Policy]
    approved_actions: List[PolicyActionType]
    blocked_reasons: List[str]
    recommendations: List[str]
    should_abstain: bool
    confidence_score: float
    guard_result: Optional[GuardResult]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'decision': self.decision.value,
            'selected_policy_id': self.selected_policy.policy_id if self.selected_policy else None,
            'approved_actions': [a.value for a in self.approved_actions],
            'blocked_reasons': self.blocked_reasons,
            'recommendations': self.recommendations,
            'should_abstain': self.should_abstain,
            'confidence_score': self.confidence_score,
            'guard_approved': self.guard_result.approved if self.guard_result else None,
            'timestamp': self.timestamp.isoformat()
        }


class OrchestratorPolicyBridge:
    """
    Main bridge between Orchestrator and Policy Engine.
    
    Workflow:
    1. Orchestrator requests action via request_action()
    2. Bridge evaluates applicable policies
    3. Bridge validates execution via guard
    4. Bridge returns decision
    5. Orchestrator executes (if approved)
    6. Orchestrator reports outcome via log_outcome()
    7. Learning system adapts
    
    This ensures:
    - No raw actions (only policy-driven)
    - All checks enforced
    - Learning from results
    - Intelligent abstention
    """
    
    def __init__(
        self,
        registry: Optional[PolicyRegistry] = None,
        evaluator: Optional[PolicyEvaluator] = None,
        guard: Optional[PolicyExecutionGuard] = None,
        learning: Optional[PolicyLearningFeedback] = None
    ):
        """
        Initialize orchestrator bridge.
        
        Args:
            registry: PolicyRegistry instance
            evaluator: PolicyEvaluator instance
            guard: PolicyExecutionGuard instance
            learning: PolicyLearningFeedback instance
        """
        self.registry = registry or PolicyRegistry()
        self.evaluator = evaluator or PolicyEvaluator(self.registry)
        self.guard = guard or PolicyExecutionGuard()
        self.learning = learning or PolicyLearningFeedback()
        
        # Request tracking
        self._request_history: List[ActionResponse] = []
    
    def request_action(
        self,
        account_id: str,
        platform: str,
        context: Dict[str, Any],
        content_id: Optional[str] = None,
        desired_action_type: Optional[PolicyActionType] = None,
        scope: Optional[PolicyScope] = None
    ) -> ActionResponse:
        """
        Request an action from the Orchestrator.
        
        This is the main entry point. The Orchestrator calls this instead of
        directly executing actions.
        
        Args:
            account_id: Account requesting action
            platform: Platform (youtube, tiktok, etc.)
            context: Full context including:
                - account_state: Current account state (Sprint 12)
                - current_risk_score: Risk score (Sprint 14)
                - current_aggressiveness: Aggressiveness score (Sprint 14)
                - metrics: Current metrics
                - signals: Recent signals (Sprint 11)
            content_id: Content ID (if applicable)
            desired_action_type: Specific action type requested (optional)
            scope: Policy scope filter (optional)
        
        Returns:
            ActionResponse with decision and details
        """
        request = ActionRequest(
            request_id=f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            account_id=account_id,
            platform=platform,
            content_id=content_id,
            desired_action_type=desired_action_type,
            context=context
        )
        
        # Add platform and account to context
        context['account_id'] = account_id
        context['platform'] = platform
        if content_id:
            context['content_id'] = content_id
        
        # 1. Check if should abstain (intelligent abstention)
        if self.evaluator.should_abstain(context):
            return ActionResponse(
                request_id=request.request_id,
                decision=ActionDecision.ABSTAINED,
                selected_policy=None,
                approved_actions=[],
                blocked_reasons=["Intelligent abstention - conditions not favorable"],
                recommendations=["Wait for better conditions", "Monitor metrics"],
                should_abstain=True,
                confidence_score=0.0,
                guard_result=None,
                timestamp=datetime.now()
            )
        
        # 2. Evaluate policies
        policy_results = self.evaluator.evaluate_context(context, scope=scope)
        
        if not policy_results:
            return ActionResponse(
                request_id=request.request_id,
                decision=ActionDecision.ABSTAINED,
                selected_policy=None,
                approved_actions=[],
                blocked_reasons=["No applicable policies found"],
                recommendations=["Review policy conditions", "Check account state"],
                should_abstain=True,
                confidence_score=0.0,
                guard_result=None,
                timestamp=datetime.now()
            )
        
        # 3. Select best policy (with learning adjustment)
        best_result = self._select_best_policy(policy_results)
        policy = best_result.policy
        
        # 4. Filter actions if specific type requested
        available_actions = policy.actions
        if desired_action_type:
            available_actions = [a for a in policy.actions if a.action_type == desired_action_type]
            
            if not available_actions:
                return ActionResponse(
                    request_id=request.request_id,
                    decision=ActionDecision.REJECTED,
                    selected_policy=policy,
                    approved_actions=[],
                    blocked_reasons=[f"Requested action {desired_action_type.value} not available in policy"],
                    recommendations=["Try different action type", "Review policy actions"],
                    should_abstain=False,
                    confidence_score=best_result.applicability_score,
                    guard_result=None,
                    timestamp=datetime.now()
                )
        
        # 5. Validate each available action through guard
        approved_actions = []
        blocked_reasons = []
        guard_results = []
        
        for action in available_actions:
            guard_result = self.guard.validate_execution(policy, action, context)
            guard_results.append(guard_result)
            
            if guard_result.approved:
                approved_actions.append(action.action_type)
            else:
                blocked_reasons.extend([r.value for r in guard_result.block_reasons])
        
        # 6. Make final decision
        if not approved_actions:
            decision = ActionDecision.BLOCKED
            recommendations = list(set(
                rec for gr in guard_results 
                for rec in gr.recommendations
            ))
        else:
            decision = ActionDecision.APPROVED
            recommendations = [best_result.recommendation]
        
        # 7. Check if requires review
        if policy.requires_supervisor_approval:
            decision = ActionDecision.REQUIRES_REVIEW
            recommendations.append("Requires Supervisor (Sprint 10) approval")
        
        # 8. Create response
        response = ActionResponse(
            request_id=request.request_id,
            decision=decision,
            selected_policy=policy,
            approved_actions=approved_actions,
            blocked_reasons=list(set(blocked_reasons)),
            recommendations=recommendations,
            should_abstain=False,
            confidence_score=best_result.applicability_score,
            guard_result=guard_results[0] if guard_results else None,
            timestamp=datetime.now()
        )
        
        # 9. Record request
        self._request_history.append(response)
        
        return response
    
    def _select_best_policy(
        self,
        policy_results: List[PolicyEvaluationResult]
    ) -> PolicyEvaluationResult:
        """
        Select best policy considering learning adjustments.
        
        Args:
            policy_results: List of applicable policies with scores
        
        Returns:
            Best PolicyEvaluationResult
        """
        # Apply learning adjustments
        adjusted_results = []
        
        for result in policy_results:
            # Get learning adjustment
            adjusted_confidence = self.learning.get_adjusted_confidence(result.policy)
            
            # Calculate adjusted score
            adjusted_score = result.applicability_score * (adjusted_confidence / result.policy.confidence_weight)
            
            # Check if policy is toxic
            if self.learning.is_policy_toxic(result.policy.policy_id):
                adjusted_score *= 0.1  # Heavy penalty for toxic policies
            
            adjusted_results.append((result, adjusted_score))
        
        # Sort by adjusted score
        adjusted_results.sort(key=lambda x: x[1], reverse=True)
        
        return adjusted_results[0][0]
    
    def log_outcome(
        self,
        request_id: str,
        policy_id: str,
        action_type: PolicyActionType,
        success: bool,
        metrics: Dict[str, float],
        success_signals_met: List[SuccessSignal] = None,
        context: Dict[str, Any] = None
    ):
        """
        Log the outcome of an executed action.
        
        This feeds the learning system to adapt future policy selection.
        
        Args:
            request_id: Original request ID
            policy_id: Policy that was executed
            action_type: Action that was executed
            success: Whether execution succeeded
            metrics: Performance metrics (velocity_lift, risk_delta, etc.)
            success_signals_met: Which success signals were achieved
            context: Execution context
        """
        # Record execution in guard
        policy = self.registry.get_policy(policy_id)
        if policy:
            action = next((a for a in policy.actions if a.action_type == action_type), None)
            if action:
                self.guard.record_execution(policy, action, context or {}, success)
        
        # Log to learning system
        self.learning.log_outcome(
            policy_id=policy_id,
            success=success,
            success_signals_met=success_signals_met or [],
            metrics=metrics,
            context=context or {}
        )
    
    def abort_execution(
        self,
        request_id: str,
        policy_id: str,
        reason: str
    ):
        """
        Abort an ongoing execution.
        
        Args:
            request_id: Original request ID
            policy_id: Policy being aborted
            reason: Reason for abort
        """
        # Log as failed execution
        self.log_outcome(
            request_id=request_id,
            policy_id=policy_id,
            action_type=PolicyActionType.ABSTAIN,  # Placeholder
            success=False,
            metrics={'velocity_lift': 0, 'risk_delta': 0},
            success_signals_met=[],
            context={'abort_reason': reason}
        )
    
    def evaluate_policies(
        self,
        context: Dict[str, Any],
        scope: Optional[PolicyScope] = None,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Evaluate and return top N applicable policies without executing.
        
        Useful for:
        - Policy debugging
        - Dashboard visualization
        - Manual review
        
        Args:
            context: Evaluation context
            scope: Filter by scope
            top_n: Number of policies to return
        
        Returns:
            List of policy evaluation dictionaries
        """
        policy_results = self.evaluator.get_top_n_policies(context, n=top_n, scope=scope)
        
        return [
            {
                'policy_id': r.policy.policy_id,
                'policy_name': r.policy.name,
                'applicability_score': r.applicability_score,
                'is_applicable': r.is_applicable,
                'recommendation': r.recommendation,
                'actions_available': [a.action_type.value for a in r.policy.actions],
                'max_allowed_risk': r.policy.max_allowed_risk_score,
                'max_allowed_aggressiveness': r.policy.max_allowed_aggressiveness,
                'learning_adjustment': self.learning.get_adjusted_confidence(r.policy) / r.policy.confidence_weight
            }
            for r in policy_results
        ]
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with:
            - Registry statistics
            - Evaluation statistics
            - Learning statistics
            - Recent requests
            - Toxic policies
        """
        return {
            'registry': self.registry.get_statistics(),
            'evaluator': self.evaluator.get_evaluation_statistics(),
            'learning': self.learning.get_overall_statistics(),
            'recent_requests': len(self._request_history),
            'toxic_policies': self.learning.get_toxic_policies(),
            'top_performing_policies': [
                p.to_dict() for p in self.learning.get_top_performing_policies(n=3)
            ]
        }
    
    def get_policy_performance(
        self,
        policy_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed performance for a specific policy.
        
        Args:
            policy_id: Policy to get performance for
        
        Returns:
            Performance dictionary or None
        """
        insights = self.learning.get_policy_insights(policy_id)
        exec_stats = self.guard.get_execution_stats(policy_id)
        
        return {
            'policy_id': policy_id,
            'learning_insights': insights,
            'execution_stats': exec_stats
        }
    
    def get_recent_decisions(
        self,
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent action decisions.
        
        Args:
            n: Number of decisions to return
        
        Returns:
            List of recent ActionResponse dictionaries
        """
        recent = self._request_history[-n:] if len(self._request_history) >= n else self._request_history
        return [r.to_dict() for r in reversed(recent)]


if __name__ == "__main__":
    # Example usage
    from decision_policy_models import create_example_policy
    
    # Create bridge
    bridge = OrchestratorPolicyBridge()
    
    # Register example policy
    policy = create_example_policy()
    bridge.registry.register_policy(policy)
    
    # Request action
    context = {
        'account_state': 'near_breakout',
        'comments_to_breakout': 3,
        'retention_ratio': 1.15,
        'identity_risk': 0.3,
        'aggressiveness_score': 0.6,
        'current_risk_score': 0.2,
        'current_aggressiveness': 0.5
    }
    
    response = bridge.request_action(
        account_id="acc_001",
        platform="youtube",
        context=context,
        content_id="vid_123"
    )
    
    print(f"✓ Action request processed")
    print(f"  Decision: {response.decision.value}")
    print(f"  Policy: {response.selected_policy.name if response.selected_policy else 'None'}")
    print(f"  Approved actions: {[a.value for a in response.approved_actions]}")
    print(f"  Confidence: {response.confidence_score:.2f}")
    
    if response.blocked_reasons:
        print(f"  Blocked reasons: {response.blocked_reasons}")
    
    if response.recommendations:
        print(f"  Recommendations:")
        for rec in response.recommendations:
            print(f"    - {rec}")
    
    # Get system status
    status = bridge.get_system_status()
    print(f"\n✓ System status:")
    print(f"  Total policies: {status['registry']['total_policies']}")
    print(f"  Active policies: {status['registry']['active_count']}")
    print(f"  Recent requests: {status['recent_requests']}")
