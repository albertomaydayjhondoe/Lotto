"""
Jobs endpoint handlers.
POST /jobs - Create a job
GET /jobs - List jobs
GET /jobs/{id} - Get a job
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID

from app.models.schemas import Job as JobSchema, JobCreate
from app.models.database import Job, JobStatus
from app.core.database import get_db

router = APIRouter()


@router.post("/jobs", response_model=JobSchema, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new ad-hoc job.
    
    Args:
        job_data: Job creation data
        db: Database session
        
    Returns:
        Created Job object
    """
    # Check for duplicate dedup_key
    if job_data.dedup_key:
        result = await db.execute(
            select(Job).where(Job.dedup_key == job_data.dedup_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return JobSchema.model_validate(existing)
    
    # Create job
    job = Job(
        id=uuid4(),
        job_type=job_data.job_type,
        status=JobStatus.PENDING,
        clip_id=UUID(job_data.clip_id) if job_data.clip_id else None,
        params=job_data.params,
        dedup_key=job_data.dedup_key
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return JobSchema.model_validate(job)


@router.get("/jobs", response_model=List[JobSchema])
async def list_jobs(
    status: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all jobs with optional filters.
    
    Args:
        status: Filter by job status
        created_by: Filter by creator (not implemented yet)
        db: Database session
        
    Returns:
        List of Job objects
    """
    query = select(Job).order_by(Job.created_at.desc())
    
    if status:
        query = query.where(Job.status == status)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [JobSchema.model_validate(job) for job in jobs]


@router.get("/jobs/{id}", response_model=JobSchema)
async def get_job(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job by ID.
    
    Args:
        id: Job ID
        db: Database session
        
    Returns:
        Job object
    """
    result = await db.execute(
        select(Job).where(Job.id == id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="job not found"
        )
    
    return JobSchema.model_validate(job)
