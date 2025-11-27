"""
Background scheduler for Meta Targeting Optimizer.

Runs optimization every 24 hours automatically.
"""
import asyncio
import logging
from app.core.database import AsyncSessionLocal
from app.meta_targeting_optimizer.optimizer import MetaTargetingOptimizer

logger = logging.getLogger(__name__)

# Global task reference
_targeting_scheduler_task: asyncio.Task = None


async def targeting_optimizer_background_task():
    """
    Background task that runs targeting optimization every 24 hours.
    """
    logger.info("Meta Targeting Optimizer scheduler started")
    
    # Run every 24 hours
    interval_seconds = 24 * 60 * 60
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                logger.info("Running Meta Targeting Optimization...")
                
                optimizer = MetaTargetingOptimizer(db=db, mode="stub")
                result = await optimizer.run_optimization(
                    campaign_id=None,  # All active campaigns
                    force_refresh=True
                )
                
                logger.info(
                    f"Targeting optimization completed: "
                    f"{result['recommendations_count']} recommendations in {result['duration_ms']}ms"
                )
        
        except Exception as e:
            logger.error(f"Error in targeting optimizer background task: {e}", exc_info=True)
        
        # Wait for next interval
        await asyncio.sleep(interval_seconds)


async def start_targeting_optimizer_scheduler() -> asyncio.Task:
    """
    Start the targeting optimizer background scheduler.
    
    Returns:
        asyncio.Task reference for the background task
    """
    global _targeting_scheduler_task
    
    if _targeting_scheduler_task is not None:
        logger.warning("Targeting optimizer scheduler already running")
        return _targeting_scheduler_task
    
    _targeting_scheduler_task = asyncio.create_task(targeting_optimizer_background_task())
    logger.info("Meta Targeting Optimizer scheduler task created")
    
    return _targeting_scheduler_task


async def stop_targeting_optimizer_scheduler(task: asyncio.Task = None):
    """
    Stop the targeting optimizer background scheduler.
    
    Args:
        task: Task reference (optional, will use global if not provided)
    """
    global _targeting_scheduler_task
    
    target_task = task or _targeting_scheduler_task
    
    if target_task is None:
        logger.warning("No targeting optimizer scheduler task to stop")
        return
    
    logger.info("Stopping Meta Targeting Optimizer scheduler...")
    target_task.cancel()
    
    try:
        await target_task
    except asyncio.CancelledError:
        logger.info("Meta Targeting Optimizer scheduler stopped successfully")
    
    _targeting_scheduler_task = None
