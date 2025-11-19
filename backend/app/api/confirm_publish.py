"""
Confirm publish endpoint handler.
POST /confirm_publish - Confirm publish of a clip
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime

from app.models.schemas import ConfirmPublishRequest, ConfirmPublishResponse
from app.models.database import Clip, Publication, ClipStatus, Job, JobStatus
from app.core.database import get_db

router = APIRouter()


@router.post("/confirm_publish", response_model=ConfirmPublishResponse)
async def confirm_publish(
    request: ConfirmPublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manual confirmation that a clip was published on the official account.
    This triggers campaign launch.
    
    Args:
        request: Confirm publish request data
        db: Database session
        
    Returns:
        ConfirmPublishResponse with success status
    """
    # Check clip exists
    result = await db.execute(
        select(Clip).where(Clip.id == request.clip_id)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="clip not found"
        )
    
    # Check for duplicate trace_id
    if request.trace_id:
        pub_result = await db.execute(
            select(Publication).where(Publication.trace_id == request.trace_id)
        )
        existing = pub_result.scalar_one_or_none()
        if existing:
            return ConfirmPublishResponse(
                message="publish already confirmed",
                trace_id=request.trace_id
            )
    
    # Create publication record
    publication = Publication(
        id=uuid4(),
        clip_id=request.clip_id,
        platform=request.platform,
        post_url=request.post_url,
        post_id=request.post_id,
        published_at=request.published_at or datetime.utcnow(),
        confirmed_by=request.confirmed_by,
        trace_id=request.trace_id
    )
    
    db.add(publication)
    
    # Update clip status
    clip.status = ClipStatus.PUBLISHED
    
    # Create campaign launch job
    campaign_job = Job(
        id=uuid4(),
        job_type="launch_campaign",
        status=JobStatus.PENDING,
        clip_id=request.clip_id,
        params={
            "publication_id": str(publication.id),
            "platform": request.platform,
            "post_id": request.post_id
        }
    )
    
    db.add(campaign_job)
    await db.commit()
    
    return ConfirmPublishResponse(
        message="publish accepted",
        trace_id=request.trace_id
    )
