"""
Scheduler para Meta Full Autonomous Cycle (PASO 10.11)

Background task que ejecuta el ciclo cada 30 minutos.
"""
import asyncio
import logging
from datetime import datetime

from app.meta_full_cycle.cycle import MetaFullCycleManager
from app.core.database import AsyncSessionLocal
from app.core.config import settings


logger = logging.getLogger(__name__)


async def meta_cycle_background_task():
    """
    Background task que ejecuta el ciclo autónomo cada 30 minutos.
    
    Se ejecuta indefinidamente mientras la aplicación esté activa.
    """
    logger.info("🔄 Meta Autonomous Cycle Scheduler started (interval: 30 min)")
    
    cycle_manager = MetaFullCycleManager()
    
    while True:
        try:
            logger.info(f"⏰ Starting scheduled cycle at {datetime.utcnow().isoformat()}")
            
            async with AsyncSessionLocal() as db:
                cycle_run = await cycle_manager.run_cycle(
                    db=db,
                    triggered_by="scheduler",
                    mode=settings.META_API_MODE,
                )
                
                logger.info(
                    f"✅ Scheduled cycle completed: {cycle_run.id} "
                    f"(status={cycle_run.status}, duration={cycle_run.duration_ms}ms)"
                )
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled cycle: {e}", exc_info=True)
        
        # Wait 30 minutes before next execution
        await asyncio.sleep(30 * 60)  # 30 minutes


async def start_meta_cycle_scheduler():
    """
    Inicia el scheduler del ciclo autónomo.
    
    Debe ser llamado desde main.py en el startup de la aplicación.
    
    Returns:
        asyncio.Task con el background task
    """
    if not settings.META_API_MODE:
        logger.warning("META_API_MODE not set, defaulting to 'stub'")
    
    logger.info(f"🚀 Starting Meta Cycle Scheduler (mode={settings.META_API_MODE})")
    
    task = asyncio.create_task(meta_cycle_background_task())
    return task


async def stop_meta_cycle_scheduler(task: asyncio.Task):
    """
    Detiene el scheduler del ciclo autónomo.
    
    Debe ser llamado desde main.py en el shutdown de la aplicación.
    """
    if task and not task.done():
        logger.info("🛑 Stopping Meta Cycle Scheduler...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("✅ Meta Cycle Scheduler stopped")
