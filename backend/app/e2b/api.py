"""API endpoints for E2B sandbox simulation engine."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import Job, JobStatus, VideoAsset
from app.e2b.models import E2BSandboxRequest, E2BSandboxResult
from app.e2b.dispatcher import dispatch_e2b_job
from app.e2b.callbacks import process_e2b_callback, validate_e2b_callback


router = APIRouter(prefix="/e2b")


@router.post("/jobs/launch", response_model=dict)
async def launch_e2b_job(
    request: E2BSandboxRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Launch E2B sandbox simulation job.
    
    Creates a job with type "cut_analysis_e2b" and dispatches it
    to the E2B simulation engine.
    
    Args:
        request: E2BSandboxRequest with video_asset_id and params
        db: Database session
    
    Returns:
        dict with job_id and status
    
    Raises:
        HTTPException 404: Video asset not found
        HTTPException 500: Job creation or dispatch failed
    """
    # Validate video asset exists
    stmt = select(VideoAsset).where(VideoAsset.id == request.video_asset_id)
    result = await db.execute(stmt)
    video_asset = result.scalar_one_or_none()
    
    if not video_asset:
        raise HTTPException(
            status_code=404,
            detail=f"Video asset {request.video_asset_id} not found"
        )
    
    # Create or load job
    if request.job_id:
        # Use existing job
        stmt = select(Job).where(Job.id == request.job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {request.job_id} not found"
            )
    else:
        # Create new job
        from uuid import uuid4
        job = Job(
            id=uuid4(),
            job_type="cut_analysis_e2b",
            status=JobStatus.PENDING,
            video_asset_id=request.video_asset_id,
            params=request.params or {}
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
    
    # Dispatch job to E2B simulator
    try:
        e2b_result = await dispatch_e2b_job(job=job, db=db)
        
        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "video_asset_id": str(request.video_asset_id),
            "num_cuts_created": len(e2b_result.cuts),
            "processing_time_ms": e2b_result.processing_time_ms
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"E2B job dispatch failed: {str(e)}"
        )


@router.post("/jobs/{job_id}/callback")
async def receive_e2b_callback(
    job_id: UUID,
    result: E2BSandboxResult,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive callback from E2B sandbox with simulation results.
    
    This endpoint simulates receiving results from an external E2B sandbox.
    In production, this would be called by the actual E2B service.
    
    Args:
        job_id: UUID of the job
        result: E2BSandboxResult with simulation data
        db: Database session
    
    Returns:
        dict with acknowledgment
    
    Raises:
        HTTPException 400: Invalid callback data
        HTTPException 404: Job not found
        HTTPException 500: Callback processing failed
    """
    # Validate callback structure
    if not validate_e2b_callback(result):
        raise HTTPException(
            status_code=400,
            detail="Invalid E2B callback data"
        )
    
    # Verify job_id matches
    if result.job_id != job_id:
        raise HTTPException(
            status_code=400,
            detail=f"Job ID mismatch: URL={job_id}, body={result.job_id}"
        )
    
    try:
        # Process callback
        job = await process_e2b_callback(
            job_id=job_id,
            result=result,
            db=db
        )
        
        return {
            "status": "callback_received",
            "job_id": str(job.id),
            "job_status": job.status.value,
            "num_cuts": len(result.cuts) if result.status == "completed" else 0
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Callback processing failed: {str(e)}"
        )


@router.get("/jobs/{job_id}/status")
async def get_e2b_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get status of E2B sandbox job.
    
    Args:
        job_id: UUID of the job
        db: Database session
    
    Returns:
        dict with job status and results
    
    Raises:
        HTTPException 404: Job not found
    """
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    return {
        "job_id": str(job.id),
        "job_type": job.job_type,
        "status": job.status.value,
        "video_asset_id": str(job.video_asset_id) if job.video_asset_id else None,
        "result": job.result,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None
    }
