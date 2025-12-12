"""
AI Global Worker Autonomous Runner.

Runs AI reasoning loop in background at configured intervals.
Stores latest reasoning output in memory for API access.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_global_worker.collector import collect_system_snapshot
from app.ai_global_worker.reasoning import run_full_reasoning
from app.ai_global_worker.schemas import AIReasoningOutput

logger = logging.getLogger(__name__)

# Global state
_last_reasoning: Optional[AIReasoningOutput] = None
_runner_task: Optional[asyncio.Task] = None
_is_running = False


def get_last_reasoning() -> Optional[AIReasoningOutput]:
    """
    Get the last generated AI reasoning output.
    
    Returns:
        Last AIReasoningOutput or None if no reasoning has run yet
    """
    return _last_reasoning


async def ai_worker_loop(db_factory, interval_seconds: int = 30):
    """
    Main AI worker loop.
    
    Runs continuously, executing AI reasoning at configured intervals.
    
    Args:
        db_factory: Async function that returns database session
        interval_seconds: Seconds between reasoning cycles
    """
    global _last_reasoning, _is_running
    
    logger.info(f"AI Global Worker starting (interval: {interval_seconds}s)")
    _is_running = True
    
    while _is_running:
        try:
            # Get database session
            async for db in db_factory():
                logger.debug("AI Worker: Starting reasoning cycle")
                start_time = datetime.utcnow()
                
                # Collect system snapshot
                snapshot = await collect_system_snapshot(db)
                logger.debug(f"AI Worker: Snapshot collected ({len(snapshot.recent_events)} events)")
                
                # Run full reasoning
                reasoning_output = await run_full_reasoning(snapshot)
                logger.debug(f"AI Worker: Reasoning complete (score: {reasoning_output.summary.health_score:.1f})")
                
                # Store in global state
                _last_reasoning = reasoning_output
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    f"AI Worker cycle complete: "
                    f"health={reasoning_output.summary.overall_health}, "
                    f"recommendations={len(reasoning_output.recommendations)}, "
                    f"time={elapsed:.2f}s"
                )
                
                break  # Exit the async for loop
            
            # Wait for next cycle
            await asyncio.sleep(interval_seconds)
            
        except asyncio.CancelledError:
            logger.info("AI Worker: Received cancellation")
            _is_running = False
            break
        except Exception as e:
            logger.error(f"AI Worker error: {e}", exc_info=True)
            # Continue running despite errors
            await asyncio.sleep(interval_seconds)
    
    logger.info("AI Global Worker stopped")


async def start_ai_worker_loop(db_factory, interval_seconds: int = 30):
    """
    Start the AI worker background loop.
    
    Args:
        db_factory: Async function that returns database session
        interval_seconds: Seconds between reasoning cycles
        
    Returns:
        Asyncio task handle
    """
    global _runner_task
    
    if _runner_task and not _runner_task.done():
        logger.warning("AI Worker already running")
        return _runner_task
    
    _runner_task = asyncio.create_task(
        ai_worker_loop(db_factory, interval_seconds)
    )
    
    return _runner_task


async def stop_ai_worker_loop():
    """
    Stop the AI worker background loop gracefully.
    """
    global _runner_task, _is_running
    
    if not _runner_task:
        logger.warning("AI Worker not running")
        return
    
    logger.info("Stopping AI Worker...")
    _is_running = False
    
    # Cancel the task
    _runner_task.cancel()
    
    try:
        await _runner_task
    except asyncio.CancelledError:
        logger.info("AI Worker task cancelled successfully")
    
    _runner_task = None
