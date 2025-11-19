"""
Upload endpoint handler.
POST /upload - Upload video file and create analysis job
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime
import os
import aiofiles

from app.models.schemas import VideoUploadResponse
from app.models.database import VideoAsset, Job, JobStatus
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    release_date: str = Form(None),
    idempotency_key: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a full video clip and create initial analysis job.
    
    Args:
        file: Video file to upload
        title: Optional video title
        description: Optional video description
        release_date: Optional release date
        idempotency_key: Optional idempotency key
        db: Database session
        
    Returns:
        VideoUploadResponse with video_asset_id and job_id
    """
    # Validate file
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file must be a video"
        )
    
    # Check idempotency
    if idempotency_key:
        result = await db.execute(
            select(VideoAsset).where(VideoAsset.idempotency_key == idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Return existing upload
            job_result = await db.execute(
                select(Job).where(Job.video_asset_id == existing.id).limit(1)
            )
            job = job_result.scalar_one_or_none()
            return VideoUploadResponse(
                video_asset_id=existing.id,
                job_id=job.id if job else uuid4(),
                message="Upload already exists (idempotency)"
            )
    
    # Create video asset
    video_asset = VideoAsset(
        id=uuid4(),
        title=title,
        description=description,
        release_date=datetime.fromisoformat(release_date) if release_date else None,
        idempotency_key=idempotency_key
    )
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{video_asset.id}.mp4")
    
    # Write file asynchronously
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    video_asset.file_path = file_path
    video_asset.file_size = len(content)
    
    db.add(video_asset)
    
    # Create analysis job
    job = Job(
        id=uuid4(),
        job_type="analyze_video",
        status=JobStatus.PENDING,
        video_asset_id=video_asset.id,
        params={"auto_generated": True}
    )
    
    db.add(job)
    await db.commit()
    
    return VideoUploadResponse(
        video_asset_id=video_asset.id,
        job_id=job.id,
        message="Upload accepted, analysis job queued"
    )
