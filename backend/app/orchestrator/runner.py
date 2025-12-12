"""
Orchestrator Runner - Autonomous Execution Loop
Runs the orchestrator in an infinite loop
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.orchestrator.monitor import monitor_system_state
from app.orchestrator.decider import decide_actions, summarize_decisions
from app.orchestrator.executor import execute_actions
from app.ledger import log_event
from app.core.config import settings

logger = logging.getLogger(__name__)


_orchestrator_task: Optional[asyncio.Task] = None
_orchestrator_running = False


async def run_orchestrator_loop():
    """
    Main orchestrator loop - runs continuously
    Cycle: Monitor → Decide → Execute → Sleep → Repeat
    """
    global _orchestrator_running
    
    if not settings.ORCHESTRATOR_ENABLED:
        logger.warning("Orchestrator is disabled in config")
        return
    
    _orchestrator_running = True
    cycle_count = 0
    
    logger.info(f"Orchestrator started - running every {settings.ORCHESTRATOR_INTERVAL_SECONDS}s")
    
    while _orchestrator_running:
        cycle_count += 1
        cycle_start = datetime.utcnow()
        
        try:
            # Get database session
            async with AsyncSessionLocal() as db:
                # Step 1: Monitor system state
                snapshot = await monitor_system_state(db)
                
                # Step 2: Decide actions
                actions = decide_actions(snapshot)
                decision_summary = summarize_decisions(actions)
                
                # Log monitoring cycle
                await log_event(
                    db=db,
                    event_type="orchestrator.cycle_started",
                    entity_type="orchestrator",
                    entity_id="orchestrator",
                    metadata={
                        "cycle": cycle_count,
                        "snapshot": {
                            "jobs_pending": snapshot["jobs"]["pending"],
                            "publish_logs_pending": snapshot["publish_logs"]["pending"],
                            "health_score": snapshot["system"]["health_score"],
                            "health_status": snapshot["system"]["health_status"]
                        },
                        "decision": decision_summary
                    }
                )
                
                # Step 3: Execute actions (if any)
                if actions:
                    logger.info(f"Cycle {cycle_count}: {len(actions)} actions to execute")
                    execution_result = await execute_actions(actions, db)
                    
                    await log_event(
                        db=db,
                        event_type="orchestrator.cycle_completed",
                        entity_type="orchestrator",
                        entity_id="orchestrator",
                        metadata={
                            "cycle": cycle_count,
                            "execution": execution_result,
                            "duration_seconds": (datetime.utcnow() - cycle_start).total_seconds()
                        }
                    )
                    
                    logger.info(f"Cycle {cycle_count}: {execution_result['success_count']} succeeded, {execution_result['error_count']} failed")
                else:
                    logger.debug(f"Cycle {cycle_count}: No actions needed, system healthy")
                    
                    await log_event(
                        db=db,
                        event_type="orchestrator.cycle_idle",
                        entity_type="orchestrator",
                        entity_id="orchestrator",
                        metadata={
                            "cycle": cycle_count,
                            "health_score": snapshot["system"]["health_score"],
                            "duration_seconds": (datetime.utcnow() - cycle_start).total_seconds()
                        }
                    )
        
        except Exception as e:
            logger.error(f"Orchestrator cycle {cycle_count} error: {e}")
            
            # Log error
            try:
                async with AsyncSessionLocal() as db:
                    await log_event(
                        db=db,
                        event_type="orchestrator.cycle_error",
                        entity_type="orchestrator",
                        entity_id="orchestrator",
                        metadata={
                            "cycle": cycle_count,
                            "error": str(e),
                            "duration_seconds": (datetime.utcnow() - cycle_start).total_seconds()
                        },
                        is_error=True
                    )
            except:
                pass  # Don't fail if logging fails
        
        # Sleep before next cycle
        await asyncio.sleep(settings.ORCHESTRATOR_INTERVAL_SECONDS)
    
    print("🛑 Orchestrator stopped")


async def start_orchestrator():
    """Start the orchestrator in a background task"""
    global _orchestrator_task, _orchestrator_running
    
    if _orchestrator_task and not _orchestrator_task.done():
        print("⚠️ Orchestrator is already running")
        return {"status": "already_running"}
    
    _orchestrator_running = True
    _orchestrator_task = asyncio.create_task(run_orchestrator_loop())
    
    return {
        "status": "started",
        "interval_seconds": settings.ORCHESTRATOR_INTERVAL_SECONDS,
        "enabled": settings.ORCHESTRATOR_ENABLED
    }


async def stop_orchestrator():
    """Stop the orchestrator gracefully"""
    global _orchestrator_running, _orchestrator_task
    
    if not _orchestrator_task or _orchestrator_task.done():
        return {"status": "not_running"}
    
    _orchestrator_running = False
    
    # Wait for current cycle to finish (max 10 seconds)
    try:
        await asyncio.wait_for(_orchestrator_task, timeout=10.0)
    except asyncio.TimeoutError:
        _orchestrator_task.cancel()
    
    return {"status": "stopped"}


def is_orchestrator_running() -> bool:
    """Check if orchestrator is currently running"""
    global _orchestrator_task
    return _orchestrator_task is not None and not _orchestrator_task.done()


async def run_orchestrator_once() -> dict:
    """
    Run a single orchestrator cycle manually
    Useful for testing or manual intervention
    """
    
    async with AsyncSessionLocal() as db:
        # Monitor
        snapshot = await monitor_system_state(db)
        
        # Decide
        actions = decide_actions(snapshot)
        decision_summary = summarize_decisions(actions)
        
        # Execute
        if actions:
            execution_result = await execute_actions(actions, db)
        else:
            execution_result = {
                "total_actions": 0,
                "success_count": 0,
                "error_count": 0,
                "results": []
            }
        
        return {
            "snapshot": snapshot,
            "decision": decision_summary,
            "execution": execution_result,
            "timestamp": datetime.utcnow().isoformat()
        }
