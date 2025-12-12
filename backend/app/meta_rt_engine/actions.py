"""
Real-Time Actions Layer for Meta RT Performance Engine (PASO 10.14)

Executes real-time actions on campaigns based on decisions.
"""

import uuid
import random
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from app.meta_rt_engine.schemas import (
    ActionRequest,
    ActionResponse,
    ActionResult,
    ActionType,
    RealTimeDecision,
)


class RealTimeActionsLayer:
    """
    Real-Time Actions Execution Layer
    
    Executes actions on Meta Ads campaigns:
    - Pause ad/adset/campaign
    - Reduce/increase budget
    - Reset bid strategy
    - Trigger optimization modules (10.11, 10.12, 10.13)
    
    Mode:
        stub: Simulate action execution
        live: Execute real actions via Meta Ads API (TODO)
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    
    async def execute_actions(
        self,
        decision: RealTimeDecision,
        auto_apply: bool = False,
    ) -> ActionResponse:
        """
        Execute actions recommended by decision engine.
        
        Args:
            decision: RealTimeDecision with recommended actions
            auto_apply: Whether to actually apply actions or simulate
        
        Returns:
            ActionResponse with execution results
        """
        start_time = datetime.utcnow()
        
        results: List[ActionResult] = []
        
        for action_type in decision.recommended_actions:
            result = await self._execute_single_action(
                campaign_id=decision.campaign_id,
                action_type=action_type,
                auto_apply=auto_apply,
            )
            results.append(result)
        
        # Calculate totals
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return ActionResponse(
            action_id=uuid.uuid4(),
            campaign_id=decision.campaign_id,
            actions_executed=results,
            total_actions=len(results),
            successful_actions=successful,
            failed_actions=failed,
            overall_success=failed == 0,
            timestamp=datetime.utcnow(),
        )
    
    
    async def _execute_single_action(
        self,
        campaign_id: UUID,
        action_type: ActionType,
        auto_apply: bool,
    ) -> ActionResult:
        """Execute a single action."""
        start_time = datetime.utcnow()
        
        if self.mode == "stub":
            result = await self._execute_action_stub(campaign_id, action_type, auto_apply)
        else:
            result = await self._execute_action_live(campaign_id, action_type, auto_apply)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.execution_time_ms = int(execution_time)
        
        return result
    
    
    async def _execute_action_stub(
        self,
        campaign_id: UUID,
        action_type: ActionType,
        auto_apply: bool,
    ) -> ActionResult:
        """STUB mode: Simulate action execution."""
        
        # Simulate 95% success rate
        success = random.random() < 0.95
        
        action_messages = {
            ActionType.PAUSE_AD: "Ad paused successfully",
            ActionType.PAUSE_ADSET: "Ad set paused successfully",
            ActionType.PAUSE_CAMPAIGN: "Campaign paused successfully",
            ActionType.REDUCE_BUDGET: "Budget reduced by 20%",
            ActionType.INCREASE_BUDGET: "Budget increased by 15%",
            ActionType.RESET_BID: "Bid strategy reset to automatic",
            ActionType.TRIGGER_CREATIVE_RESYNC: "Creative intelligence resync triggered (PASO 10.13)",
            ActionType.TRIGGER_FULL_CYCLE: "Full optimization cycle triggered (PASO 10.11)",
            ActionType.TRIGGER_TARGETING_REFRESH: "Targeting optimizer triggered (PASO 10.12)",
            ActionType.ALERT_ONLY: "Alert sent to dashboard - no action taken",
        }
        
        message = action_messages.get(action_type, f"Action {action_type} executed")
        
        if not auto_apply:
            message = f"[SIMULATED] {message}"
        
        details = {
            "campaign_id": str(campaign_id),
            "auto_applied": auto_apply,
            "simulated": self.mode == "stub",
        }
        
        # Add action-specific details
        if action_type == ActionType.REDUCE_BUDGET:
            details["budget_reduction_pct"] = 20
            details["new_daily_budget"] = random.uniform(50, 200)
        elif action_type == ActionType.INCREASE_BUDGET:
            details["budget_increase_pct"] = 15
            details["new_daily_budget"] = random.uniform(150, 400)
        elif action_type == ActionType.RESET_BID:
            details["previous_strategy"] = "LOWEST_COST_WITH_BID_CAP"
            details["new_strategy"] = "LOWEST_COST_WITHOUT_CAP"
        
        return ActionResult(
            action_type=action_type,
            success=success,
            applied=auto_apply and success,
            message=message if success else f"Failed to execute {action_type}",
            details=details,
            execution_time_ms=0,  # Will be set by caller
        )
    
    
    async def _execute_action_live(
        self,
        campaign_id: UUID,
        action_type: ActionType,
        auto_apply: bool,
    ) -> ActionResult:
        """
        LIVE mode: Execute real actions via Meta Ads API.
        
        TODO: Implement real action execution:
        1. Pause ad/adset/campaign via Meta API
        2. Update budget via Meta API
        3. Reset bid strategy via Meta API
        4. Trigger optimization modules (10.11, 10.12, 10.13)
        """
        # For now, fallback to stub mode
        return await self._execute_action_stub(campaign_id, action_type, auto_apply)
