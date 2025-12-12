"""
Sprint 15: Decision Policy Engine - Policy Evaluator

Contextual policy evaluator that determines which policies are applicable
in a given context and ranks them by applicability score.

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime

from .decision_policy_models import (
    Policy,
    PolicyScope,
    AccountState,
    PolicyStatus
)
from .policy_registry import PolicyRegistry


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation for a given context"""
    policy: Policy
    applicability_score: float  # 0.0-1.0
    is_applicable: bool
    context_match_details: Dict[str, Any]
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy.policy_id,
            'policy_name': self.policy.name,
            'applicability_score': self.applicability_score,
            'is_applicable': self.is_applicable,
            'context_match_details': self.context_match_details,
            'recommendation': self.recommendation
        }


class PolicyEvaluator:
    """
    Evaluates context and determines applicable policies.
    
    The evaluator:
    1. Loads active policies from registry
    2. Evaluates each policy against context
    3. Scores applicability
    4. Ranks policies by score
    5. Returns ordered list or empty (intelligent abstention)
    """
    
    def __init__(self, registry: Optional[PolicyRegistry] = None):
        """
        Initialize policy evaluator.
        
        Args:
            registry: PolicyRegistry instance (creates new if None)
        """
        self.registry = registry or PolicyRegistry()
        
        # Evaluation history for analysis
        self._evaluation_history: List[Dict[str, Any]] = []
    
    def evaluate_context(
        self,
        context: Dict[str, Any],
        scope: Optional[PolicyScope] = None,
        min_score_threshold: float = 0.3
    ) -> List[PolicyEvaluationResult]:
        """
        Evaluate context and return applicable policies ranked by score.
        
        Args:
            context: Context dictionary with:
                - account_state: Current account state
                - platform: Platform name
                - content_id: Content identifier
                - metrics: Current metrics
                - signals: Recent signals (Sprint 11)
                - risk_data: Risk scores (Sprint 14)
                - aggressiveness_data: Aggressiveness scores (Sprint 14)
            scope: Filter by policy scope (optional)
            min_score_threshold: Minimum score to include policy
        
        Returns:
            List of PolicyEvaluationResult sorted by score (descending)
            Empty list if no policies are applicable (intelligent abstention)
        """
        # Extract key context elements
        account_state = context.get('account_state')
        if isinstance(account_state, str):
            try:
                account_state = AccountState(account_state)
            except ValueError:
                account_state = None
        
        # Get active policies
        active_policies = self.registry.get_active_policies(
            scope=scope,
            account_state=account_state
        )
        
        # Evaluate each policy
        results = []
        for policy in active_policies:
            evaluation = self._evaluate_single_policy(policy, context)
            
            # Apply minimum score threshold
            if evaluation.applicability_score >= min_score_threshold:
                results.append(evaluation)
        
        # Sort by score (descending)
        results.sort(key=lambda r: r.applicability_score, reverse=True)
        
        # Record evaluation
        self._record_evaluation(context, results)
        
        return results
    
    def _evaluate_single_policy(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> PolicyEvaluationResult:
        """
        Evaluate a single policy against context.
        
        Args:
            policy: Policy to evaluate
            context: Evaluation context
        
        Returns:
            PolicyEvaluationResult with score and details
        """
        # Check basic applicability
        is_applicable = policy.is_applicable(context)
        
        # Calculate detailed applicability score
        score = policy.calculate_applicability_score(context)
        
        # Collect context match details
        match_details = self._analyze_context_match(policy, context)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(policy, context, score, match_details)
        
        return PolicyEvaluationResult(
            policy=policy,
            applicability_score=score,
            is_applicable=is_applicable,
            context_match_details=match_details,
            recommendation=recommendation
        )
    
    def _analyze_context_match(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze how well context matches policy requirements.
        
        Args:
            policy: Policy to analyze
            context: Evaluation context
        
        Returns:
            Dictionary with match analysis
        """
        details = {
            'conditions_met': [],
            'conditions_failed': [],
            'risk_check': None,
            'aggressiveness_check': None,
            'state_match': None
        }
        
        # Check conditions
        for condition in policy.conditions:
            if condition.evaluate(context):
                details['conditions_met'].append({
                    'field': condition.field,
                    'operator': condition.operator,
                    'value': condition.value,
                    'weight': condition.weight
                })
            else:
                details['conditions_failed'].append({
                    'field': condition.field,
                    'operator': condition.operator,
                    'value': condition.value,
                    'context_value': context.get(condition.field, 'N/A')
                })
        
        # Risk check
        current_risk = context.get('current_risk_score', 0)
        details['risk_check'] = {
            'current': current_risk,
            'max_allowed': policy.max_allowed_risk_score,
            'passes': current_risk <= policy.max_allowed_risk_score
        }
        
        # Aggressiveness check
        current_agg = context.get('current_aggressiveness', 0)
        details['aggressiveness_check'] = {
            'current': current_agg,
            'max_allowed': policy.max_allowed_aggressiveness,
            'passes': current_agg <= policy.max_allowed_aggressiveness
        }
        
        # State match
        account_state = context.get('account_state')
        if isinstance(account_state, str):
            try:
                account_state = AccountState(account_state)
            except ValueError:
                account_state = None
        
        details['state_match'] = {
            'current_state': account_state.value if account_state else None,
            'applicable_states': [s.value for s in policy.applicable_states],
            'matches': account_state in policy.applicable_states if account_state else False
        }
        
        return details
    
    def _generate_recommendation(
        self,
        policy: Policy,
        context: Dict[str, Any],
        score: float,
        match_details: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable recommendation.
        
        Args:
            policy: Policy evaluated
            context: Evaluation context
            score: Applicability score
            match_details: Context match analysis
        
        Returns:
            Recommendation string
        """
        if score >= 0.8:
            return f"HIGHLY RECOMMENDED: {policy.name} is an excellent fit (score: {score:.2f})"
        
        elif score >= 0.6:
            recommendation = f"RECOMMENDED: {policy.name} is a good fit (score: {score:.2f})"
            
            # Add caveats if any
            if not match_details['risk_check']['passes']:
                recommendation += " - Monitor risk closely"
            
            if not match_details['aggressiveness_check']['passes']:
                recommendation += " - Reduce aggressiveness first"
            
            return recommendation
        
        elif score >= 0.3:
            recommendation = f"ACCEPTABLE: {policy.name} could work (score: {score:.2f})"
            
            failed_conditions = len(match_details['conditions_failed'])
            if failed_conditions > 0:
                recommendation += f" - {failed_conditions} conditions not ideal"
            
            return recommendation
        
        else:
            reason = "Score too low"
            
            if match_details['conditions_failed']:
                reason = f"{len(match_details['conditions_failed'])} critical conditions failed"
            
            elif not match_details['risk_check']['passes']:
                reason = "Risk too high"
            
            elif not match_details['aggressiveness_check']['passes']:
                reason = "Aggressiveness too high"
            
            return f"NOT RECOMMENDED: {policy.name} - {reason}"
    
    def _record_evaluation(
        self,
        context: Dict[str, Any],
        results: List[PolicyEvaluationResult]
    ):
        """Record evaluation for analysis"""
        self._evaluation_history.append({
            'timestamp': datetime.now().isoformat(),
            'context_summary': {
                'account_state': context.get('account_state'),
                'platform': context.get('platform'),
                'risk_score': context.get('current_risk_score', 0),
                'aggressiveness': context.get('current_aggressiveness', 0)
            },
            'policies_evaluated': len(results),
            'top_score': results[0].applicability_score if results else 0,
            'abstention': len(results) == 0
        })
        
        # Keep only last 1000 evaluations
        if len(self._evaluation_history) > 1000:
            self._evaluation_history = self._evaluation_history[-1000:]
    
    def should_abstain(self, context: Dict[str, Any]) -> bool:
        """
        Determine if system should abstain from action.
        
        Abstention is intelligent when:
        - No policies are applicable
        - All policies score below threshold
        - Risk is too high
        - Aggressiveness is in danger zone
        
        Args:
            context: Evaluation context
        
        Returns:
            True if should abstain, False otherwise
        """
        # Check for high risk
        if context.get('current_risk_score', 0) > 0.75:
            return True
        
        # Check for high aggressiveness
        if context.get('current_aggressiveness', 0) > 0.85:
            return True
        
        # Check for emergency flags
        if context.get('emergency_flag', False):
            return True
        
        if context.get('shadowban_detected', False):
            return True
        
        # Evaluate policies
        results = self.evaluate_context(context)
        
        # Abstain if no policies applicable or all scores too low
        if not results or results[0].applicability_score < 0.3:
            return True
        
        return False
    
    def get_best_policy(
        self,
        context: Dict[str, Any],
        scope: Optional[PolicyScope] = None
    ) -> Optional[PolicyEvaluationResult]:
        """
        Get the single best policy for context.
        
        Args:
            context: Evaluation context
            scope: Filter by scope
        
        Returns:
            Best PolicyEvaluationResult or None if should abstain
        """
        if self.should_abstain(context):
            return None
        
        results = self.evaluate_context(context, scope=scope)
        
        return results[0] if results else None
    
    def get_top_n_policies(
        self,
        context: Dict[str, Any],
        n: int = 3,
        scope: Optional[PolicyScope] = None
    ) -> List[PolicyEvaluationResult]:
        """
        Get top N policies for context.
        
        Args:
            context: Evaluation context
            n: Number of policies to return
            scope: Filter by scope
        
        Returns:
            List of top N PolicyEvaluationResult
        """
        results = self.evaluate_context(context, scope=scope)
        return results[:n]
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about evaluations.
        
        Returns:
            Dictionary with statistics
        """
        if not self._evaluation_history:
            return {
                'total_evaluations': 0,
                'abstention_rate': 0,
                'average_top_score': 0
            }
        
        total = len(self._evaluation_history)
        abstentions = sum(1 for e in self._evaluation_history if e['abstention'])
        
        scores = [e['top_score'] for e in self._evaluation_history if not e['abstention']]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_evaluations': total,
            'abstention_count': abstentions,
            'abstention_rate': abstentions / total if total > 0 else 0,
            'average_top_score': avg_score,
            'evaluations_with_policies': total - abstentions
        }


if __name__ == "__main__":
    # Example usage
    from decision_policy_models import create_example_policy
    
    # Create registry and evaluator
    registry = PolicyRegistry()
    policy = create_example_policy()
    registry.register_policy(policy)
    
    evaluator = PolicyEvaluator(registry)
    
    # Example context
    context = {
        'account_state': 'near_breakout',
        'platform': 'youtube',
        'comments_to_breakout': 3,
        'retention_ratio': 1.15,
        'identity_risk': 0.3,
        'aggressiveness_score': 0.6,
        'current_risk_score': 0.2,
        'current_aggressiveness': 0.5
    }
    
    # Evaluate
    results = evaluator.evaluate_context(context)
    
    print(f"✓ Evaluated {len(results)} policies")
    
    if results:
        best = results[0]
        print(f"  Best: {best.policy.name}")
        print(f"  Score: {best.applicability_score:.2f}")
        print(f"  Recommendation: {best.recommendation}")
    else:
        print("  Intelligent abstention - no policies applicable")
    
    # Check abstention
    should_abstain = evaluator.should_abstain(context)
    print(f"\n✓ Should abstain: {should_abstain}")
    
    # Get statistics
    stats = evaluator.get_evaluation_statistics()
    print(f"\n✓ Evaluation statistics:")
    print(f"  Total evaluations: {stats['total_evaluations']}")
    print(f"  Abstention rate: {stats['abstention_rate']:.2%}")
