"""Job dispatcher for E2B sandbox simulation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Job, JobStatus
from app.e2b.runner import run_e2b_simulation
from app.e2b.models import E2BSandboxResult
from app.ledger import log_job_event


async def dispatch_e2b_job(
    job: Job,
    db: AsyncSession,
) -> E2BSandboxResult:
    """
    Dispatch job to E2B sandbox simulation.
    
    Routes job_type="cut_analysis_e2b" to run_e2b_simulation().
    Updates job status and logs events.
    
    Args:
        job: Job to process
        db: Database session
    
    Returns:
        E2BSandboxResult with simulation output
    
    Raises:
        ValueError: If job type is not supported
    """
    if job.job_type != "cut_analysis_e2b":
        raise ValueError(f"Unsupported job type for E2B: {job.job_type}")
    
    # Update job status to PROCESSING
    job.status = JobStatus.PROCESSING
    await db.commit()
    
    await log_job_event(
        db=db,
        job_id=job.id,
        event_type="job_processing_started",
        metadata={
            "job_type": job.job_type,
            "video_asset_id": str(job.video_asset_id),
            "dispatcher": "e2b"
        }
    )
    
    try:
        # Run E2B simulation
        result = await run_e2b_simulation(job=job, db=db)
        
        # Update job with result
        job.status = JobStatus.COMPLETED
        job.result = {
            "status": result.status,
            "num_cuts": len(result.cuts),
            "num_detections": len(result.yolo_detections),
            "num_embeddings": len(result.embeddings),
            "processing_time_ms": result.processing_time_ms
        }
        await db.commit()
        
        await log_job_event(
            db=db,
            job_id=job.id,
            event_type="job_completed",
            metadata={
                "status": result.status,
                "num_cuts": len(result.cuts),
                "processing_time_ms": result.processing_time_ms
            }
        )
        
        return result
        
    except Exception as e:
        # Update job status to FAILED
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.commit()
        
        await log_job_event(
            db=db,
            job_id=job.id,
            event_type="job_failed",
            metadata={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        
        raise


def should_use_e2b_dispatcher(job: Job) -> bool:
    """
    Check if job should be routed to E2B dispatcher.
    
    Args:
        job: Job to check
    
    Returns:
        True if job_type is "cut_analysis_e2b"
    """
    return job.job_type == "cut_analysis_e2b"
