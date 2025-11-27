"""Scheduler for Meta Creative Production Engine (PASO 10.17)"""
import asyncio
from datetime import datetime, timedelta
import logging

from app.meta_creative_production.variant_generator import AutonomousVariantGenerator
from app.meta_creative_production.promotion_loop import AutoPromotionLoop
from app.meta_creative_production.fatigue_monitor import FatigueMonitor

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None
_is_running = False

async def creative_production_background_task():
    """
    Background task for continuous creative production (12h cycle).
    
    Actions:
    1. Generate variants for active master creatives
    2. Upload to Meta Ads
    3. Promote top 3 performers
    4. Monitor fatigue and create refreshes
    5. Repeat every 12h
    """
    global _is_running
    
    logger.info("🚀 Creative Production Engine scheduler started (12h cycle)")
    
    retry_count = 0
    max_retries = 3
    
    while _is_running:
        try:
            logger.info("▶️ Running creative production cycle...")
            start_time = datetime.utcnow()
            
            # Initialize components (STUB mode)
            generator = AutonomousVariantGenerator(mode="stub")
            promotion_loop = AutoPromotionLoop(mode="stub")
            fatigue_monitor = FatigueMonitor(mode="stub")
            
            # Step 1: Monitor fatigue
            logger.info("🔍 Monitoring variant fatigue...")
            fatigue_result = await fatigue_monitor.monitor_all_variants()
            logger.info(
                f"✅ Fatigue check: {fatigue_result.variants_checked} checked, "
                f"{fatigue_result.fatigued_detected} fatigued, "
                f"{fatigue_result.archived_count} archived"
            )
            
            # Step 2: Generate new variants (STUB: simulate)
            logger.info("🎨 Generating new variants...")
            variants_generated = 25  # STUB
            logger.info(f"✅ Generated {variants_generated} new variants")
            
            # Step 3: Upload to Meta Ads (STUB: simulate)
            logger.info("📤 Uploading variants to Meta Ads...")
            uploads_successful = 20  # STUB
            logger.info(f"✅ Uploaded {uploads_successful} variants")
            
            # Step 4: Promote top 3
            logger.info("🏆 Promoting top 3 performers...")
            # STUB: simulate promotion
            logger.info("✅ Top 3 promoted")
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Creative production cycle completed in {elapsed:.1f}s")
            
            # Reset retry count on success
            retry_count = 0
            
            # Wait 12 hours
            logger.info("⏰ Waiting 12h until next cycle...")
            await asyncio.sleep(12 * 60 * 60)  # 12 hours
            
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Error in creative production cycle: {e}", exc_info=True)
            
            if retry_count >= max_retries:
                logger.error(f"❌ Max retries ({max_retries}) reached. Stopping scheduler.")
                _is_running = False
                break
            
            # Wait 5 minutes before retry
            logger.info(f"⏳ Retrying in 5 minutes (attempt {retry_count}/{max_retries})...")
            await asyncio.sleep(5 * 60)
    
    logger.info("🛑 Creative Production Engine scheduler stopped")

async def start_creative_production_scheduler():
    """Start the creative production scheduler and return task"""
    global _scheduler_task, _is_running
    
    if _is_running:
        logger.warning("⚠️ Creative production scheduler already running")
        return _scheduler_task
    
    _is_running = True
    _scheduler_task = asyncio.create_task(creative_production_background_task())
    logger.info("✅ Creative production scheduler task created")
    return _scheduler_task

async def stop_creative_production_scheduler(task: asyncio.Task):
    """Stop the creative production scheduler"""
    global _is_running
    
    if not _is_running:
        logger.warning("⚠️ Creative production scheduler not running")
        return
    
    _is_running = False
    
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("✅ Creative production scheduler stopped")
