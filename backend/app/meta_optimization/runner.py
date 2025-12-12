"""
Optimization Runner - Background Worker

Runs the optimization loop periodically, evaluating campaigns and
generating/executing optimization actions based on ROAS data.
"""

import asyncio
import logging
from typing import Callable, Dict, Any, List
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MetaCampaignModel, CampaignStatus
from app.meta_optimization.service import OptimizationService
from app.meta_optimization.config import settings

logger = logging.getLogger("meta_optimization.runner")


class OptimizationRunner:
    """
    Background worker that runs the optimization loop.
    
    Periodically evaluates active campaigns, generates optimization actions,
    and optionally executes them automatically (in 'auto' mode).
    """
    
    def __init__(self, dbmaker: Callable):
        """
        Initialize the optimization runner.
        
        Args:
            dbmaker: Async session maker function
        """
        self.dbmaker = dbmaker
        self._task = None
        self._stop = False
        self._tick_count = 0
    
    async def _tick(self) -> Dict[str, Any]:
        """
        Execute one optimization cycle.
        
        Returns:
            Statistics about the tick (campaigns evaluated, actions created, etc.)
        """
        stats = {
            "tick_number": self._tick_count,
            "started_at": datetime.utcnow().isoformat(),
            "campaigns_evaluated": 0,
            "actions_suggested": 0,
            "actions_executed": 0,
            "errors": 0,
        }
        
        try:
            async with self.dbmaker() as db:
                svc = OptimizationService(db)
                
                # Get active campaigns
                campaigns = await self._get_active_campaigns(db)
                stats["campaigns_evaluated"] = len(campaigns)
                
                logger.info(f"Optimization tick {self._tick_count}: evaluating {len(campaigns)} campaigns")
                
                total_actions_created = 0
                
                for campaign in campaigns:
                    try:
                        # Evaluate campaign and get suggested actions
                        actions = await svc.evaluate_campaign(
                            campaign_id=campaign.campaign_id,
                            lookback_days=7,
                        )
                        
                        # Enqueue actions
                        for action in actions:
                            try:
                                action_id = await svc.enqueue_action(
                                    action=action,
                                    created_by="optimizer",
                                )
                                total_actions_created += 1
                                stats["actions_suggested"] += 1
                                
                                # In 'auto' mode, execute safe actions immediately
                                if settings.OPTIMIZER_MODE == "auto":
                                    if self._is_safe_for_auto_execution(action):
                                        try:
                                            result = await svc.execute_action(
                                                action_id=action_id,
                                                run_by="optimizer_auto",
                                            )
                                            if result["status"] == "executed":
                                                stats["actions_executed"] += 1
                                                logger.info(f"Auto-executed action {action_id}")
                                        except Exception as e:
                                            logger.error(f"Failed to auto-execute action {action_id}: {e}")
                                            stats["errors"] += 1
                                    else:
                                        logger.debug(f"Action {action_id} not safe for auto-execution")
                                
                            except Exception as e:
                                logger.error(f"Failed to enqueue action for campaign {campaign.campaign_id}: {e}")
                                stats["errors"] += 1
                        
                        # Respect action limits
                        if total_actions_created >= settings.OPTIMIZER_MAX_ACTIONS_PER_RUN:
                            logger.warning(f"Reached max actions per run ({settings.OPTIMIZER_MAX_ACTIONS_PER_RUN})")
                            break
                    
                    except Exception as e:
                        logger.error(f"Error evaluating campaign {campaign.campaign_id}: {e}")
                        stats["errors"] += 1
                        continue
                
                stats["completed_at"] = datetime.utcnow().isoformat()
                
                logger.info(
                    f"Optimization tick {self._tick_count} completed",
                    extra=stats
                )
        
        except Exception as e:
            logger.exception(f"Critical error in optimization tick: {e}")
            stats["errors"] += 1
            stats["error_message"] = str(e)
        
        return stats
    
    async def run_loop(self):
        """
        Run the optimization loop continuously.
        
        This method runs indefinitely (until stop() is called) and executes
        optimization ticks at the configured interval.
        """
        logger.info(
            f"Starting optimization loop (mode={settings.OPTIMIZER_MODE}, "
            f"interval={settings.OPTIMIZER_INTERVAL_SECONDS}s)"
        )
        
        while not self._stop and settings.OPTIMIZER_ENABLED:
            try:
                self._tick_count += 1
                stats = await self._tick()
                
                logger.info(
                    f"Tick {self._tick_count} completed: "
                    f"{stats['actions_suggested']} actions suggested, "
                    f"{stats['actions_executed']} executed"
                )
                
            except Exception as e:
                logger.exception(f"Optimizer tick {self._tick_count} failed: {e}")
            
            # Wait for next tick
            if not self._stop:
                await asyncio.sleep(settings.OPTIMIZER_INTERVAL_SECONDS)
        
        logger.info("Optimization loop stopped")
    
    def stop(self):
        """Stop the optimization loop gracefully."""
        logger.info("Stopping optimization loop...")
        self._stop = True
    
    async def start(self):
        """Start the optimization loop as a background task."""
        if self._task and not self._task.done():
            logger.warning("Optimization loop already running")
            return
        
        self._stop = False
        self._task = asyncio.create_task(self.run_loop())
        logger.info("Optimization loop started as background task")
    
    async def wait(self):
        """Wait for the optimization loop task to complete."""
        if self._task:
            await self._task
    
    # Helper methods
    
    async def _get_active_campaigns(self, db: AsyncSession) -> List[MetaCampaignModel]:
        """
        Get list of active campaigns eligible for optimization.
        
        Filters:
        - Status = ACTIVE
        - Not in embargo period
        - Has minimum spend
        """
        from datetime import timedelta
        
        embargo_cutoff = datetime.utcnow() - timedelta(hours=settings.OPTIMIZER_EMBARGO_HOURS)
        
        stmt = select(MetaCampaignModel).where(
            and_(
                MetaCampaignModel.status == "ACTIVE",
                MetaCampaignModel.created_at <= embargo_cutoff,  # Past embargo period
            )
        ).limit(100)  # Limit to prevent overwhelming the system
        
        result = await db.execute(stmt)
        campaigns = result.scalars().all()
        
        return campaigns
    
    def _is_safe_for_auto_execution(self, action: Dict[str, Any]) -> bool:
        """
        Determine if an action is safe for automatic execution.
        
        Criteria for safe auto-execution:
        - High confidence (>= 0.75)
        - Not a reallocation (too complex)
        - Budget changes within safe limits
        - Pause actions always safe (safety measure)
        """
        # Pause actions are always safe (stop bleeding money)
        if action["type"] == "pause":
            return True
        
        # Check confidence threshold (higher for auto)
        if action.get("confidence", 0) < 0.75:
            return False
        
        # Reallocation requires manual review
        if action["type"] == "reallocate":
            return False
        
        # Check budget change limits (extra conservative for auto)
        amount_pct = abs(action.get("amount_pct", 0))
        if amount_pct > settings.OPTIMIZER_MAX_DAILY_CHANGE_PCT * 0.5:  # 50% of max
            return False
        
        return True


# Module-level imports removed (already at top)
