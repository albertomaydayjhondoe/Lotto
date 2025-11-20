"""
Persistent Job Queue
Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent processing
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.database import Job, JobStatus


async def dequeue_job(db: AsyncSession) -> Optional[Job]:
    """
    Dequeue a single PENDING job from the queue.
    
    Uses SELECT FOR UPDATE SKIP LOCKED to ensure:
    - Only one worker gets each job
    - No deadlocks between concurrent workers
    - Automatic row-level locking
    
    Args:
        db: Async database session
        
    Returns:
        Job object ready for processing, or None if no jobs available
    """
    # Use raw SQL for PostgreSQL-specific FOR UPDATE SKIP LOCKED
    # SQLite doesn't support this, so we'll handle both cases
    
    try:
        # Try PostgreSQL syntax first
        query = text("""
            SELECT * FROM jobs 
            WHERE status = 'pending'
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        """)
        
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        # Get the job object
        job_result = await db.execute(
            select(Job).where(Job.id == row.id)
        )
        job = job_result.scalar_one_or_none()
        
    except Exception:
        # Fallback for SQLite (no FOR UPDATE SKIP LOCKED support)
        # Use simple SELECT with immediate status update
        result = await db.execute(
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .order_by(Job.created_at)
            .limit(1)
        )
        job = result.scalar_one_or_none()
    
    if not job:
        return None
    
    # Mark as PROCESSING
    job.status = JobStatus.PROCESSING
    job.updated_at = datetime.utcnow()
    
    # Commit immediately to lock this job
    await db.commit()
    await db.refresh(job)
    
    return job


async def requeue_job(job: Job, db: AsyncSession) -> None:
    """
    Requeue a job for retry.
    
    Args:
        job: Job to requeue
        db: Database session
    """
    job.status = JobStatus.RETRY
    job.updated_at = datetime.utcnow()
    await db.commit()
