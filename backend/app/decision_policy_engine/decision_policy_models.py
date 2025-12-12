"""
Sprint 15: Decision Policy Engine - Policy Models

Formal, versionable policy structure that replaces point decisions with strategic,
auditable, and adaptive policies.

Each policy defines:
- What is allowed
- How many times
- At what rhythm
- Under what risks
- With what success signals
- When to abort
- When to repeat
- When to abstain

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
import json


class PolicyScope(Enum):
    """Policy application scope"""
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_CHANNEL = "youtube_channel"
    TIKTOK_VIDEO = "tiktok_video"
    TIKTOK_ACCOUNT = "tiktok_account"
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_ACCOUNT = "instagram_account"
    TWITTER_TWEET = "twitter_tweet"
    TWITTER_ACCOUNT = "twitter_account"
    GLOBAL_STRATEGY = "global_strategy"
    ACCOUNT_WARMUP = "account_warmup"


class AccountState(Enum):
    """Account states (from Sprint 12)"""
    INITIAL_SETUP = "initial_setup"
    WARMING_UP = "warming_up"
    HUMAN_WARMUP = "human_warmup"
    ORGANIC_LIFT = "organic_lift"
    STABLE_ACTIVE = "stable_active"
    NEAR_BREAKOUT = "near_breakout"
    BREAKOUT_DETECTED = "breakout_detected"
    HIGH_PERFORMANCE = "high_performance"
    DECLINING = "declining"
    AT_RISK = "at_risk"
    EMERGENCY_COOLDOWN = "emergency_cooldown"


class PolicyActionType(Enum):
    """Types of actions a policy can authorize"""
    COMMENT_REPLY = "comment_reply"
    CONTEXTUAL_BOOST = "contextual_boost"
    ENGAGEMENT_BOOST = "engagement_boost"
    CONTENT_SHARE = "content_share"
    FOLLOW_SIMILAR_ACCOUNTS = "follow_similar_accounts"
    LIKE_RELATED_CONTENT = "like_related_content"
    WATCH_SIMILAR_CONTENT = "watch_similar_content"
    CREATE_VARIANT_CONTENT = "create_variant_content"
    SCHEDULE_CONTENT = "schedule_content"
    ADJUST_STRATEGY = "adjust_strategy"
    SCALE_ACCOUNTS = "scale_accounts"
    EMERGENCY_STOP = "emergency_stop"
    ABSTAIN = "abstain"


class SuccessSignal(Enum):
    """Signals that indicate policy success"""
    VELOCITY_INCREASE = "velocity_increase"
    RETENTION_IMPROVEMENT = "retention_improvement"
    BREAKOUT_ACHIEVED = "breakout_achieved"
    ENGAGEMENT_RATE_UP = "engagement_rate_up"
    REACH_EXPANSION = "reach_expansion"
    CONVERSION_INCREASE = "conversion_increase"
    RISK_REDUCTION = "risk_reduction"
    ORGANIC_GROWTH = "organic_growth"
    ACCOUNT_HEALTH_IMPROVED = "account_health_improved"


class AbortCondition(Enum):
    """Conditions that trigger policy abortion"""
    RISK_SPIKE = "risk_spike"
    PATTERN_SIMILARITY_HIGH = "pattern_similarity_high"
    IDENTITY_RISK_HIGH = "identity_risk_high"
    AGGRESSIVENESS_DANGER = "aggressiveness_danger"
    SHADOWBAN_DETECTED = "shadowban_detected"
    ENGAGEMENT_DROP = "engagement_drop"
    REACH_COLLAPSE = "reach_collapse"
    ACCOUNT_FLAG_DETECTED = "account_flag_detected"
    CORRELATION_RISK_HIGH = "correlation_risk_high"
    SUPERVISOR_OVERRIDE = "supervisor_override"
    MANUAL_ABORT = "manual_abort"


class PolicyStatus(Enum):
    """Policy lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"  # A/B testing
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    ARCHIVED = "archived"


@dataclass
class PolicyCondition:
    """A single condition that must be met for policy to be applicable"""
    field: str  # e.g., "comments_to_breakout", "retention_ratio", "identity_risk"
    operator: str  # "<=", ">=", "<", ">", "==", "!=", "in", "not_in"
    value: Any  # Comparison value
    weight: float = 1.0  # Weight in overall condition scoring
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        if self.field not in context:
            return False
        
        context_value = context[self.field]
        
        try:
            if self.operator == "<=":
                return float(context_value) <= float(self.value)
            elif self.operator == ">=":
                return float(context_value) >= float(self.value)
            elif self.operator == "<":
                return float(context_value) < float(self.value)
            elif self.operator == ">":
                return float(context_value) > float(self.value)
            elif self.operator == "==":
                return context_value == self.value
            elif self.operator == "!=":
                return context_value != self.value
            elif self.operator == "in":
                return context_value in self.value
            elif self.operator == "not_in":
                return context_value not in self.value
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
            'weight': self.weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyCondition':
        return cls(
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
            weight=data.get('weight', 1.0)
        )


@dataclass
class PolicyAction:
    """An action authorized by the policy"""
    action_type: PolicyActionType
    max_executions: int  # Max times this action can be executed under this policy
    cooldown_minutes: List[int]  # [min, max] cooldown range
    parameters: Dict[str, Any] = field(default_factory=dict)  # Action-specific params
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'max_executions': self.max_executions,
            'cooldown_minutes': self.cooldown_minutes,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyAction':
        return cls(
            action_type=PolicyActionType(data['action_type']),
            max_executions=data['max_executions'],
            cooldown_minutes=data['cooldown_minutes'],
            parameters=data.get('parameters', {})
        )


@dataclass
class PolicyMetadata:
    """Policy metadata for tracking and versioning"""
    created_at: datetime
    created_by: str
    version: str
    previous_version: Optional[str] = None
    change_notes: str = ""
    tags: List[str] = field(default_factory=list)
    a_b_test_group: Optional[str] = None  # e.g., "A", "B", None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'version': self.version,
            'previous_version': self.previous_version,
            'change_notes': self.change_notes,
            'tags': self.tags,
            'a_b_test_group': self.a_b_test_group
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyMetadata':
        return cls(
            created_at=datetime.fromisoformat(data['created_at']),
            created_by=data['created_by'],
            version=data['version'],
            previous_version=data.get('previous_version'),
            change_notes=data.get('change_notes', ''),
            tags=data.get('tags', []),
            a_b_test_group=data.get('a_b_test_group')
        )


@dataclass
class Policy:
    """
    A formal, versionable policy that defines strategic behavior.
    
    Policies replace point decisions with structured, auditable rules that define:
    - Applicability conditions
    - Authorized actions
    - Execution limits
    - Success criteria
    - Abort conditions
    """
    policy_id: str
    name: str
    description: str
    scope: PolicyScope
    applicable_states: List[AccountState]
    conditions: List[PolicyCondition]
    actions: List[PolicyAction]
    success_signals: List[SuccessSignal]
    abort_conditions: List[AbortCondition]
    confidence_weight: float  # 0.0-1.0, affects policy selection scoring
    status: PolicyStatus
    metadata: PolicyMetadata
    
    # Execution constraints
    max_total_actions: int = 10  # Max actions across all action types
    global_cooldown_minutes: int = 60  # Min time between any actions
    expiry_date: Optional[datetime] = None
    
    # Integration with Sprint 14 (Cognitive Governance)
    requires_risk_simulation: bool = True
    requires_supervisor_approval: bool = False
    max_allowed_risk_score: float = 0.5
    max_allowed_aggressiveness: float = 0.7
    
    def __post_init__(self):
        """Validate policy structure"""
        if not (0.0 <= self.confidence_weight <= 1.0):
            raise ValueError("confidence_weight must be between 0.0 and 1.0")
        
        if not (0.0 <= self.max_allowed_risk_score <= 1.0):
            raise ValueError("max_allowed_risk_score must be between 0.0 and 1.0")
        
        if not (0.0 <= self.max_allowed_aggressiveness <= 1.0):
            raise ValueError("max_allowed_aggressiveness must be between 0.0 and 1.0")
        
        if self.max_total_actions <= 0:
            raise ValueError("max_total_actions must be positive")
        
        if self.global_cooldown_minutes < 0:
            raise ValueError("global_cooldown_minutes must be non-negative")
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """
        Check if policy is applicable in the given context.
        
        Returns True only if:
        - Policy is ACTIVE or TESTING
        - Account state is in applicable_states
        - All conditions evaluate to True
        - Not expired
        """
        # Status check
        if self.status not in [PolicyStatus.ACTIVE, PolicyStatus.TESTING]:
            return False
        
        # Expiry check
        if self.expiry_date and datetime.now() > self.expiry_date:
            return False
        
        # Account state check
        account_state = context.get('account_state')
        if account_state:
            if isinstance(account_state, str):
                try:
                    account_state = AccountState(account_state)
                except ValueError:
                    return False
            
            if account_state not in self.applicable_states:
                return False
        
        # Condition checks
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True
    
    def calculate_applicability_score(self, context: Dict[str, Any]) -> float:
        """
        Calculate how well this policy fits the context (0.0-1.0).
        
        Higher score = better fit.
        """
        if not self.is_applicable(context):
            return 0.0
        
        # Base score from confidence weight
        score = self.confidence_weight
        
        # Bonus for matching conditions with high weights
        condition_score = 0.0
        total_weight = sum(c.weight for c in self.conditions)
        
        if total_weight > 0:
            for condition in self.conditions:
                if condition.evaluate(context):
                    condition_score += condition.weight / total_weight
            
            # Blend condition score with confidence weight (70/30)
            score = 0.7 * score + 0.3 * condition_score
        
        # Penalty for high risk requirements
        if context.get('current_risk_score', 0) > self.max_allowed_risk_score * 0.8:
            score *= 0.8
        
        # Penalty for high aggressiveness
        if context.get('current_aggressiveness', 0) > self.max_allowed_aggressiveness * 0.8:
            score *= 0.7
        
        return min(1.0, max(0.0, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to dictionary"""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'description': self.description,
            'scope': self.scope.value,
            'applicable_states': [s.value for s in self.applicable_states],
            'conditions': [c.to_dict() for c in self.conditions],
            'actions': [a.to_dict() for a in self.actions],
            'success_signals': [s.value for s in self.success_signals],
            'abort_conditions': [a.value for a in self.abort_conditions],
            'confidence_weight': self.confidence_weight,
            'status': self.status.value,
            'metadata': self.metadata.to_dict(),
            'max_total_actions': self.max_total_actions,
            'global_cooldown_minutes': self.global_cooldown_minutes,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'requires_risk_simulation': self.requires_risk_simulation,
            'requires_supervisor_approval': self.requires_supervisor_approval,
            'max_allowed_risk_score': self.max_allowed_risk_score,
            'max_allowed_aggressiveness': self.max_allowed_aggressiveness
        }
    
    def to_json(self) -> str:
        """Serialize policy to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Deserialize policy from dictionary"""
        return cls(
            policy_id=data['policy_id'],
            name=data['name'],
            description=data['description'],
            scope=PolicyScope(data['scope']),
            applicable_states=[AccountState(s) for s in data['applicable_states']],
            conditions=[PolicyCondition.from_dict(c) for c in data['conditions']],
            actions=[PolicyAction.from_dict(a) for a in data['actions']],
            success_signals=[SuccessSignal(s) for s in data['success_signals']],
            abort_conditions=[AbortCondition(a) for a in data['abort_conditions']],
            confidence_weight=data['confidence_weight'],
            status=PolicyStatus(data['status']),
            metadata=PolicyMetadata.from_dict(data['metadata']),
            max_total_actions=data.get('max_total_actions', 10),
            global_cooldown_minutes=data.get('global_cooldown_minutes', 60),
            expiry_date=datetime.fromisoformat(data['expiry_date']) if data.get('expiry_date') else None,
            requires_risk_simulation=data.get('requires_risk_simulation', True),
            requires_supervisor_approval=data.get('requires_supervisor_approval', False),
            max_allowed_risk_score=data.get('max_allowed_risk_score', 0.5),
            max_allowed_aggressiveness=data.get('max_allowed_aggressiveness', 0.7)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Policy':
        """Deserialize policy from JSON string"""
        return cls.from_dict(json.loads(json_str))


def create_example_policy() -> Policy:
    """
    Create an example policy for YouTube breakout support.
    
    This demonstrates the structure and can be used for testing.
    """
    return Policy(
        policy_id="YT_BREAKOUT_SUPPORT_v1.3",
        name="YouTube Breakout Support",
        description="Support videos that are near breakout threshold with strategic engagement",
        scope=PolicyScope.YOUTUBE_VIDEO,
        applicable_states=[
            AccountState.ORGANIC_LIFT,
            AccountState.NEAR_BREAKOUT
        ],
        conditions=[
            PolicyCondition(field="comments_to_breakout", operator="<=", value=5, weight=1.5),
            PolicyCondition(field="retention_ratio", operator=">", value=1.1, weight=1.2),
            PolicyCondition(field="identity_risk", operator="<", value=0.4, weight=1.0),
            PolicyCondition(field="aggressiveness_score", operator="<", value=0.7, weight=1.0)
        ],
        actions=[
            PolicyAction(
                action_type=PolicyActionType.COMMENT_REPLY,
                max_executions=2,
                cooldown_minutes=[45, 180],
                parameters={'authenticity': 'high', 'context_aware': True}
            ),
            PolicyAction(
                action_type=PolicyActionType.CONTEXTUAL_BOOST,
                max_executions=1,
                cooldown_minutes=[120, 240],
                parameters={'boost_type': 'organic_amplification'}
            )
        ],
        success_signals=[
            SuccessSignal.VELOCITY_INCREASE,
            SuccessSignal.BREAKOUT_ACHIEVED,
            SuccessSignal.ENGAGEMENT_RATE_UP
        ],
        abort_conditions=[
            AbortCondition.RISK_SPIKE,
            AbortCondition.PATTERN_SIMILARITY_HIGH,
            AbortCondition.IDENTITY_RISK_HIGH,
            AbortCondition.SHADOWBAN_DETECTED
        ],
        confidence_weight=0.82,
        status=PolicyStatus.ACTIVE,
        metadata=PolicyMetadata(
            created_at=datetime.now(),
            created_by="PolicyDesigner",
            version="1.3",
            previous_version="1.2",
            change_notes="Increased retention_ratio threshold to 1.1",
            tags=["youtube", "breakout", "engagement"]
        ),
        max_total_actions=3,
        global_cooldown_minutes=45,
        requires_risk_simulation=True,
        requires_supervisor_approval=False,
        max_allowed_risk_score=0.5,
        max_allowed_aggressiveness=0.7
    )


if __name__ == "__main__":
    # Example usage
    policy = create_example_policy()
    print("✓ Example policy created")
    print(f"  ID: {policy.policy_id}")
    print(f"  Status: {policy.status.value}")
    print(f"  Confidence: {policy.confidence_weight}")
    
    # Test serialization
    policy_json = policy.to_json()
    print(f"\n✓ Serialized to JSON ({len(policy_json)} chars)")
    
    # Test deserialization
    policy_restored = Policy.from_json(policy_json)
    print(f"✓ Deserialized from JSON")
    print(f"  Restored ID: {policy_restored.policy_id}")
    
    # Test applicability
    context = {
        'account_state': 'near_breakout',
        'comments_to_breakout': 3,
        'retention_ratio': 1.15,
        'identity_risk': 0.3,
        'aggressiveness_score': 0.6,
        'current_risk_score': 0.2,
        'current_aggressiveness': 0.5
    }
    
    is_applicable = policy.is_applicable(context)
    score = policy.calculate_applicability_score(context)
    
    print(f"\n✓ Policy evaluation:")
    print(f"  Applicable: {is_applicable}")
    print(f"  Score: {score:.2f}")
