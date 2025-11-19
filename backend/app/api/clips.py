"""
Clips endpoint handlers.
GET /clips - List clips
POST /clips/{id}/variants - Request variant generation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID

from app.models.schemas import Clip as ClipSchema, ClipVariantsRequest, Job as JobSchema
from app.models.database import Clip, Job, JobStatus
from app.core.database import get_db

router = APIRouter()


@router.get("/clips", response_model=List[ClipSchema])
async def list_clips(
    status: Optional[str] = Query(None),
    min_visual_score: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List clips with optional filters.
    
    Args:
        status: Filter by clip status
        min_visual_score: Filter by minimum visual score
        db: Database session
        
    Returns:
        List of Clip objects
    """
    query = select(Clip).order_by(Clip.created_at.desc())
    
    if status:
        query = query.where(Clip.status == status)
    
    if min_visual_score is not None:
        query = query.where(Clip.visual_score >= min_visual_score)
    
    result = await db.execute(query)
    clips = result.scalars().all()
    
    return [ClipSchema.model_validate(clip) for clip in clips]


@router.post("/clips/{id}/variants", response_model=JobSchema, status_code=202)
async def create_clip_variants(
    id: UUID,
    request: ClipVariantsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request variant generation for a clip.
    
    Args:
        id: Clip ID
        request: Variant generation request
        db: Database session
        
    Returns:
        Job object for variant generation
    """
    # Check clip exists
    result = await db.execute(
        select(Clip).where(Clip.id == id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="clip not found"
        )
    
    # Check for duplicate dedup_key
    if request.dedup_key:
        job_result = await db.execute(
            select(Job).where(Job.dedup_key == request.dedup_key)
        )
        existing = job_result.scalar_one_or_none()
        if existing:
            return JobSchema.model_validate(existing)
    
    # Create variant generation job
    job = Job(
        id=uuid4(),
        job_type="generate_variants",
        status=JobStatus.PENDING,
        clip_id=id,
        params={
            "n_variants": request.n_variants,
            "options": request.options or {}
        },
        dedup_key=request.dedup_key
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return JobSchema.model_validate(job)
