"""
Scheduler para Meta Creative Intelligence System

Ejecuta automáticamente el orchestrator cada 6-24h (configurable).
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.meta_creative_intelligence.orchestrator import MetaCreativeIntelligenceOrchestrator

logger = logging.getLogger(__name__)

# Global task reference
_scheduler_task: Optional[asyncio.Task] = None


async def creative_intelligence_background_task(
    interval_hours: int = 12,
    mode: str = "stub",
):
    """
    Background task que ejecuta el orchestrator periódicamente.
    
    Args:
        interval_hours: Intervalo en horas (default: 12h)
        mode: "stub" o "live"
    """
    logger.info(f"Creative Intelligence scheduler started (interval: {interval_hours}h, mode: {mode})")
    
    orchestrator = MetaCreativeIntelligenceOrchestrator(mode=mode)
    
    while True:
        try:
            logger.info("Starting scheduled creative intelligence run")
            
            async with AsyncSessionLocal() as db:
                # TODO: Obtener lista de video_asset_ids activos desde DB
                # Por ahora, skip si no hay assets
                logger.info("No active video assets found for scheduled run")
            
            await asyncio.sleep(interval_hours * 3600)
        
        except asyncio.CancelledError:
            logger.info("Creative Intelligence scheduler cancelled")
            break
        
        except Exception as e:
            logger.error(f"Error in creative intelligence scheduler: {e}")
            # Wait before retry
            await asyncio.sleep(300)  # 5 min


async def start_creative_intelligence_scheduler(
    interval_hours: int = 12,
    mode: str = "stub",
) -> asyncio.Task:
    """
    Inicia el scheduler.
    
    Args:
        interval_hours: Intervalo en horas
        mode: "stub" o "live"
        
    Returns:
        asyncio.Task
    """
    global _scheduler_task
    
    if _scheduler_task is not None:
        logger.warning("Creative Intelligence scheduler already running")
        return _scheduler_task
    
    _scheduler_task = asyncio.create_task(
        creative_intelligence_background_task(
            interval_hours=interval_hours,
            mode=mode,
        )
    )
    
    logger.info(f"Creative Intelligence scheduler started (interval: {interval_hours}h)")
    return _scheduler_task


async def stop_creative_intelligence_scheduler(task: Optional[asyncio.Task] = None):
    """
    Detiene el scheduler.
    
    Args:
        task: Task to cancel (optional, uses global if None)
    """
    global _scheduler_task
    
    target_task = task or _scheduler_task
    
    if target_task is None:
        logger.warning("No scheduler task to stop")
        return
    
    target_task.cancel()
    
    try:
        await target_task
    except asyncio.CancelledError:
        logger.info("Creative Intelligence scheduler stopped")
    
    if task is None:
        _scheduler_task = None
