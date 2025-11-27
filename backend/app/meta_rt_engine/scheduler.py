"""
Background Scheduler for Meta RT Performance Engine (PASO 10.14)

Runs real-time performance monitoring every 5 minutes.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.database import AsyncSessionLocal
from app.meta_rt_engine.detector import RealTimeDetector
from app.meta_rt_engine.decision_engine import RealTimeDecisionEngine
from app.meta_rt_engine.actions import RealTimeActionsLayer
from app.meta_rt_engine.schemas import PerformanceSnapshot, PerformanceMetrics
import uuid

logger = logging.getLogger(__name__)

# Global task reference
rt_engine_task: Optional[asyncio.Task] = None


async def rt_engine_background_task(
    interval_minutes: int = 5,
    mode: str = "stub",
    auto_apply_actions: bool = False,
):
    """
    Background task that runs RT engine every N minutes.
    
    Args:
        interval_minutes: Interval between runs (default 5 minutes)
        mode: "stub" or "live"
        auto_apply_actions: Whether to automatically apply actions
    """
    logger.info(f"RT Engine background task started (interval={interval_minutes}min, mode={mode}, auto_apply={auto_apply_actions})")
    
    detector = RealTimeDetector(mode=mode)
    decision_engine = RealTimeDecisionEngine(mode=mode)
    actions_layer = RealTimeActionsLayer(mode=mode)
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # TODO: Get active campaigns from DB
                # For now, use synthetic campaign IDs
                campaign_ids = [uuid.uuid4() for _ in range(3)]
                
                for campaign_id in campaign_ids:
                    # Create performance snapshot
                    snapshot = PerformanceSnapshot(
                        campaign_id=campaign_id,
                        ad_account_id="act_123456789",
                        timestamp=datetime.utcnow(),
                        window_minutes=interval_minutes,
                        metrics=PerformanceMetrics(
                            impressions=1000,
                            clicks=30,
                            conversions=5,
                            spend=50.0,
                            ctr=0.03,
                            cvr=0.167,
                            cpm=50.0,
                            cpc=1.67,
                            cpa=10.0,
                            roas=3.0,
                            frequency=2.5,
                            reach=400,
                        ),
                    )
                    
                    # Detect anomalies
                    detection_result = await detector.detect_anomalies(
                        campaign_id=campaign_id,
                        current_snapshot=snapshot,
                    )
                    
                    # Make decisions if anomalies detected
                    if detection_result.anomalies:
                        decision = await decision_engine.make_decision(detection_result)
                        
                        # Execute actions if configured
                        if auto_apply_actions and decision.should_auto_apply:
                            action_response = await actions_layer.execute_actions(
                                decision=decision,
                                auto_apply=True,
                            )
                            logger.info(f"Actions executed for campaign {campaign_id}: {action_response.successful_actions}/{action_response.total_actions} successful")
                
                logger.info(f"RT Engine run completed for {len(campaign_ids)} campaigns")
            
            # Wait for next interval
            await asyncio.sleep(interval_minutes * 60)
            
        except asyncio.CancelledError:
            logger.info("RT Engine background task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in RT Engine background task: {e}")
            # Wait 5 minutes before retry on error
            await asyncio.sleep(300)


async def start_rt_engine_scheduler(
    interval_minutes: int = 5,
    mode: str = "stub",
    auto_apply_actions: bool = False,
) -> asyncio.Task:
    """
    Start the RT Engine background scheduler.
    
    Returns:
        asyncio.Task reference
    """
    global rt_engine_task
    
    rt_engine_task = asyncio.create_task(
        rt_engine_background_task(
            interval_minutes=interval_minutes,
            mode=mode,
            auto_apply_actions=auto_apply_actions,
        )
    )
    
    logger.info("RT Engine scheduler started")
    return rt_engine_task


async def stop_rt_engine_scheduler(task: Optional[asyncio.Task] = None):
    """
    Stop the RT Engine background scheduler.
    
    Args:
        task: Task reference (uses global if not provided)
    """
    global rt_engine_task
    
    task_to_stop = task or rt_engine_task
    
    if task_to_stop and not task_to_stop.done():
        task_to_stop.cancel()
        try:
            await task_to_stop
        except asyncio.CancelledError:
            logger.info("RT Engine scheduler stopped gracefully")
    
    rt_engine_task = None
