"""
Sprint 15: Decision Policy Engine - Execution Guard

Pre-execution validation that blocks actions if any safety check fails.

Integrates with Sprint 14 (Cognitive Governance) for risk and aggressiveness monitoring.

Author: STAKAZO Project  
Date: 2025-12-12
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict
from enum import Enum

from .decision_policy_models import (
    Policy,
    PolicyAction,
    PolicyActionType,
    AbortCondition,
    AccountState
)


class BlockReason(Enum):
    """Reasons for blocking execution"""
    COOLDOWN_ACTIVE = "cooldown_active"
    ACTION_LIMIT_REACHED = "action_limit_reached"
    GLOBAL_LIMIT_REACHED = "global_limit_reached"
    HIGH_AGGRESSIVENESS = "high_aggressiveness"
    HIGH_RISK = "high_risk"
    PATTERN_REPETITION = "pattern_repetition"
    INVALID_ACCOUNT_STATE = "invalid_account_state"
    SUPERVISOR_BLOCKED = "supervisor_blocked"
    EMERGENCY_FLAG = "emergency_flag"
    ABORT_CONDITION_MET = "abort_condition_met"
    POLICY_EXPIRED = "policy_expired"
    POLICY_INACTIVE = "policy_inactive"


@dataclass
class ExecutionCheck:
    """Result of a single execution check"""
    check_name: str
    passed: bool
    details: Dict[str, Any]
    block_reason: Optional[BlockReason] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'check_name': self.check_name,
            'passed': self.passed,
            'details': self.details,
            'block_reason': self.block_reason.value if self.block_reason else None
        }


@dataclass
class GuardResult:
    """Result of execution guard validation"""
    approved: bool
    policy_id: str
    action_type: str
    checks: List[ExecutionCheck]
    block_reasons: List[BlockReason]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'approved': self.approved,
            'policy_id': self.policy_id,
            'action_type': self.action_type,
            'checks': [c.to_dict() for c in self.checks],
            'block_reasons': [r.value for r in self.block_reasons],
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


class PolicyExecutionGuard:
    """
    Guardian that validates execution prerequisites before allowing actions.
    
    The guard checks:
    1. Cooldown periods
    2. Action limits (per action, per policy)
    3. Global aggressiveness (Sprint 14)
    4. Risk scores (Sprint 14)
    5. Pattern repetition
    6. Account state validity
    7. Supervisor flags
    8. Abort conditions
    
    If ANY check fails -> BLOCK execution
    """
    
    def __init__(
        self,
        storage_path: str = "storage/execution_guard"
    ):
        """
        Initialize execution guard.
        
        Args:
            storage_path: Path for storing execution history
        """
        self.storage_path = storage_path
        
        # Execution tracking
        self._execution_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._last_execution: Dict[str, datetime] = {}
        self._action_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Pattern detection
        self._action_timestamps: List[datetime] = []
        self._action_types_sequence: List[str] = []
    
    def validate_execution(
        self,
        policy: Policy,
        action: PolicyAction,
        context: Dict[str, Any]
    ) -> GuardResult:
        """
        Validate if action execution should be allowed.
        
        Args:
            policy: Policy authorizing the action
            action: Action to execute
            context: Execution context with:
                - account_id: Account executing action
                - current_risk_score: Risk score (Sprint 14)
                - current_aggressiveness: Aggressiveness score (Sprint 14)
                - account_state: Current account state
                - supervisor_flags: Flags from Supervisor (Sprint 10)
        
        Returns:
            GuardResult with approval status and details
        """
        checks: List[ExecutionCheck] = []
        block_reasons: List[BlockReason] = []
        recommendations: List[str] = []
        
        # 1. Policy status check
        check = self._check_policy_status(policy)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
        
        # 2. Cooldown check
        check = self._check_cooldown(policy, action, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append(check.details.get('recommendation', ''))
        
        # 3. Action limit check
        check = self._check_action_limits(policy, action, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
        
        # 4. Global limit check
        check = self._check_global_limits(policy, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
        
        # 5. Aggressiveness check (Sprint 14)
        check = self._check_aggressiveness(policy, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append("Reduce system aggressiveness before proceeding")
        
        # 6. Risk check (Sprint 14)
        check = self._check_risk(policy, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append("Risk too high - wait for conditions to improve")
        
        # 7. Pattern repetition check
        check = self._check_pattern_repetition(action, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append("Vary actions to avoid detectable patterns")
        
        # 8. Account state check
        check = self._check_account_state(policy, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
        
        # 9. Supervisor flags check
        check = self._check_supervisor_flags(context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append("Supervisor has blocked this action")
        
        # 10. Abort conditions check
        check = self._check_abort_conditions(policy, context)
        checks.append(check)
        if not check.passed:
            block_reasons.append(check.block_reason)
            recommendations.append("Abort condition met - policy terminated")
        
        # Final approval
        approved = len(block_reasons) == 0
        
        return GuardResult(
            approved=approved,
            policy_id=policy.policy_id,
            action_type=action.action_type.value,
            checks=checks,
            block_reasons=block_reasons,
            recommendations=[r for r in recommendations if r],
            timestamp=datetime.now()
        )
    
    def _check_policy_status(self, policy: Policy) -> ExecutionCheck:
        """Check if policy is active and not expired"""
        from .decision_policy_models import PolicyStatus
        
        if policy.status not in [PolicyStatus.ACTIVE, PolicyStatus.TESTING]:
            return ExecutionCheck(
                check_name="Policy Status",
                passed=False,
                details={'status': policy.status.value},
                block_reason=BlockReason.POLICY_INACTIVE
            )
        
        if policy.expiry_date and datetime.now() > policy.expiry_date:
            return ExecutionCheck(
                check_name="Policy Status",
                passed=False,
                details={'expiry_date': policy.expiry_date.isoformat()},
                block_reason=BlockReason.POLICY_EXPIRED
            )
        
        return ExecutionCheck(
            check_name="Policy Status",
            passed=True,
            details={'status': policy.status.value}
        )
    
    def _check_cooldown(
        self,
        policy: Policy,
        action: PolicyAction,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check if cooldown period has elapsed"""
        account_id = context.get('account_id', 'unknown')
        action_key = f"{policy.policy_id}:{action.action_type.value}:{account_id}"
        
        last_execution = self._last_execution.get(action_key)
        
        if last_execution:
            # Use minimum cooldown from range
            min_cooldown = min(action.cooldown_minutes)
            elapsed = (datetime.now() - last_execution).total_seconds() / 60
            
            if elapsed < min_cooldown:
                remaining = min_cooldown - elapsed
                return ExecutionCheck(
                    check_name="Cooldown",
                    passed=False,
                    details={
                        'last_execution': last_execution.isoformat(),
                        'elapsed_minutes': elapsed,
                        'required_minutes': min_cooldown,
                        'remaining_minutes': remaining,
                        'recommendation': f"Wait {int(remaining)} more minutes"
                    },
                    block_reason=BlockReason.COOLDOWN_ACTIVE
                )
        
        return ExecutionCheck(
            check_name="Cooldown",
            passed=True,
            details={'status': 'No active cooldown'}
        )
    
    def _check_action_limits(
        self,
        policy: Policy,
        action: PolicyAction,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check if action execution limit reached"""
        account_id = context.get('account_id', 'unknown')
        count_key = f"{policy.policy_id}:{action.action_type.value}:{account_id}"
        
        current_count = self._action_counts[policy.policy_id][count_key]
        
        if current_count >= action.max_executions:
            return ExecutionCheck(
                check_name="Action Limits",
                passed=False,
                details={
                    'current_count': current_count,
                    'max_allowed': action.max_executions,
                    'action_type': action.action_type.value
                },
                block_reason=BlockReason.ACTION_LIMIT_REACHED
            )
        
        return ExecutionCheck(
            check_name="Action Limits",
            passed=True,
            details={
                'current_count': current_count,
                'max_allowed': action.max_executions
            }
        )
    
    def _check_global_limits(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check if global action limit reached"""
        account_id = context.get('account_id', 'unknown')
        
        # Count total actions for this policy + account
        total_count = sum(
            count for key, count in self._action_counts[policy.policy_id].items()
            if account_id in key
        )
        
        if total_count >= policy.max_total_actions:
            return ExecutionCheck(
                check_name="Global Limits",
                passed=False,
                details={
                    'total_count': total_count,
                    'max_allowed': policy.max_total_actions
                },
                block_reason=BlockReason.GLOBAL_LIMIT_REACHED
            )
        
        return ExecutionCheck(
            check_name="Global Limits",
            passed=True,
            details={
                'total_count': total_count,
                'max_allowed': policy.max_total_actions
            }
        )
    
    def _check_aggressiveness(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check aggressiveness score (Sprint 14 integration)"""
        current_agg = context.get('current_aggressiveness', 0)
        max_allowed = policy.max_allowed_aggressiveness
        
        if current_agg > max_allowed:
            return ExecutionCheck(
                check_name="Aggressiveness",
                passed=False,
                details={
                    'current': current_agg,
                    'max_allowed': max_allowed,
                    'excess': current_agg - max_allowed
                },
                block_reason=BlockReason.HIGH_AGGRESSIVENESS
            )
        
        return ExecutionCheck(
            check_name="Aggressiveness",
            passed=True,
            details={
                'current': current_agg,
                'max_allowed': max_allowed,
                'status': 'safe' if current_agg < 0.7 else 'warning'
            }
        )
    
    def _check_risk(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check risk score (Sprint 14 integration)"""
        current_risk = context.get('current_risk_score', 0)
        max_allowed = policy.max_allowed_risk_score
        
        if current_risk > max_allowed:
            return ExecutionCheck(
                check_name="Risk Score",
                passed=False,
                details={
                    'current': current_risk,
                    'max_allowed': max_allowed,
                    'risk_level': 'high' if current_risk > 0.75 else 'medium'
                },
                block_reason=BlockReason.HIGH_RISK
            )
        
        return ExecutionCheck(
            check_name="Risk Score",
            passed=True,
            details={
                'current': current_risk,
                'max_allowed': max_allowed,
                'risk_level': 'low' if current_risk < 0.3 else 'acceptable'
            }
        )
    
    def _check_pattern_repetition(
        self,
        action: PolicyAction,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Detect repetitive patterns that could be flagged"""
        action_type = action.action_type.value
        
        # Check recent action sequence
        recent_actions = self._action_types_sequence[-10:]
        
        if len(recent_actions) >= 3:
            # Check for exact repetition
            if recent_actions[-3:] == [action_type] * 3:
                return ExecutionCheck(
                    check_name="Pattern Repetition",
                    passed=False,
                    details={
                        'pattern': f"Same action ({action_type}) 3 times in a row",
                        'recent_sequence': recent_actions
                    },
                    block_reason=BlockReason.PATTERN_REPETITION
                )
        
        # Check timing patterns
        if len(self._action_timestamps) >= 5:
            recent_times = self._action_timestamps[-5:]
            intervals = [
                (recent_times[i+1] - recent_times[i]).total_seconds()
                for i in range(len(recent_times)-1)
            ]
            
            # Check for mechanical timing (all intervals within 5 seconds of each other)
            if len(set(int(i) for i in intervals)) <= 2:
                return ExecutionCheck(
                    check_name="Pattern Repetition",
                    passed=False,
                    details={
                        'pattern': 'Mechanical timing detected',
                        'intervals': intervals
                    },
                    block_reason=BlockReason.PATTERN_REPETITION
                )
        
        return ExecutionCheck(
            check_name="Pattern Repetition",
            passed=True,
            details={'status': 'No repetitive patterns detected'}
        )
    
    def _check_account_state(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check if account state allows execution"""
        account_state = context.get('account_state')
        
        if not account_state:
            return ExecutionCheck(
                check_name="Account State",
                passed=True,
                details={'status': 'No state constraint'}
            )
        
        if isinstance(account_state, str):
            try:
                account_state = AccountState(account_state)
            except ValueError:
                return ExecutionCheck(
                    check_name="Account State",
                    passed=False,
                    details={'error': 'Invalid account state'},
                    block_reason=BlockReason.INVALID_ACCOUNT_STATE
                )
        
        if account_state not in policy.applicable_states:
            return ExecutionCheck(
                check_name="Account State",
                passed=False,
                details={
                    'current_state': account_state.value,
                    'allowed_states': [s.value for s in policy.applicable_states]
                },
                block_reason=BlockReason.INVALID_ACCOUNT_STATE
            )
        
        return ExecutionCheck(
            check_name="Account State",
            passed=True,
            details={'current_state': account_state.value}
        )
    
    def _check_supervisor_flags(
        self,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check for supervisor blocking flags (Sprint 10 integration)"""
        supervisor_flags = context.get('supervisor_flags', {})
        
        if supervisor_flags.get('block_all_actions', False):
            return ExecutionCheck(
                check_name="Supervisor Flags",
                passed=False,
                details={'reason': 'Supervisor has blocked all actions'},
                block_reason=BlockReason.SUPERVISOR_BLOCKED
            )
        
        if context.get('emergency_flag', False):
            return ExecutionCheck(
                check_name="Supervisor Flags",
                passed=False,
                details={'reason': 'Emergency flag active'},
                block_reason=BlockReason.EMERGENCY_FLAG
            )
        
        return ExecutionCheck(
            check_name="Supervisor Flags",
            passed=True,
            details={'status': 'No blocking flags'}
        )
    
    def _check_abort_conditions(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> ExecutionCheck:
        """Check if any abort conditions are met"""
        for abort_condition in policy.abort_conditions:
            if self._is_abort_condition_met(abort_condition, context):
                return ExecutionCheck(
                    check_name="Abort Conditions",
                    passed=False,
                    details={
                        'condition': abort_condition.value,
                        'policy_id': policy.policy_id
                    },
                    block_reason=BlockReason.ABORT_CONDITION_MET
                )
        
        return ExecutionCheck(
            check_name="Abort Conditions",
            passed=True,
            details={'status': 'No abort conditions met'}
        )
    
    def _is_abort_condition_met(
        self,
        condition: AbortCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Check if specific abort condition is met"""
        if condition == AbortCondition.RISK_SPIKE:
            return context.get('current_risk_score', 0) > 0.75
        
        elif condition == AbortCondition.AGGRESSIVENESS_DANGER:
            return context.get('current_aggressiveness', 0) > 0.85
        
        elif condition == AbortCondition.SHADOWBAN_DETECTED:
            return context.get('shadowban_detected', False)
        
        elif condition == AbortCondition.ENGAGEMENT_DROP:
            return context.get('engagement_drop_detected', False)
        
        elif condition == AbortCondition.REACH_COLLAPSE:
            return context.get('reach_collapse_detected', False)
        
        elif condition == AbortCondition.ACCOUNT_FLAG_DETECTED:
            return context.get('account_flagged', False)
        
        elif condition == AbortCondition.SUPERVISOR_OVERRIDE:
            return context.get('supervisor_flags', {}).get('override', False)
        
        elif condition == AbortCondition.MANUAL_ABORT:
            return context.get('manual_abort', False)
        
        return False
    
    def record_execution(
        self,
        policy: Policy,
        action: PolicyAction,
        context: Dict[str, Any],
        success: bool
    ):
        """Record successful execution for tracking"""
        account_id = context.get('account_id', 'unknown')
        action_key = f"{policy.policy_id}:{action.action_type.value}:{account_id}"
        count_key = action_key
        
        # Update last execution time
        self._last_execution[action_key] = datetime.now()
        
        # Update action counts
        self._action_counts[policy.policy_id][count_key] += 1
        
        # Record for pattern detection
        self._action_timestamps.append(datetime.now())
        self._action_types_sequence.append(action.action_type.value)
        
        # Keep only recent history
        if len(self._action_timestamps) > 100:
            self._action_timestamps = self._action_timestamps[-100:]
        if len(self._action_types_sequence) > 100:
            self._action_types_sequence = self._action_types_sequence[-100:]
        
        # Record in execution history
        self._execution_history[policy.policy_id].append({
            'timestamp': datetime.now().isoformat(),
            'action_type': action.action_type.value,
            'account_id': account_id,
            'success': success
        })
    
    def reset_policy_counters(self, policy_id: str):
        """Reset execution counters for a policy"""
        if policy_id in self._action_counts:
            del self._action_counts[policy_id]
    
    def get_execution_stats(self, policy_id: str) -> Dict[str, Any]:
        """Get execution statistics for a policy"""
        history = self._execution_history.get(policy_id, [])
        
        if not history:
            return {
                'total_executions': 0,
                'success_count': 0,
                'failure_count': 0,
                'success_rate': 0
            }
        
        total = len(history)
        success_count = sum(1 for h in history if h['success'])
        
        return {
            'total_executions': total,
            'success_count': success_count,
            'failure_count': total - success_count,
            'success_rate': success_count / total if total > 0 else 0,
            'last_execution': history[-1]['timestamp'] if history else None
        }


if __name__ == "__main__":
    # Example usage
    from decision_policy_models import create_example_policy
    
    guard = PolicyExecutionGuard()
    policy = create_example_policy()
    action = policy.actions[0]
    
    context = {
        'account_id': 'acc_001',
        'current_risk_score': 0.3,
        'current_aggressiveness': 0.5,
        'account_state': 'near_breakout'
    }
    
    result = guard.validate_execution(policy, action, context)
    
    print(f"✓ Execution validated")
    print(f"  Approved: {result.approved}")
    print(f"  Checks: {len(result.checks)} performed")
    
    if not result.approved:
        print(f"  Blocked: {[r.value for r in result.block_reasons]}")
        print(f"  Recommendations: {result.recommendations}")
