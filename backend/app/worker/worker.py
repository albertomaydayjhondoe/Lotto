"""
Job Worker Main Loop
Autonomous background job processor
"""
import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Job, JobStatus
from app.worker.queue import dequeue_job
from app.worker.dispatcher import dispatch_job, is_job_type_supported
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def process_single_job(db: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Process a single job from the queue.
    
    Used by:
    - Background worker loop
    - Manual /jobs/process endpoint (dev/testing)
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with processing summary, or None if no jobs available:
        {
            "processed": bool,
            "job_id": str,
            "job_type": str,
            "status": str,
            "result": dict,
            "processing_time_ms": int,
            "error": Optional[str]
        }
    """
    # Dequeue next available job
    job = await dequeue_job(db)
    
    if not job:
        return {
            "processed": False,
            "message": "No pending jobs in queue"
        }
    
    start_time = time.monotonic()
    job_id = str(job.id)
    job_type = job.job_type
    
    logger.info("Starting job processing", extra={"job_id": job_id, "job_type": job_type})
    
    try:
        # Check if handler exists
        if not is_job_type_supported(job_type):
            raise KeyError(f"Unknown job_type: {job_type}")
        
        # Execute handler
        result = await dispatch_job(job, db)
        
        # Mark as completed
        job.status = JobStatus.COMPLETED
        job.result = result
        job.error_message = None
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        
        processing_time_ms = int((time.monotonic() - start_time) * 1000)
        
        logger.info(
            "Job completed successfully",
            extra={
                "job_id": job_id,
                "job_type": job_type,
                "processing_time_ms": processing_time_ms,
                "clips_created": result.get("clips_created", 0)
            }
        )
        
        return {
            "processed": True,
            "job_id": job_id,
            "job_type": job_type,
            "status": "completed",
            "result": result,
            "processing_time_ms": processing_time_ms,
            "error": None
        }
        
    except KeyError as e:
        # Unknown job type - mark as FAILED
        logger.error(
            "Job failed: unknown job type",
            extra={"job_id": job_id, "job_type": job_type, "error": str(e)}
        )
        
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        
        processing_time_ms = int((time.monotonic() - start_time) * 1000)
        
        return {
            "processed": True,
            "job_id": job_id,
            "job_type": job_type,
            "status": "failed",
            "result": None,
            "processing_time_ms": processing_time_ms,
            "error": str(e)
        }
        
    except Exception as e:
        # Handler exception - mark as FAILED
        logger.exception(
            "Job failed with exception",
            extra={"job_id": job_id, "job_type": job_type, "error": str(e)}
        )
        
        await db.rollback()
        
        # Re-fetch job to update status
        await db.refresh(job)
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        
        processing_time_ms = int((time.monotonic() - start_time) * 1000)
        
        return {
            "processed": True,
            "job_id": job_id,
            "job_type": job_type,
            "status": "failed",
            "result": None,
            "processing_time_ms": processing_time_ms,
            "error": str(e)
        }


async def worker_loop(db: AsyncSession) -> None:
    """
    Main worker loop - runs continuously processing jobs.
    
    Architecture:
    - Polls for PENDING jobs every WORKER_POLL_INTERVAL seconds
    - Uses persistent queue with row-level locking
    - Handles errors gracefully without crashing
    - Supports concurrent workers
    
    Args:
        db: Database session (should be long-lived)
        
    Note:
        This is an infinite loop. Run in background task or separate process.
    """
    logger.info("Worker loop started")
    
    while True:
        try:
            # Process one job
            result = await process_single_job(db)
            
            if not result or not result.get("processed"):
                # No jobs available, sleep before checking again
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL)
            else:
                # Job processed, continue immediately to next job
                # (no sleep - process queue as fast as possible)
                pass
                
        except Exception as e:
            # Catch-all to prevent worker crash
            logger.exception("Worker loop encountered unexpected error")
            await asyncio.sleep(settings.WORKER_POLL_INTERVAL)
