"""
Rules Adapter - Connect Rules Engine to Orchestrator

Complete decision flow:
1. Build state snapshot
2. Load and merge rules
3. Evaluate rules against state
4. Check cost guards
5. Execute action
6. Log telemetry
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..rules_engine.loader_v2 import RulesLoaderV2
from ..rules_engine.rule_context import RuleContextBuilder, StateSnapshot
from ..rules_engine.evaluator_v2 import RulesEvaluatorV2, DecisionResult
from ..rules_engine.actions_v2 import ActionExecutorV2, ActionResult
from ..rules_engine.cost_guards import CostGuard


logger = logging.getLogger(__name__)


class RulesAdapter:
    """
    Adapter connecting Rules Engine to Orchestrator.
    
    Flow:
        Content arrives → Build snapshot → Evaluate → Check guards → Execute → Log
    """
    
    def __init__(
        self,
        rules_base_dir: str = "/workspaces/stakazo/backend/app/rules_engine",
        daily_budget_limit: float = 10.0,
        monthly_budget_limit: float = 30.0,
        action_cost_limit: float = 0.10
    ):
        """
        Initialize adapter.
        
        Args:
            rules_base_dir: Base directory for rules files
            daily_budget_limit: Daily budget limit (EUR)
            monthly_budget_limit: Monthly budget limit (EUR)
            action_cost_limit: Per-action cost limit (EUR)
        """
        self.rules_base_dir = rules_base_dir
        
        # Initialize components
        self.loader = RulesLoaderV2(base_dir=rules_base_dir)
        self.context_builder = RuleContextBuilder()
        self.cost_guard = CostGuard(
            daily_limit=daily_budget_limit,
            monthly_limit=monthly_budget_limit,
            action_limit=action_cost_limit
        )
        self.executor = ActionExecutorV2()
        
        # Load rules once at startup
        self.ruleset = self.loader.load_and_merge()
        self.evaluator = RulesEvaluatorV2(self.ruleset)
        
        logger.info(f"RulesAdapter initialized with {len(self.ruleset.rules)} rules")
    
    async def make_decision(
        self,
        content: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Make decision for content.
        
        Complete flow:
        1. Build state snapshot
        2. Evaluate rules
        3. Check cost guards
        4. Execute action (if allowed)
        5. Log telemetry
        
        Args:
            content: Content to evaluate (optional for system-level decisions)
            force_refresh: Force refresh of cached state
            
        Returns:
            Complete decision result with action outcome
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Build state snapshot
            logger.info("Building state snapshot...")
            snapshot = await self.context_builder.build_snapshot(
                content=content,
                force_refresh=force_refresh
            )
            
            # Validate snapshot
            validation = self.context_builder.validate_snapshot(snapshot)
            if not validation["is_valid"]:
                logger.warning(f"Snapshot validation failed: {validation['errors']}")
                return {
                    "success": False,
                    "error": "INVALID_SNAPSHOT",
                    "validation": validation,
                    "timestamp": start_time.isoformat()
                }
            
            logger.info(f"Snapshot built: {snapshot.snapshot_id} (completeness: {validation['completeness_score']:.0%})")
            
            # Step 2: Evaluate rules
            logger.info("Evaluating rules...")
            decision = await self.evaluator.evaluate(snapshot)
            
            logger.info(
                f"Decision: {decision.recommended_action.value} "
                f"(priority: {decision.action_priority.value}, "
                f"confidence: {decision.confidence:.0%}, "
                f"eval time: {decision.evaluation_time_ms:.2f}ms)"
            )
            
            # Step 3: Check cost guards
            logger.info("Checking cost guards...")
            cost_check = self.cost_guard.check(decision, snapshot.cost_tracking)
            
            if not cost_check.allowed:
                logger.warning(f"Cost guard blocked action: {cost_check.reason}")
                return {
                    "success": False,
                    "error": "BUDGET_EXCEEDED",
                    "snapshot_id": snapshot.snapshot_id,
                    "decision": self._format_decision(decision),
                    "cost_check": self._format_cost_check(cost_check),
                    "timestamp": start_time.isoformat()
                }
            
            if cost_check.warnings:
                logger.warning(f"Cost warnings: {cost_check.warnings}")
            
            # Step 4: Safety check
            safety_ok, safety_reason = self.cost_guard.check_safety(
                decision,
                {
                    "orchestrator_state": snapshot.orchestrator_state,
                    "cost_tracking": snapshot.cost_tracking
                }
            )
            
            if not safety_ok:
                logger.warning(f"Safety check failed: {safety_reason}")
                return {
                    "success": False,
                    "error": "SAFETY_CHECK_FAILED",
                    "snapshot_id": snapshot.snapshot_id,
                    "decision": self._format_decision(decision),
                    "safety_reason": safety_reason,
                    "timestamp": start_time.isoformat()
                }
            
            # Step 5: Check if requires human approval
            if decision.requires_human_approval:
                logger.info("Action requires human approval - waiting...")
                return {
                    "success": False,
                    "error": "REQUIRES_APPROVAL",
                    "snapshot_id": snapshot.snapshot_id,
                    "decision": self._format_decision(decision),
                    "approval_required": True,
                    "timestamp": start_time.isoformat()
                }
            
            # Step 6: Execute action
            logger.info(f"Executing action: {decision.recommended_action.value}...")
            action_result = await self.executor.execute(decision, snapshot)
            
            logger.info(
                f"Action executed: {action_result.status.value} "
                f"(success: {action_result.success}, "
                f"exec time: {action_result.execution_time_ms:.2f}ms, "
                f"retries: {action_result.retries})"
            )
            
            # Step 7: Log telemetry
            end_time = datetime.utcnow()
            total_time_ms = (end_time - start_time).total_seconds() * 1000
            
            telemetry = {
                "snapshot_id": snapshot.snapshot_id,
                "decision": self._format_decision(decision),
                "cost_check": self._format_cost_check(cost_check),
                "action_result": self._format_action_result(action_result),
                "timing": {
                    "total_ms": total_time_ms,
                    "evaluation_ms": decision.evaluation_time_ms,
                    "execution_ms": action_result.execution_time_ms
                },
                "timestamp": start_time.isoformat()
            }
            
            await self._log_telemetry(telemetry)
            
            return {
                "success": action_result.success,
                "snapshot_id": snapshot.snapshot_id,
                "decision": self._format_decision(decision),
                "action_result": self._format_action_result(action_result),
                "cost_check": self._format_cost_check(cost_check),
                "timing": telemetry["timing"],
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Decision flow failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "DECISION_FLOW_ERROR",
                "error_message": str(e),
                "timestamp": start_time.isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            System status with budget, health, and rules info
        """
        # Build snapshot for current state
        snapshot = await self.context_builder.build_snapshot(force_refresh=True)
        
        # Get budget summary
        budget_summary = self.cost_guard.get_budget_summary(snapshot.cost_tracking)
        
        # Check for anomalies
        has_anomalies, anomalies = self.cost_guard.detect_anomalies(snapshot.cost_tracking)
        
        # Get snapshot summary
        snapshot_summary = self.context_builder.get_snapshot_summary(snapshot)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot_id": snapshot.snapshot_id,
            "rules": {
                "total": len(self.ruleset.rules),
                "enabled": sum(1 for r in self.ruleset.rules if r.enabled),
                "by_priority": {
                    "CRITICAL": sum(1 for r in self.ruleset.rules if r.priority.value == "CRITICAL" and r.enabled),
                    "HIGH": sum(1 for r in self.ruleset.rules if r.priority.value == "HIGH" and r.enabled),
                    "MEDIUM": sum(1 for r in self.ruleset.rules if r.priority.value == "MEDIUM" and r.enabled),
                    "LOW": sum(1 for r in self.ruleset.rules if r.priority.value == "LOW" and r.enabled)
                }
            },
            "budget": budget_summary,
            "anomalies": {
                "detected": has_anomalies,
                "details": anomalies
            },
            "snapshot": snapshot_summary,
            "health": snapshot.orchestrator_state.get("system_health", {})
        }
    
    async def reload_rules(self) -> Dict[str, Any]:
        """
        Reload rules from disk.
        
        Returns:
            Reload result with rules count
        """
        logger.info("Reloading rules...")
        
        try:
            # Reload ruleset
            self.ruleset = self.loader.load_and_merge()
            
            # Recreate evaluator with new rules
            self.evaluator = RulesEvaluatorV2(self.ruleset)
            
            logger.info(f"Rules reloaded: {len(self.ruleset.rules)} total")
            
            return {
                "success": True,
                "rules_loaded": len(self.ruleset.rules),
                "enabled": sum(1 for r in self.ruleset.rules if r.enabled),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_decision(self, decision: DecisionResult) -> Dict[str, Any]:
        """Format decision for output."""
        return {
            "action": decision.recommended_action.value,
            "priority": decision.action_priority.value,
            "confidence": f"{decision.confidence:.0%}",
            "triggered_rules": len(decision.triggered_rules),
            "requires_approval": decision.requires_human_approval,
            "reasoning": decision.reasoning[:3],  # Top 3 reasons
            "warnings": decision.warnings,
            "evaluation_time_ms": f"{decision.evaluation_time_ms:.2f}"
        }
    
    def _format_cost_check(self, cost_check) -> Dict[str, Any]:
        """Format cost check for output."""
        return {
            "allowed": cost_check.allowed,
            "status": cost_check.status.value,
            "reason": cost_check.reason,
            "daily": {
                "spend": f"€{cost_check.daily_spend:.2f}",
                "limit": f"€{cost_check.daily_limit:.2f}",
                "remaining": f"€{cost_check.daily_remaining:.2f}"
            },
            "monthly": {
                "spend": f"€{cost_check.monthly_spend:.2f}",
                "limit": f"€{cost_check.monthly_limit:.2f}",
                "remaining": f"€{cost_check.monthly_remaining:.2f}"
            },
            "action_cost": f"€{cost_check.estimated_action_cost:.2f}",
            "warnings": cost_check.warnings
        }
    
    def _format_action_result(self, result: ActionResult) -> Dict[str, Any]:
        """Format action result for output."""
        return {
            "action": result.action.value,
            "status": result.status.value,
            "success": result.success,
            "message": result.message,
            "execution_time_ms": f"{result.execution_time_ms:.2f}",
            "retries": result.retries,
            "output": result.output,
            "error": result.error
        }
    
    async def _log_telemetry(self, telemetry: Dict[str, Any]):
        """Log telemetry to orchestrator."""
        # TODO: Send to actual orchestrator/logging system
        # await self.orchestrator_api.log_telemetry(telemetry)
        
        logger.info(f"[TELEMETRY] Decision logged: {telemetry['snapshot_id']}")
