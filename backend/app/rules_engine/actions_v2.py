"""
Action Executor v2 - Execute recommended actions from evaluator

Executes actions across all engines:
- Satellite Engine (post, reschedule, boost)
- Content Engine (rerender, select clips)
- CM (update plan, interrogation)
- Meta Ads (budget, campaigns)
- Orchestrator (logging, alerts)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import logging

from .evaluator_v2 import ActionType, DecisionResult
from .rule_context import StateSnapshot, Platform


logger = logging.getLogger(__name__)


class ActionStatus(str, Enum):
    """Status of action execution."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REQUIRES_APPROVAL = "requires_approval"


class ActionResult(BaseModel):
    """Result of action execution."""
    action: ActionType
    status: ActionStatus
    timestamp: datetime
    
    # Result details
    success: bool
    message: str
    
    # Execution details
    execution_time_ms: float
    retries: int = 0
    
    # Output data
    output: Dict[str, Any] = {}
    
    # Errors
    error: Optional[str] = None
    

class ActionExecutorV2:
    """
    Execute actions recommended by RulesEvaluatorV2.
    
    Handles:
    - Satellite operations
    - Content operations
    - CM operations
    - Meta Ads operations
    - Orchestrator operations
    """
    
    def __init__(
        self,
        satellite_api=None,
        content_api=None,
        cm_api=None,
        metaads_api=None,
        orchestrator_api=None,
        telegram_api=None
    ):
        """
        Initialize executor with API clients.
        
        Args:
            satellite_api: Satellite Engine API client
            content_api: Content Engine API client
            cm_api: Community Manager API client
            metaads_api: Meta Ads API client
            orchestrator_api: Orchestrator API client
            telegram_api: Telegram Bot API client
        """
        self.satellite_api = satellite_api
        self.content_api = content_api
        self.cm_api = cm_api
        self.metaads_api = metaads_api
        self.orchestrator_api = orchestrator_api
        self.telegram_api = telegram_api
        
        # Action routing
        self.action_handlers = {
            ActionType.POST_SHORT: self._execute_post_short,
            ActionType.HOLD_CONTENT: self._execute_hold_content,
            ActionType.REQUEST_REVIEW: self._execute_request_review,
            ActionType.FORCE_RERENDER: self._execute_force_rerender,
            ActionType.SELECT_NEW_CLIPS: self._execute_select_new_clips,
            ActionType.POST_TO_SATELLITE: self._execute_post_to_satellite,
            ActionType.RESCHEDULE_POST: self._execute_reschedule_post,
            ActionType.BOOST_POST: self._execute_boost_post,
            ActionType.UPDATE_CONTENT_PLAN: self._execute_update_content_plan,
            ActionType.REQUEST_BRAND_INTERROGATION: self._execute_brand_interrogation,
            ActionType.REFINE_GUIDELINES: self._execute_refine_guidelines,
            ActionType.ADJUST_BUDGET: self._execute_adjust_budget,
            ActionType.START_CAMPAIGN: self._execute_start_campaign,
            ActionType.PAUSE_CAMPAIGN: self._execute_pause_campaign,
            ActionType.LOG_DECISION: self._execute_log_decision,
            ActionType.PUSH_ALERT_TELEGRAM: self._execute_push_alert,
            ActionType.REQUEST_HUMAN_APPROVAL: self._execute_request_approval,
            ActionType.REJECT_CONTENT: self._execute_reject_content,
            ActionType.EMERGENCY_PAUSE: self._execute_emergency_pause
        }
    
    async def execute(
        self,
        decision: DecisionResult,
        snapshot: StateSnapshot,
        max_retries: int = 3
    ) -> ActionResult:
        """
        Execute action from decision result.
        
        Args:
            decision: Decision from evaluator
            snapshot: Current state snapshot
            max_retries: Maximum retry attempts
            
        Returns:
            ActionResult with execution details
        """
        import time
        start_time = time.time()
        
        action = decision.recommended_action
        
        # Check if requires human approval
        if decision.requires_human_approval:
            logger.info(f"Action {action} requires human approval")
            return ActionResult(
                action=action,
                status=ActionStatus.REQUIRES_APPROVAL,
                timestamp=datetime.utcnow(),
                success=False,
                message="Action requires human approval",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Get handler
        handler = self.action_handlers.get(action)
        if not handler:
            logger.error(f"No handler for action: {action}")
            return ActionResult(
                action=action,
                status=ActionStatus.FAILED,
                timestamp=datetime.utcnow(),
                success=False,
                message=f"No handler for action: {action}",
                execution_time_ms=(time.time() - start_time) * 1000,
                error="MISSING_HANDLER"
            )
        
        # Execute with retries
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                result = await handler(decision, snapshot)
                execution_time = (time.time() - start_time) * 1000
                
                result.execution_time_ms = execution_time
                result.retries = retries
                
                logger.info(f"Action {action} executed successfully in {execution_time:.2f}ms")
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Action {action} failed (attempt {retries + 1}/{max_retries + 1}): {e}")
                retries += 1
                
                if retries <= max_retries:
                    await self._wait_before_retry(retries)
        
        # All retries failed
        execution_time = (time.time() - start_time) * 1000
        return ActionResult(
            action=action,
            status=ActionStatus.FAILED,
            timestamp=datetime.utcnow(),
            success=False,
            message=f"Action failed after {retries} retries",
            execution_time_ms=execution_time,
            retries=retries,
            error=last_error
        )
    
    async def _wait_before_retry(self, retry_num: int):
        """Exponential backoff before retry."""
        import asyncio
        wait_time = min(2 ** retry_num, 10)  # Max 10 seconds
        await asyncio.sleep(wait_time)
    
    # ============================================================
    # CONTENT ACTIONS
    # ============================================================
    
    async def _execute_post_short(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Post short to official channel."""
        params = decision.action_params
        platform = params.get("platform", Platform.TIKTOK)
        
        if not snapshot.content:
            return ActionResult(
                action=ActionType.POST_SHORT,
                status=ActionStatus.FAILED,
                timestamp=datetime.utcnow(),
                success=False,
                message="No content to post",
                execution_time_ms=0.0
            )
        
        # TODO: Replace with actual API call
        # result = await self.satellite_api.post_short(
        #     content=snapshot.content,
        #     platform=platform,
        #     schedule_time=params.get("schedule_time")
        # )
        
        logger.info(f"[MOCK] Posting short to {platform} (official)")
        
        return ActionResult(
            action=ActionType.POST_SHORT,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message=f"Short posted to {platform} (official)",
            execution_time_ms=0.0,
            output={
                "platform": platform,
                "post_id": "mock_post_123",
                "scheduled": params.get("schedule_time") is not None
            }
        )
    
    async def _execute_hold_content(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Hold content - do not post."""
        logger.info("[MOCK] Holding content - not posting")
        
        return ActionResult(
            action=ActionType.HOLD_CONTENT,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Content held - not posting",
            execution_time_ms=0.0,
            output={
                "reason": decision.action_params.get("reason", "Does not meet standards")
            }
        )
    
    async def _execute_request_review(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Request human review."""
        # TODO: Send Telegram notification
        # await self.telegram_api.send_message(...)
        
        logger.info("[MOCK] Requesting human review via Telegram")
        
        return ActionResult(
            action=ActionType.REQUEST_REVIEW,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Review request sent",
            execution_time_ms=0.0,
            output={
                "notification_sent": True,
                "reason": decision.action_params.get("reason", "Needs review")
            }
        )
    
    async def _execute_force_rerender(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Force content rerender."""
        # TODO: Trigger rerender job
        # await self.content_api.trigger_rerender(...)
        
        logger.info("[MOCK] Triggering content rerender")
        
        return ActionResult(
            action=ActionType.FORCE_RERENDER,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Rerender job triggered",
            execution_time_ms=0.0,
            output={"job_id": "mock_job_456"}
        )
    
    async def _execute_select_new_clips(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Select new clips for content."""
        # TODO: Trigger clip selection
        # await self.content_api.select_new_clips(...)
        
        logger.info("[MOCK] Selecting new clips")
        
        return ActionResult(
            action=ActionType.SELECT_NEW_CLIPS,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="New clips selected",
            execution_time_ms=0.0,
            output={"clips_selected": 5}
        )
    
    # ============================================================
    # SATELLITE ACTIONS
    # ============================================================
    
    async def _execute_post_to_satellite(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Post to satellite channel."""
        params = decision.action_params
        platform = params.get("platform", Platform.TIKTOK)
        
        # TODO: Replace with actual API call
        # result = await self.satellite_api.post_to_satellite(...)
        
        logger.info(f"[MOCK] Posting to satellite channel on {platform}")
        
        return ActionResult(
            action=ActionType.POST_TO_SATELLITE,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message=f"Posted to satellite on {platform}",
            execution_time_ms=0.0,
            output={
                "platform": platform,
                "satellite_post_id": "mock_sat_789",
                "immediate": params.get("immediate", False)
            }
        )
    
    async def _execute_reschedule_post(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Reschedule post."""
        logger.info("[MOCK] Rescheduling post")
        
        return ActionResult(
            action=ActionType.RESCHEDULE_POST,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Post rescheduled",
            execution_time_ms=0.0
        )
    
    async def _execute_boost_post(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Boost existing post."""
        logger.info("[MOCK] Boosting post")
        
        return ActionResult(
            action=ActionType.BOOST_POST,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Post boosted",
            execution_time_ms=0.0
        )
    
    # ============================================================
    # CM ACTIONS
    # ============================================================
    
    async def _execute_update_content_plan(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Update CM content plan."""
        # TODO: Update CM plan
        # await self.cm_api.update_plan(...)
        
        logger.info("[MOCK] Updating CM content plan")
        
        return ActionResult(
            action=ActionType.UPDATE_CONTENT_PLAN,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Content plan updated",
            execution_time_ms=0.0
        )
    
    async def _execute_brand_interrogation(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Request brand interrogation."""
        logger.info("[MOCK] Requesting brand interrogation")
        
        return ActionResult(
            action=ActionType.REQUEST_BRAND_INTERROGATION,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Brand interrogation requested",
            execution_time_ms=0.0
        )
    
    async def _execute_refine_guidelines(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Refine brand guidelines."""
        logger.info("[MOCK] Refining brand guidelines")
        
        return ActionResult(
            action=ActionType.REFINE_GUIDELINES,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Guidelines refined",
            execution_time_ms=0.0
        )
    
    # ============================================================
    # META ADS ACTIONS
    # ============================================================
    
    async def _execute_adjust_budget(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Adjust Meta Ads budget."""
        # TODO: Adjust budget via Meta Ads API
        # await self.metaads_api.adjust_budget(...)
        
        logger.info("[MOCK] Adjusting Meta Ads budget")
        
        return ActionResult(
            action=ActionType.ADJUST_BUDGET,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Budget adjusted",
            execution_time_ms=0.0
        )
    
    async def _execute_start_campaign(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Start Meta Ads campaign."""
        logger.info("[MOCK] Starting Meta Ads campaign")
        
        return ActionResult(
            action=ActionType.START_CAMPAIGN,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Campaign started",
            execution_time_ms=0.0
        )
    
    async def _execute_pause_campaign(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Pause Meta Ads campaign."""
        logger.info("[MOCK] Pausing Meta Ads campaign")
        
        return ActionResult(
            action=ActionType.PAUSE_CAMPAIGN,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Campaign paused",
            execution_time_ms=0.0
        )
    
    # ============================================================
    # ORCHESTRATOR ACTIONS
    # ============================================================
    
    async def _execute_log_decision(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Log decision to orchestrator."""
        # TODO: Send to orchestrator
        # await self.orchestrator_api.log_decision(...)
        
        logger.info("[MOCK] Logging decision to orchestrator")
        
        return ActionResult(
            action=ActionType.LOG_DECISION,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Decision logged",
            execution_time_ms=0.0
        )
    
    async def _execute_push_alert(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Push alert to Telegram."""
        # TODO: Send Telegram alert
        # await self.telegram_api.send_alert(...)
        
        logger.info("[MOCK] Pushing alert to Telegram")
        
        return ActionResult(
            action=ActionType.PUSH_ALERT_TELEGRAM,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Alert sent to Telegram",
            execution_time_ms=0.0
        )
    
    async def _execute_request_approval(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Request human approval."""
        logger.info("[MOCK] Requesting human approval")
        
        return ActionResult(
            action=ActionType.REQUEST_HUMAN_APPROVAL,
            status=ActionStatus.REQUIRES_APPROVAL,
            timestamp=datetime.utcnow(),
            success=False,
            message="Awaiting human approval",
            execution_time_ms=0.0
        )
    
    # ============================================================
    # SAFETY ACTIONS
    # ============================================================
    
    async def _execute_reject_content(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Reject content."""
        logger.info("[MOCK] Rejecting content")
        
        return ActionResult(
            action=ActionType.REJECT_CONTENT,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Content rejected",
            execution_time_ms=0.0,
            output={
                "reason": decision.action_params.get("reason", "Does not meet standards")
            }
        )
    
    async def _execute_emergency_pause(
        self, decision: DecisionResult, snapshot: StateSnapshot
    ) -> ActionResult:
        """Emergency pause all operations."""
        logger.warning("[MOCK] EMERGENCY PAUSE triggered")
        
        # TODO: Pause all operations
        # await self.orchestrator_api.emergency_pause()
        
        return ActionResult(
            action=ActionType.EMERGENCY_PAUSE,
            status=ActionStatus.SUCCESS,
            timestamp=datetime.utcnow(),
            success=True,
            message="Emergency pause activated",
            execution_time_ms=0.0
        )
