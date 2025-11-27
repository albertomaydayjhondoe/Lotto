"""
Background Scheduler para Meta Creative Variants Engine (PASO 10.10)

Ejecuta generación automática cada 6 horas.
"""
import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.meta_creative_variants.engine import CreativeVariantsEngine
from app.meta_creative_variants.schemas import GenerateVariantsRequest

logger = logging.getLogger(__name__)


async def creative_variants_scheduler_task():
    """
    Background task que ejecuta cada 6 horas:
    1. Detectar campañas activas sin suficientes creatives
    2. Generar nuevas variantes
    3. Subir automáticamente si presupuesto > threshold
    """
    logger.info("Starting Creative Variants Scheduler")
    
    interval_hours = 6
    interval_seconds = interval_hours * 3600
    
    while True:
        try:
            logger.info("=== Creative Variants Auto-Generation Cycle Started ===")
            start_time = datetime.utcnow()
            
            async with AsyncSessionLocal() as db:
                engine = CreativeVariantsEngine(db)
                
                # TODO: Detect campaigns needing more creatives
                # For now, stub implementation
                
                campaigns_to_process = []
                
                if settings.META_API_MODE == "stub":
                    # Stub: generar para clip ficticio
                    campaigns_to_process = [
                        {
                            "clip_id": "stub_clip_001",
                            "campaign_id": "23847656789012340",
                            "adset_id": "23847656789012345",
                        }
                    ]
                
                for campaign in campaigns_to_process:
                    try:
                        request = GenerateVariantsRequest(
                            clip_id=campaign["clip_id"],
                            campaign_id=campaign.get("campaign_id"),
                            adset_id=campaign.get("adset_id"),
                            num_variants=10,
                            auto_upload=False,  # Manual approval
                            dry_run=False,
                        )
                        
                        response = await engine.generate_variants(request)
                        
                        logger.info(
                            f"Generated {response.total_variants} variants for campaign {campaign.get('campaign_id')}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing campaign {campaign}: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"=== Cycle Complete === Duration: {duration:.2f}s | "
                f"Processed: {len(campaigns_to_process)} campaigns"
            )
            
        except Exception as e:
            logger.error(f"Error in creative variants scheduler: {e}")
        
        # Wait for next cycle
        logger.info(f"Sleeping for {interval_hours} hours until next cycle")
        await asyncio.sleep(interval_seconds)


async def start_creative_variants_scheduler():
    """Start the scheduler as a background task."""
    if settings.META_API_MODE == "stub":
        logger.info("Creative Variants Scheduler started in STUB mode")
    
    task = asyncio.create_task(creative_variants_scheduler_task())
    return task
