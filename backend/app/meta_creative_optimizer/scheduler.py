"""Scheduler for Creative Optimizer (PASO 10.16)"""
import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from app.meta_creative_optimizer.data_collector import UnifiedDataCollector
from app.meta_creative_optimizer.winner_selector import WinnerSelector
from app.meta_creative_optimizer.decision_engine import CreativeDecisionEngine

logger = logging.getLogger(__name__)


async def creative_optimizer_background_task(
    interval_hours: int = 24,
    mode: str = "stub"
):
    """Background task that runs optimization every interval_hours"""
    while True:
        try:
            logger.info(f"Starting creative optimization cycle (mode={mode})")
            start_time = datetime.utcnow()
            
            # Collect data
            collector = UnifiedDataCollector(mode=mode)
            creatives = await collector.collect_all_creatives()
            
            # Select winner
            selector = WinnerSelector(mode=mode)
            winner = await selector.select_winner(creatives)
            
            # Make decisions
            engine = CreativeDecisionEngine(mode=mode)
            decisions = await engine.make_decisions(creatives, winner)
            
            # TODO: Persist to DB
            # TODO: Execute orchestrations
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Optimization complete: {len(creatives)} creatives, "
                f"{len(decisions)} decisions, {duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error in optimization cycle: {e}")
            await asyncio.sleep(300)  # 5 min retry
            continue
        
        await asyncio.sleep(interval_hours * 3600)


async def start_creative_optimizer_scheduler(
    interval_hours: int = 24,
    mode: str = "stub"
) -> asyncio.Task:
    """Start scheduler background task"""
    task = asyncio.create_task(
        creative_optimizer_background_task(interval_hours, mode)
    )
    logger.info(f"Creative Optimizer scheduler started (interval={interval_hours}h, mode={mode})")
    return task


async def stop_creative_optimizer_scheduler(task: asyncio.Task):
    """Stop scheduler gracefully"""
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Creative Optimizer scheduler stopped")
