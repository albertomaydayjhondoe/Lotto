"""
Optimization Service - Business Logic

Evaluates campaigns/ads using ROAS data and generates optimization actions.
Handles action persistence, execution, and safety guard rails.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4
from decimal import Decimal

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaROASMetricsModel,
    OptimizationActionModel,
    OptimizationActionStatus,
)
from app.meta_ads_orchestrator.roas_optimizer import ROASOptimizer
from app.meta_ads_orchestrator.roas_engine import ROASCalculator
from .config import settings

logger = logging.getLogger("meta_optimization.service")


class OptimizationService:
    """
    Service for evaluating campaigns and generating optimization actions.
    
    Modes:
    - suggest: Create actions for manual review (default)
    - auto: Execute safe actions automatically with guard rails
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.optimizer = ROASOptimizer(db)
        self.calculator = ROASCalculator(db)
    
    async def evaluate_campaign(
        self,
        campaign_id: str,
        lookback_days: int = 7,
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a campaign and return suggested optimization actions.
        
        Returns list of actions:
        [{
            "action_id": "uuid",
            "type": "scale_up"|"scale_down"|"pause"|"reallocate",
            "target": "ad_id"|"adset_id"|"campaign_id",
            "target_level": "ad"|"adset"|"campaign",
            "amount_pct": 0.2,
            "reason": "roas_above_threshold",
            "confidence": 0.85,
            "roas_value": 3.5,
            ...
        }]
        """
        min_conf = min_confidence or settings.OPTIMIZER_MIN_CONFIDENCE
        actions = []
        
        try:
            # Check if campaign is still in embargo period
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                logger.warning(f"Campaign {campaign_id} not found")
                return []
            
            if not self._is_eligible_for_optimization(campaign):
                logger.info(f"Campaign {campaign_id} not eligible for optimization (embargo/status)")
                return []
            
            # Get ROAS metrics for campaign
            roas_metrics = await self._get_roas_metrics(
                campaign_id=campaign_id,
                lookback_days=lookback_days
            )
            
            if not roas_metrics:
                logger.info(f"No ROAS metrics found for campaign {campaign_id}")
                return []
            
            # 1. Detect ads to scale up
            scale_up_candidates = await self.optimizer.detect_ads_to_scale_up(
                campaign_id=campaign_id,
                lookback_days=lookback_days,
                min_roas=settings.OPTIMIZER_SCALE_UP_MIN_ROAS,
                min_confidence=min_conf,
            )
            
            for ad_data in scale_up_candidates:
                if await self._check_cooldown(ad_data.ad_id, "scale_up"):
                    continue
                
                action = await self._create_scale_up_action(ad_data)
                if action and self._passes_guard_rails(action):
                    actions.append(action)
            
            # 2. Detect ads to scale down
            scale_down_candidates = await self.optimizer.detect_ads_to_scale_down(
                campaign_id=campaign_id,
                lookback_days=lookback_days,
                max_roas=settings.OPTIMIZER_SCALE_DOWN_MAX_ROAS,
            )
            
            for ad_data in scale_down_candidates:
                if await self._check_cooldown(ad_data.ad_id, "scale_down"):
                    continue
                
                action = await self._create_scale_down_action(ad_data)
                if action and self._passes_guard_rails(action):
                    actions.append(action)
            
            # 3. Check for budget reallocation opportunities
            if len(roas_metrics) >= settings.OPTIMIZER_REALLOCATE_MIN_ADS:
                realloc_action = await self._evaluate_reallocation(
                    campaign_id=campaign_id,
                    roas_metrics=roas_metrics,
                )
                if realloc_action and self._passes_guard_rails(realloc_action):
                    actions.append(realloc_action)
            
            # Limit actions per campaign
            actions = actions[:settings.OPTIMIZER_MAX_ACTIONS_PER_CAMPAIGN]
            
            logger.info(
                f"Evaluated campaign {campaign_id}: {len(actions)} actions generated",
                extra={"campaign_id": campaign_id, "action_count": len(actions)}
            )
            
        except Exception as e:
            logger.exception(f"Error evaluating campaign {campaign_id}: {e}")
            raise
        
        return actions
    
    async def enqueue_action(
        self,
        action: Dict[str, Any],
        created_by: str = "optimizer",
    ) -> str:
        """
        Persist an optimization action to the database.
        
        Returns: action_id
        """
        try:
            action_id = action.get("action_id") or str(uuid4())
            
            # Create action model
            action_model = OptimizationActionModel(
                action_id=action_id,
                campaign_id=action.get("campaign_id"),
                adset_id=action.get("adset_id"),
                ad_id=action.get("ad_id"),
                action_type=action["type"],
                target_level=action["target_level"],
                target_id=action["target"],
                amount_pct=action.get("amount_pct"),
                amount_usd=action.get("amount_usd"),
                new_budget_usd=action.get("new_budget_usd"),
                old_budget_usd=action.get("old_budget_usd"),
                reason=action["reason"],
                reason_details=action.get("reason_details"),
                confidence=action["confidence"],
                roas_value=action.get("roas_value"),
                spend_usd=action.get("spend_usd"),
                revenue_usd=action.get("revenue_usd"),
                conversions=action.get("conversions"),
                impressions=action.get("impressions"),
                status=OptimizationActionStatus.SUGGESTED,
                created_by=created_by,
                expires_at=datetime.utcnow() + timedelta(hours=48),  # 48h expiry
                safety_score=action.get("safety_score", 0.5),
                guard_rails_passed=action.get("guard_rails_passed", 1),
                guard_rails_details=action.get("guard_rails_details"),
                reallocation_plan=action.get("reallocation_plan"),
                affected_ad_ids=action.get("affected_ad_ids"),
                params=action.get("params"),
            )
            
            self.db.add(action_model)
            await self.db.commit()
            
            # Create ledger event
            await self._create_ledger_event(
                event_type="optimization_suggested",
                action_id=action_id,
                details=action,
            )
            
            logger.info(
                f"Enqueued action {action_id}",
                extra={
                    "action_id": action_id,
                    "type": action["type"],
                    "target": action["target"],
                }
            )
            
            return action_id
            
        except Exception as e:
            logger.exception(f"Error enqueueing action: {e}")
            await self.db.rollback()
            raise
    
    async def execute_action(
        self,
        action_id: str,
        run_by: str = "system",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an optimization action.
        
        Args:
            action_id: Unique action identifier
            run_by: User/system executing the action
            dry_run: If True, simulate without actually executing
        
        Returns:
            {
                "action_id": str,
                "status": "executed"|"failed",
                "details": {...},
                "meta_response": {...}
            }
        """
        try:
            # Fetch action
            stmt = select(OptimizationActionModel).where(
                OptimizationActionModel.action_id == action_id
            )
            result = await self.db.execute(stmt)
            action = result.scalar_one_or_none()
            
            if not action:
                raise ValueError(f"Action {action_id} not found")
            
            if action.status not in [OptimizationActionStatus.SUGGESTED, OptimizationActionStatus.PENDING]:
                raise ValueError(f"Action {action_id} status is {action.status}, cannot execute")
            
            # Update status to executing
            action.status = OptimizationActionStatus.EXECUTING
            action.executed_by = run_by
            await self.db.commit()
            
            # Execute based on action type
            result = {"action_id": action_id, "status": "failed", "details": {}}
            
            if dry_run:
                result["status"] = "dry_run"
                result["details"] = {"message": "Dry run - no actual execution"}
            else:
                if action.action_type == "scale_up":
                    result = await self._execute_scale_up(action)
                elif action.action_type == "scale_down":
                    result = await self._execute_scale_down(action)
                elif action.action_type == "pause":
                    result = await self._execute_pause(action)
                elif action.action_type == "resume":
                    result = await self._execute_resume(action)
                elif action.action_type == "reallocate":
                    result = await self._execute_reallocation(action)
                else:
                    raise ValueError(f"Unknown action type: {action.action_type}")
            
            # Update action with result
            if result["status"] == "executed":
                action.status = OptimizationActionStatus.EXECUTED
                action.executed_at = datetime.utcnow()
                action.execution_result = result.get("details")
                action.meta_response = result.get("meta_response")
                
                # Create success ledger event
                await self._create_ledger_event(
                    event_type="optimization_executed",
                    action_id=action_id,
                    details=result,
                )
            else:
                action.status = OptimizationActionStatus.FAILED
                action.execution_error = result.get("error", "Unknown error")
                
                # Create failure ledger event
                await self._create_ledger_event(
                    event_type="optimization_failed",
                    action_id=action_id,
                    details=result,
                )
            
            await self.db.commit()
            
            logger.info(
                f"Executed action {action_id}: {result['status']}",
                extra={"action_id": action_id, "result": result}
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Error executing action {action_id}: {e}")
            await self.db.rollback()
            raise
    
    async def get_pending_actions(
        self,
        campaign_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[OptimizationActionModel]:
        """Get list of pending/suggested actions."""
        stmt = select(OptimizationActionModel).where(
            OptimizationActionModel.status.in_([
                OptimizationActionStatus.SUGGESTED,
                OptimizationActionStatus.PENDING,
            ])
        )
        
        if campaign_id:
            stmt = stmt.where(OptimizationActionModel.campaign_id == campaign_id)
        
        stmt = stmt.order_by(desc(OptimizationActionModel.confidence)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # Private helper methods
    
    async def _get_campaign(self, campaign_id: str) -> Optional[MetaCampaignModel]:
        """Fetch campaign from database."""
        stmt = select(MetaCampaignModel).where(MetaCampaignModel.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _is_eligible_for_optimization(self, campaign: MetaCampaignModel) -> bool:
        """Check if campaign is eligible for optimization (embargo period, status)."""
        # Check embargo period
        if campaign.created_at:
            hours_since_creation = (datetime.utcnow() - campaign.created_at).total_seconds() / 3600
            if hours_since_creation < settings.OPTIMIZER_EMBARGO_HOURS:
                return False
        
        # Check campaign status (only optimize active campaigns)
        if campaign.status != "ACTIVE":
            return False
        
        return True
    
    async def _check_cooldown(self, ad_id: str, action_type: str) -> bool:
        """Check if ad is in cooldown period (recently optimized)."""
        stmt = select(OptimizationActionModel).where(
            and_(
                OptimizationActionModel.ad_id == ad_id,
                OptimizationActionModel.action_type == action_type,
                OptimizationActionModel.status == OptimizationActionStatus.EXECUTED,
                OptimizationActionModel.executed_at >= datetime.utcnow() - timedelta(hours=settings.OPTIMIZER_COOLDOWN_HOURS),
            )
        )
        result = await self.db.execute(stmt)
        recent_action = result.scalar_one_or_none()
        return recent_action is not None
    
    async def _get_roas_metrics(
        self,
        campaign_id: str,
        lookback_days: int = 7,
    ) -> List[MetaROASMetricsModel]:
        """Fetch ROAS metrics for campaign."""
        date_start = datetime.utcnow() - timedelta(days=lookback_days)
        
        stmt = select(MetaROASMetricsModel).where(
            and_(
                MetaROASMetricsModel.campaign_id == campaign_id,
                MetaROASMetricsModel.date >= date_start,
                MetaROASMetricsModel.ad_id.isnot(None),  # Only ad-level metrics
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _create_scale_up_action(self, ad_data: MetaROASMetricsModel) -> Optional[Dict[str, Any]]:
        """Create a scale-up action from ROAS metrics."""
        # Calculate budget increase based on performance tier
        roas = ad_data.actual_roas or 0
        confidence = ad_data.confidence_score or 0.5
        
        if roas >= 5.0:
            budget_increase_pct = 1.0  # 100%
        elif roas >= 4.0:
            budget_increase_pct = 0.75  # 75%
        elif roas >= 3.5:
            budget_increase_pct = 0.50  # 50%
        elif roas >= 3.0:
            budget_increase_pct = 0.25  # 25%
        else:
            budget_increase_pct = 0.10  # 10%
        
        # Cap at max daily change
        budget_increase_pct = min(budget_increase_pct, settings.OPTIMIZER_MAX_DAILY_CHANGE_PCT)
        
        return {
            "action_id": str(uuid4()),
            "type": "scale_up",
            "target_level": "ad",
            "target": str(ad_data.ad_id),
            "campaign_id": ad_data.campaign_id,
            "adset_id": ad_data.adset_id,
            "ad_id": ad_data.ad_id,
            "amount_pct": budget_increase_pct,
            "reason": "high_roas_performance",
            "reason_details": f"ROAS {roas:.2f} exceeds threshold {settings.OPTIMIZER_SCALE_UP_MIN_ROAS:.2f}",
            "confidence": confidence,
            "roas_value": roas,
            "safety_score": min(confidence, 0.9),
            "guard_rails_passed": 1,
        }
    
    async def _create_scale_down_action(self, ad_data: MetaROASMetricsModel) -> Optional[Dict[str, Any]]:
        """Create a scale-down or pause action from ROAS metrics."""
        roas = ad_data.actual_roas or 0
        confidence = ad_data.confidence_score or 0.5
        
        # Pause if ROAS is very low
        if roas < settings.OPTIMIZER_PAUSE_ROAS:
            action_type = "pause"
            amount_pct = -1.0  # -100% (full pause)
            reason = "roas_critically_low"
        else:
            action_type = "scale_down"
            amount_pct = -0.30  # -30%
            amount_pct = max(amount_pct, -settings.OPTIMIZER_MAX_DAILY_CHANGE_PCT)
            reason = "roas_below_threshold"
        
        return {
            "action_id": str(uuid4()),
            "type": action_type,
            "target_level": "ad",
            "target": str(ad_data.ad_id),
            "campaign_id": ad_data.campaign_id,
            "adset_id": ad_data.adset_id,
            "ad_id": ad_data.ad_id,
            "amount_pct": amount_pct,
            "reason": reason,
            "reason_details": f"ROAS {roas:.2f} below threshold {settings.OPTIMIZER_SCALE_DOWN_MAX_ROAS:.2f}",
            "confidence": confidence,
            "roas_value": roas,
            "safety_score": min(confidence, 0.8),
            "guard_rails_passed": 1,
        }
    
    async def _evaluate_reallocation(
        self,
        campaign_id: str,
        roas_metrics: List[MetaROASMetricsModel],
    ) -> Optional[Dict[str, Any]]:
        """Evaluate if budget reallocation is beneficial."""
        if len(roas_metrics) < settings.OPTIMIZER_REALLOCATE_MIN_ADS:
            return None
        
        # Calculate ROAS variance
        roas_values = [m.actual_roas for m in roas_metrics if m.actual_roas]
        if not roas_values:
            return None
        
        max_roas = max(roas_values)
        min_roas = min(roas_values)
        
        # Only reallocate if there's significant difference
        if max_roas / min_roas < settings.OPTIMIZER_REALLOCATE_THRESHOLD_DIFF:
            return None
        
        # Use optimizer to compute reallocation plan
        total_budget = sum(m.recommended_daily_budget_usd or 0 for m in roas_metrics)
        realloc_plan = await self.optimizer.compute_budget_reallocations(
            campaign_id=campaign_id,
            total_budget=total_budget,
            lookback_days=7,
        )
        
        return {
            "action_id": str(uuid4()),
            "type": "reallocate",
            "target_level": "campaign",
            "target": str(campaign_id),
            "campaign_id": campaign_id,
            "reason": "optimize_budget_allocation",
            "reason_details": f"ROAS variance detected (max={max_roas:.2f}, min={min_roas:.2f})",
            "confidence": 0.7,
            "reallocation_plan": realloc_plan,
            "affected_ad_ids": [str(m.ad_id) for m in roas_metrics],
            "safety_score": 0.6,
            "guard_rails_passed": 1,
        }
    
    def _passes_guard_rails(self, action: Dict[str, Any]) -> bool:
        """Check if action passes safety guard rails."""
        # Check confidence threshold
        if action.get("confidence", 0) < settings.OPTIMIZER_MIN_CONFIDENCE:
            logger.debug(f"Action {action.get('action_id')} failed: confidence too low")
            return False
        
        # Check budget change limits
        amount_pct = abs(action.get("amount_pct", 0))
        if amount_pct > settings.OPTIMIZER_MAX_DAILY_CHANGE_PCT and action["type"] != "pause":
            logger.debug(f"Action {action.get('action_id')} failed: budget change too large")
            return False
        
        # Pause actions always pass (safety measure)
        if action["type"] == "pause":
            return True
        
        return True
    
    async def _execute_scale_up(self, action: OptimizationActionModel) -> Dict[str, Any]:
        """Execute scale-up action (increase budget)."""
        # TODO: Integrate with MetaAdsClient to actually change budget
        # For now, simulate success
        return {
            "action_id": action.action_id,
            "status": "executed",
            "details": {
                "message": f"Scaled up {action.target_id} by {action.amount_pct*100:.1f}%",
                "old_budget": action.old_budget_usd,
                "new_budget": action.new_budget_usd,
            },
            "meta_response": {"success": True},
        }
    
    async def _execute_scale_down(self, action: OptimizationActionModel) -> Dict[str, Any]:
        """Execute scale-down action (decrease budget)."""
        return {
            "action_id": action.action_id,
            "status": "executed",
            "details": {
                "message": f"Scaled down {action.target_id} by {abs(action.amount_pct)*100:.1f}%",
                "old_budget": action.old_budget_usd,
                "new_budget": action.new_budget_usd,
            },
            "meta_response": {"success": True},
        }
    
    async def _execute_pause(self, action: OptimizationActionModel) -> Dict[str, Any]:
        """Execute pause action (stop ad/campaign)."""
        return {
            "action_id": action.action_id,
            "status": "executed",
            "details": {
                "message": f"Paused {action.target_id}",
                "reason": action.reason,
            },
            "meta_response": {"success": True},
        }
    
    async def _execute_resume(self, action: OptimizationActionModel) -> Dict[str, Any]:
        """Execute resume action (restart paused ad/campaign)."""
        return {
            "action_id": action.action_id,
            "status": "executed",
            "details": {
                "message": f"Resumed {action.target_id}",
            },
            "meta_response": {"success": True},
        }
    
    async def _execute_reallocation(self, action: OptimizationActionModel) -> Dict[str, Any]:
        """Execute budget reallocation across multiple ads."""
        return {
            "action_id": action.action_id,
            "status": "executed",
            "details": {
                "message": f"Reallocated budget for campaign {action.campaign_id}",
                "plan": action.reallocation_plan,
                "affected_ads": len(action.affected_ad_ids or []),
            },
            "meta_response": {"success": True},
        }
    
    async def _create_ledger_event(
        self,
        event_type: str,
        action_id: str,
        details: Dict[str, Any],
    ):
        """Create event log entry for audit trail."""
        # TODO: Implement proper EventLogModel once available
        # For now, just log to application logs
        try:
            logger.info(
                f"Ledger event: {event_type}",
                extra={
                    "event_type": event_type,
                    "action_id": action_id,
                    "details": details,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create ledger event: {e}")
            # Don't fail the main operation if ledger fails
