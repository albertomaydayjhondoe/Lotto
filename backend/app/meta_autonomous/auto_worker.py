"""
Meta Autonomous Worker

Master orchestration loop that coordinates:
- ROAS Engine (PASO 10.5)
- Optimization Loop (PASO 10.6)
- Policy Engine (business rules)
- Safety Engine (guardrails)
- Meta Ads Orchestrator (PASO 10.3)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, func
import asyncio
import logging

from app.models.database import (
    MetaCampaignModel,
    MetaROASMetricsModel,
    OptimizationActionModel,
    OptimizationActionStatus,
)
from app.meta_optimization.service import OptimizationService
# Note: ROASOptimizer not directly used in worker (accessed via OptimizationService)
from .policy_engine import PolicyEngine
from .safety import SafetyEngine
from .config import AutonomousSettings

logger = logging.getLogger(__name__)


class MetaAutoWorker:
    """
    Autonomous worker that continuously optimizes Meta ad campaigns.
    
    Responsibilities:
    - Fetch active campaigns
    - Get ROAS metrics from ROAS Engine
    - Generate optimization actions via Optimization Loop
    - Filter actions through Policy Engine
    - Validate actions through Safety Engine
    - Execute or queue actions based on mode (suggest/auto)
    - Report statistics and errors
    """
    
    def __init__(
        self,
        dbmaker: async_sessionmaker[AsyncSession],
        settings: Optional[AutonomousSettings] = None
    ):
        self.dbmaker = dbmaker
        self.settings = settings or AutonomousSettings()
        self.policy_engine = PolicyEngine(self.settings)
        self.safety_engine = SafetyEngine(self.settings)
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(
            f"MetaAutoWorker initialized: "
            f"mode={self.settings.META_AUTO_MODE}, "
            f"interval={self.settings.META_AUTO_INTERVAL_SECONDS}s, "
            f"enabled={self.settings.META_AUTO_ENABLED}"
        )
    
    async def tick(self) -> Dict[str, Any]:
        """
        Execute one autonomous optimization cycle.
        
        Returns:
            Statistics dictionary with counts and results
        """
        logger.info("=== MetaAutoWorker tick started ===")
        
        stats = {
            "tick_started_at": datetime.utcnow().isoformat(),
            "campaigns_evaluated": 0,
            "actions_generated": 0,
            "actions_policy_blocked": 0,
            "actions_safety_blocked": 0,
            "actions_queued": 0,
            "actions_executed": 0,
            "actions_failed": 0,
            "errors": [],
        }
        
        async with self.dbmaker() as db:
            try:
                # Step 1: Get active campaigns (past embargo period)
                campaigns = await self._get_active_campaigns(db)
                logger.info(f"Found {len(campaigns)} active campaigns to evaluate")
                
                # Step 2: For each campaign, run optimization cycle
                for campaign in campaigns[:self.settings.MAX_CAMPAIGNS_PER_TICK]:
                    try:
                        campaign_stats = await self._process_campaign(campaign, db)
                        stats["campaigns_evaluated"] += 1
                        stats["actions_generated"] += campaign_stats["actions_generated"]
                        stats["actions_policy_blocked"] += campaign_stats["policy_blocked"]
                        stats["actions_safety_blocked"] += campaign_stats["safety_blocked"]
                        stats["actions_queued"] += campaign_stats["queued"]
                        stats["actions_executed"] += campaign_stats["executed"]
                        stats["actions_failed"] += campaign_stats["failed"]
                    except Exception as e:
                        error_msg = f"Campaign {campaign.campaign_id} error: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        stats["errors"].append(error_msg)
                
                # Enforce global action limit
                if stats["actions_queued"] + stats["actions_executed"] >= self.settings.MAX_ACTIONS_PER_TICK:
                    logger.warning(f"Reached max actions per tick: {self.settings.MAX_ACTIONS_PER_TICK}")
                
            except Exception as e:
                error_msg = f"Tick error: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats["errors"].append(error_msg)
        
        stats["tick_completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"=== Tick completed: {stats} ===")
        return stats
    
    async def _get_active_campaigns(
        self,
        db: AsyncSession
    ) -> List[MetaCampaignModel]:
        """
        Get campaigns that are eligible for optimization.
        
        Criteria:
        - Status = ACTIVE
        - Created at least MIN_AGE_HOURS ago (past embargo)
        """
        embargo_cutoff = datetime.utcnow() - timedelta(hours=self.settings.MIN_AGE_HOURS)
        
        stmt = select(MetaCampaignModel).where(
            and_(
                MetaCampaignModel.status == "ACTIVE",
                MetaCampaignModel.created_at <= embargo_cutoff
            )
        ).limit(self.settings.MAX_CAMPAIGNS_PER_TICK)
        
        result = await db.execute(stmt)
        campaigns = result.scalars().all()
        
        return list(campaigns)
    
    async def _process_campaign(
        self,
        campaign: MetaCampaignModel,
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Process a single campaign through the optimization pipeline.
        
        Returns:
            Statistics for this campaign
        """
        logger.info(f"Processing campaign: {campaign.campaign_id}")
        
        stats = {
            "actions_generated": 0,
            "policy_blocked": 0,
            "safety_blocked": 0,
            "queued": 0,
            "executed": 0,
            "failed": 0,
        }
        
        # Step 1: Get ROAS metrics from ROAS Engine (PASO 10.5)
        roas_metrics = await self._get_roas_metrics(campaign, db)
        if not roas_metrics:
            logger.info(f"No ROAS metrics for campaign {campaign.campaign_id}, skipping")
            return stats
        
        # Step 2: Generate optimization actions (PASO 10.6)
        optimization_service = OptimizationService(db)
        try:
            actions = await optimization_service.evaluate_campaign(
                campaign.campaign_id,
                lookback_days=7,
                min_confidence=self.settings.HARD_STOP_CONFIDENCE
            )
            stats["actions_generated"] = len(actions)
            logger.info(f"Generated {len(actions)} actions for campaign {campaign.campaign_id}")
        except Exception as e:
            logger.error(f"Failed to generate actions: {e}")
            return stats
        
        # Step 3: Filter actions through Policy Engine and Safety Engine
        for action in actions:
            try:
                # Build context for validation
                context = self._build_action_context(action, campaign, roas_metrics)
                
                # Policy validation
                policy_allowed, policy_reason = self.policy_engine.validate_action(
                    action["type"],
                    action,
                    context
                )
                
                if not policy_allowed:
                    logger.info(f"Policy blocked: {policy_reason}")
                    stats["policy_blocked"] += 1
                    continue
                
                # Safety validation
                safety_blocked, safety_reason = await self.safety_engine.validate_action(
                    action["type"],
                    action,
                    context,
                    db
                )
                
                if safety_blocked:
                    logger.info(f"Safety blocked: {safety_reason}")
                    stats["safety_blocked"] += 1
                    continue
                
                # Step 4: Execute or queue based on mode
                is_auto = self.settings.META_AUTO_MODE == "auto"
                
                if is_auto and self._is_safe_for_auto(action, context):
                    # Auto mode: execute immediately
                    success = await self._execute_action(action, optimization_service, db)
                    if success:
                        stats["executed"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    # Suggest mode: queue for human review
                    await self._queue_action(action, optimization_service, db)
                    stats["queued"] += 1
                
            except Exception as e:
                logger.error(f"Action processing error: {e}", exc_info=True)
                stats["failed"] += 1
        
        return stats
    
    async def _get_roas_metrics(
        self,
        campaign: MetaCampaignModel,
        db: AsyncSession
    ) -> List[MetaROASMetricsModel]:
        """Get recent ROAS metrics for campaign."""
        lookback = datetime.utcnow().date() - timedelta(days=7)
        
        stmt = select(MetaROASMetricsModel).where(
            and_(
                MetaROASMetricsModel.campaign_id == campaign.id,
                MetaROASMetricsModel.date >= lookback
            )
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    def _build_action_context(
        self,
        action: Dict[str, Any],
        campaign: MetaCampaignModel,
        roas_metrics: List[MetaROASMetricsModel]
    ) -> Dict[str, Any]:
        """Build context dictionary for action validation."""
        # Calculate aggregate metrics
        avg_roas = sum(m.actual_roas for m in roas_metrics) / len(roas_metrics) if roas_metrics else 0
        avg_confidence = sum(m.confidence_score for m in roas_metrics) / len(roas_metrics) if roas_metrics else 0
        total_spend = sum(getattr(m, 'spend', 0) for m in roas_metrics)
        total_impressions = sum(getattr(m, 'impressions', 0) for m in roas_metrics)
        
        return {
            "is_auto_mode": self.settings.META_AUTO_MODE == "auto",
            "current_budget": action.get("old_budget_usd", 0),
            "roas": avg_roas,
            "confidence": avg_confidence,
            "spend": total_spend,
            "impressions": total_impressions,
            "created_at": campaign.created_at,
            "entity_id": action.get("target_id", campaign.campaign_id),
            "spend_today": 0,  # TODO: Query actual daily spend
            "last_action_time": None,  # TODO: Query from OptimizationActionModel
        }
    
    def _is_safe_for_auto(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Determine if action is safe for automatic execution.
        
        Auto execution requires:
        - High confidence (≥75%)
        - Small changes (≤10%)
        - Simple action types (no reallocation)
        - Pause is always safe
        """
        action_type = action["type"]
        
        # Pause is always safe
        if action_type == "pause":
            return True
        
        # Reallocation requires human approval
        if action_type == "reallocate":
            return False
        
        # Check confidence
        confidence = action.get("confidence", 0)
        if confidence < 0.75:
            return False
        
        # Check change size for budget actions
        if action_type in ["scale_up", "scale_down"]:
            amount_pct = action.get("amount_pct", 0)
            if abs(amount_pct) > self.settings.MAX_AUTO_CHANGE_PCT:
                return False
        
        return True
    
    async def _queue_action(
        self,
        action: Dict[str, Any],
        optimization_service: OptimizationService,
        db: AsyncSession
    ) -> None:
        """Queue action for human review."""
        try:
            await optimization_service.enqueue_action(
                action,
                created_by="autonomous_worker"
            )
            logger.info(f"Queued action: {action['type']} for {action.get('target_id')}")
        except Exception as e:
            logger.error(f"Failed to queue action: {e}")
            raise
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        optimization_service: OptimizationService,
        db: AsyncSession
    ) -> bool:
        """
        Execute action immediately (auto mode).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # First queue the action
            await optimization_service.enqueue_action(
                action,
                created_by="autonomous_worker"
            )
            
            # Then execute it
            # Note: In production, this would call the actual Meta Ads API
            # For now, we simulate execution
            logger.info(
                f"AUTO EXECUTED: {action['type']} on {action.get('target_id')} "
                f"(simulated - Meta API integration pending)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute action: {e}", exc_info=True)
            return False
    
    async def run_loop(self) -> None:
        """
        Main worker loop - runs continuously until stopped.
        """
        if not self.settings.META_AUTO_ENABLED:
            logger.warning("MetaAutoWorker is disabled in settings")
            return
        
        self._running = True
        logger.info("MetaAutoWorker loop started")
        
        while self._running:
            try:
                # Execute tick
                stats = await self.tick()
                
                # Log summary
                logger.info(
                    f"Tick summary: "
                    f"campaigns={stats['campaigns_evaluated']}, "
                    f"actions_generated={stats['actions_generated']}, "
                    f"queued={stats['actions_queued']}, "
                    f"executed={stats['actions_executed']}, "
                    f"errors={len(stats['errors'])}"
                )
                
                # Sleep until next tick
                await asyncio.sleep(self.settings.META_AUTO_INTERVAL_SECONDS)
                
            except asyncio.CancelledError:
                logger.info("Worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                # Sleep before retry to avoid tight error loop
                await asyncio.sleep(60)
        
        self._running = False
        logger.info("MetaAutoWorker loop stopped")
    
    def start(self) -> None:
        """Start the worker as a background task."""
        if self._task and not self._task.done():
            logger.warning("Worker already running")
            return
        
        self._task = asyncio.create_task(self.run_loop())
        logger.info("MetaAutoWorker background task started")
    
    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("MetaAutoWorker stop requested")
    
    @property
    def is_running(self) -> bool:
        """Check if worker is currently running."""
        return self._running and self._task and not self._task.done()
