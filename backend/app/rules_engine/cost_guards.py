"""
Cost Guards - Budget enforcement and safety checks

Enforces:
- Daily budget limit (<€10)
- Per-action cost limit (<€0.10)
- Monthly budget limit (<€30)
- Safety checks for dangerous actions
- Anomaly detection
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
import logging

from .evaluator_v2 import ActionType, DecisionResult


logger = logging.getLogger(__name__)


class BudgetStatus(str, Enum):
    """Status of budget check."""
    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    ANOMALY = "anomaly"


class CostGuardResult(BaseModel):
    """Result of cost guard check."""
    allowed: bool
    status: BudgetStatus
    reason: str
    
    # Budget details
    daily_spend: float
    daily_limit: float
    daily_remaining: float
    
    monthly_spend: float
    monthly_limit: float
    monthly_remaining: float
    
    # Action cost
    estimated_action_cost: float
    action_cost_limit: float
    
    # Warnings
    warnings: List[str] = []


class CostGuard:
    """
    Enforce budget limits and safety checks.
    
    Limits:
    - Daily: <€10
    - Per-action: <€0.10
    - Monthly: <€30
    """
    
    # Default limits (in EUR)
    DEFAULT_DAILY_LIMIT = 10.0
    DEFAULT_MONTHLY_LIMIT = 30.0
    DEFAULT_ACTION_LIMIT = 0.10
    
    # Warning thresholds
    WARNING_THRESHOLD = 0.90  # Warn at 90% of limit
    
    # Action costs (estimates in EUR)
    ACTION_COSTS = {
        ActionType.POST_SHORT: 0.02,
        ActionType.POST_TO_SATELLITE: 0.01,
        ActionType.FORCE_RERENDER: 0.05,
        ActionType.BOOST_POST: 0.08,
        ActionType.START_CAMPAIGN: 0.10,
        ActionType.ADJUST_BUDGET: 0.02,
        ActionType.SELECT_NEW_CLIPS: 0.03,
        ActionType.REQUEST_BRAND_INTERROGATION: 0.05,
        # Free actions
        ActionType.HOLD_CONTENT: 0.0,
        ActionType.REQUEST_REVIEW: 0.0,
        ActionType.LOG_DECISION: 0.0,
        ActionType.PUSH_ALERT_TELEGRAM: 0.0,
        ActionType.REQUEST_HUMAN_APPROVAL: 0.0,
        ActionType.REJECT_CONTENT: 0.0,
        ActionType.EMERGENCY_PAUSE: 0.0
    }
    
    def __init__(
        self,
        daily_limit: float = DEFAULT_DAILY_LIMIT,
        monthly_limit: float = DEFAULT_MONTHLY_LIMIT,
        action_limit: float = DEFAULT_ACTION_LIMIT
    ):
        """
        Initialize cost guard.
        
        Args:
            daily_limit: Daily budget limit (EUR)
            monthly_limit: Monthly budget limit (EUR)
            action_limit: Per-action cost limit (EUR)
        """
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.action_limit = action_limit
    
    def check(
        self,
        decision: DecisionResult,
        cost_tracking: Dict[str, Any]
    ) -> CostGuardResult:
        """
        Check if action is allowed based on budget constraints.
        
        Args:
            decision: Decision from evaluator
            cost_tracking: Current cost tracking data
            
        Returns:
            CostGuardResult with allowed status and details
        """
        action = decision.recommended_action
        
        # Get current spend
        daily_spend = cost_tracking.get("daily_spend", 0.0)
        monthly_spend = cost_tracking.get("monthly_spend", 0.0)
        
        # Get limits
        daily_limit = cost_tracking.get("daily_limit", self.daily_limit)
        monthly_limit = cost_tracking.get("monthly_limit", self.monthly_limit)
        
        # Estimate action cost
        estimated_cost = self.ACTION_COSTS.get(action, 0.01)
        
        # Calculate remaining budgets
        daily_remaining = daily_limit - daily_spend
        monthly_remaining = monthly_limit - monthly_spend
        
        warnings = []
        
        # Check 1: Daily limit
        if daily_spend >= daily_limit:
            logger.warning(f"Daily budget exceeded: €{daily_spend:.2f}/€{daily_limit:.2f}")
            return CostGuardResult(
                allowed=False,
                status=BudgetStatus.EXCEEDED,
                reason=f"Daily budget exceeded: €{daily_spend:.2f}/€{daily_limit:.2f}",
                daily_spend=daily_spend,
                daily_limit=daily_limit,
                daily_remaining=daily_remaining,
                monthly_spend=monthly_spend,
                monthly_limit=monthly_limit,
                monthly_remaining=monthly_remaining,
                estimated_action_cost=estimated_cost,
                action_cost_limit=self.action_limit
            )
        
        # Check 2: Monthly limit
        if monthly_spend >= monthly_limit:
            logger.warning(f"Monthly budget exceeded: €{monthly_spend:.2f}/€{monthly_limit:.2f}")
            return CostGuardResult(
                allowed=False,
                status=BudgetStatus.EXCEEDED,
                reason=f"Monthly budget exceeded: €{monthly_spend:.2f}/€{monthly_limit:.2f}",
                daily_spend=daily_spend,
                daily_limit=daily_limit,
                daily_remaining=daily_remaining,
                monthly_spend=monthly_spend,
                monthly_limit=monthly_limit,
                monthly_remaining=monthly_remaining,
                estimated_action_cost=estimated_cost,
                action_cost_limit=self.action_limit
            )
        
        # Check 3: Per-action cost
        if estimated_cost > self.action_limit:
            logger.warning(f"Action cost too high: €{estimated_cost:.2f} > €{self.action_limit:.2f}")
            return CostGuardResult(
                allowed=False,
                status=BudgetStatus.EXCEEDED,
                reason=f"Action cost €{estimated_cost:.2f} exceeds per-action limit €{self.action_limit:.2f}",
                daily_spend=daily_spend,
                daily_limit=daily_limit,
                daily_remaining=daily_remaining,
                monthly_spend=monthly_spend,
                monthly_limit=monthly_limit,
                monthly_remaining=monthly_remaining,
                estimated_action_cost=estimated_cost,
                action_cost_limit=self.action_limit
            )
        
        # Check 4: Would action exceed daily limit?
        if daily_spend + estimated_cost > daily_limit:
            logger.warning(f"Action would exceed daily limit: €{daily_spend + estimated_cost:.2f} > €{daily_limit:.2f}")
            return CostGuardResult(
                allowed=False,
                status=BudgetStatus.EXCEEDED,
                reason=f"Action would exceed daily limit: €{daily_spend + estimated_cost:.2f} > €{daily_limit:.2f}",
                daily_spend=daily_spend,
                daily_limit=daily_limit,
                daily_remaining=daily_remaining,
                monthly_spend=monthly_spend,
                monthly_limit=monthly_limit,
                monthly_remaining=monthly_remaining,
                estimated_action_cost=estimated_cost,
                action_cost_limit=self.action_limit
            )
        
        # Check 5: Would action exceed monthly limit?
        if monthly_spend + estimated_cost > monthly_limit:
            logger.warning(f"Action would exceed monthly limit: €{monthly_spend + estimated_cost:.2f} > €{monthly_limit:.2f}")
            return CostGuardResult(
                allowed=False,
                status=BudgetStatus.EXCEEDED,
                reason=f"Action would exceed monthly limit: €{monthly_spend + estimated_cost:.2f} > €{monthly_limit:.2f}",
                daily_spend=daily_spend,
                daily_limit=daily_limit,
                daily_remaining=daily_remaining,
                monthly_spend=monthly_spend,
                monthly_limit=monthly_limit,
                monthly_remaining=monthly_remaining,
                estimated_action_cost=estimated_cost,
                action_cost_limit=self.action_limit
            )
        
        # Check 6: Warning thresholds
        if daily_spend >= daily_limit * self.WARNING_THRESHOLD:
            warnings.append(
                f"Daily budget at {(daily_spend / daily_limit) * 100:.0f}%: €{daily_spend:.2f}/€{daily_limit:.2f}"
            )
        
        if monthly_spend >= monthly_limit * self.WARNING_THRESHOLD:
            warnings.append(
                f"Monthly budget at {(monthly_spend / monthly_limit) * 100:.0f}%: €{monthly_spend:.2f}/€{monthly_limit:.2f}"
            )
        
        # All checks passed
        status = BudgetStatus.WARNING if warnings else BudgetStatus.OK
        
        return CostGuardResult(
            allowed=True,
            status=status,
            reason="Budget check passed",
            daily_spend=daily_spend,
            daily_limit=daily_limit,
            daily_remaining=daily_remaining,
            monthly_spend=monthly_spend,
            monthly_limit=monthly_limit,
            monthly_remaining=monthly_remaining,
            estimated_action_cost=estimated_cost,
            action_cost_limit=self.action_limit,
            warnings=warnings
        )
    
    def check_safety(
        self,
        decision: DecisionResult,
        snapshot_state: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Check if action is safe to execute.
        
        Args:
            decision: Decision from evaluator
            snapshot_state: Current snapshot state
            
        Returns:
            (allowed, reason) tuple
        """
        action = decision.recommended_action
        
        # Dangerous actions that need extra checks
        dangerous_actions = [
            ActionType.EMERGENCY_PAUSE,
            ActionType.START_CAMPAIGN,
            ActionType.ADJUST_BUDGET
        ]
        
        if action in dangerous_actions:
            # Check if action is explicitly approved
            if not decision.action_params.get("approved", False):
                return False, f"Dangerous action {action.value} requires explicit approval"
        
        # Check system health
        orchestrator_state = snapshot_state.get("orchestrator_state", {})
        system_health = orchestrator_state.get("system_health", {})
        
        if system_health.get("status") == "degraded":
            logger.warning("System in degraded state - limiting actions")
            # Only allow safe actions
            safe_actions = [
                ActionType.LOG_DECISION,
                ActionType.HOLD_CONTENT,
                ActionType.REQUEST_REVIEW,
                ActionType.PUSH_ALERT_TELEGRAM
            ]
            if action not in safe_actions:
                return False, "System degraded - only safe actions allowed"
        
        if system_health.get("status") == "error":
            logger.error("System in error state - emergency pause recommended")
            return False, "System in error state - action blocked"
        
        return True, "Safety check passed"
    
    def detect_anomalies(
        self,
        cost_tracking: Dict[str, Any],
        historical_costs: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[bool, List[str]]:
        """
        Detect unusual spending patterns.
        
        Args:
            cost_tracking: Current cost tracking data
            historical_costs: Historical cost data for comparison
            
        Returns:
            (has_anomalies, anomalies) tuple
        """
        anomalies = []
        
        daily_spend = cost_tracking.get("daily_spend", 0.0)
        
        # Check 1: Sudden spike in daily spend
        if historical_costs:
            recent_costs = historical_costs[-7:]  # Last 7 days
            if recent_costs:
                avg_daily = sum(c.get("daily_spend", 0.0) for c in recent_costs) / len(recent_costs)
                
                if daily_spend > avg_daily * 3:
                    anomalies.append(
                        f"Unusual spike in daily spend: €{daily_spend:.2f} vs avg €{avg_daily:.2f}"
                    )
        
        # Check 2: Too many expensive actions
        per_action_costs = cost_tracking.get("per_action_costs", [])
        expensive_actions = [c for c in per_action_costs if c > 0.05]
        
        if len(expensive_actions) > 10:
            anomalies.append(
                f"Too many expensive actions today: {len(expensive_actions)} actions >€0.05"
            )
        
        # Check 3: Rapid cost accumulation
        last_hour_spend = cost_tracking.get("last_hour_spend", 0.0)
        if last_hour_spend > daily_spend * 0.5:
            anomalies.append(
                f"Rapid cost accumulation: €{last_hour_spend:.2f} in last hour (50% of daily)"
            )
        
        has_anomalies = len(anomalies) > 0
        
        if has_anomalies:
            logger.warning(f"Cost anomalies detected: {anomalies}")
        
        return has_anomalies, anomalies
    
    def get_budget_summary(self, cost_tracking: Dict[str, Any]) -> Dict[str, Any]:
        """Get human-readable budget summary."""
        daily_spend = cost_tracking.get("daily_spend", 0.0)
        monthly_spend = cost_tracking.get("monthly_spend", 0.0)
        daily_limit = cost_tracking.get("daily_limit", self.daily_limit)
        monthly_limit = cost_tracking.get("monthly_limit", self.monthly_limit)
        
        return {
            "daily": {
                "spend": f"€{daily_spend:.2f}",
                "limit": f"€{daily_limit:.2f}",
                "remaining": f"€{daily_limit - daily_spend:.2f}",
                "percentage": f"{(daily_spend / daily_limit) * 100:.0f}%"
            },
            "monthly": {
                "spend": f"€{monthly_spend:.2f}",
                "limit": f"€{monthly_limit:.2f}",
                "remaining": f"€{monthly_limit - monthly_spend:.2f}",
                "percentage": f"{(monthly_spend / monthly_limit) * 100:.0f}%"
            },
            "status": self._get_status_emoji(daily_spend, daily_limit, monthly_spend, monthly_limit)
        }
    
    def _get_status_emoji(
        self, daily_spend: float, daily_limit: float,
        monthly_spend: float, monthly_limit: float
    ) -> str:
        """Get status emoji based on budget usage."""
        if daily_spend >= daily_limit or monthly_spend >= monthly_limit:
            return "🔴 EXCEEDED"
        elif daily_spend >= daily_limit * 0.9 or monthly_spend >= monthly_limit * 0.9:
            return "🟡 WARNING"
        else:
            return "🟢 OK"
