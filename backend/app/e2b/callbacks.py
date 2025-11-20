"""Callbacks for E2B sandbox simulation results."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Job, JobStatus
from app.e2b.models import E2BSandboxResult
from app.ledger import log_event


async def process_e2b_callback(
    job_id: UUID,
    result: E2BSandboxResult,
    db: AsyncSession,
) -> Job:
    """
    Process callback from E2B sandbox simulation.
    
    Updates job with results and logs to ledger.
    This simulates receiving results from an external E2B sandbox.
    
    Args:
        job_id: ID of the job
        result: E2BSandboxResult with simulation data
        db: Database session
    
    Returns:
        Updated Job object
    
    Raises:
        ValueError: If job not found
    """
    # Load job
    stmt = select(Job).where(Job.id == job_id)
    db_result = await db.execute(stmt)
    job = db_result.scalar_one_or_none()
    
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    # Update job with callback result
    if result.status == "completed":
        job.status = JobStatus.COMPLETED
        job.result = {
            "status": result.status,
            "num_cuts": len(result.cuts),
            "num_detections": len(result.yolo_detections),
            "num_embeddings": len(result.embeddings),
            "processing_time_ms": result.processing_time_ms,
            "callback_received_at": result.created_at.isoformat()
        }
    else:
        job.status = JobStatus.FAILED
        job.error_message = result.error_message or "E2B simulation failed"
        job.result = {
            "status": result.status,
            "error": result.error_message
        }
    
    await db.commit()
    
    # Log callback receipt to ledger
    await log_event(
        db=db,
        event_type="e2b_callback_received",
        entity_type="job",
        entity_id=str(job_id),
        metadata={
            "result_status": result.status,
            "num_cuts": len(result.cuts) if result.status == "completed" else 0,
            "processing_time_ms": result.processing_time_ms,
            "has_error": result.error_message is not None
        }
    )
    
    return job


def validate_e2b_callback(result: E2BSandboxResult) -> bool:
    """
    Validate E2B callback result structure.
    
    Args:
        result: E2BSandboxResult to validate
    
    Returns:
        True if valid, False otherwise
    """
    if result.status not in ["completed", "failed"]:
        return False
    
    if result.status == "completed":
        # Must have at least some cuts
        if len(result.cuts) == 0:
            return False
        
        # All cuts must have valid scores
        for cut in result.cuts:
            if not (0.0 <= cut.visual_score <= 1.0):
                return False
            if not (0.0 <= cut.motion_intensity <= 1.0):
                return False
            if not (0.0 <= cut.trend_score <= 1.0):
                return False
    
    return True
