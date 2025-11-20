"""
Upload endpoint handler.
POST /upload - Upload video file and create analysis job with REAL implementation.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime
import os
import aiofiles
from pathlib import Path

from app.models.schemas import VideoUploadResponse
from app.models.database import VideoAsset, Job, JobStatus
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

# Chunk size for reading/writing files (8MB)
CHUNK_SIZE = 8 * 1024 * 1024


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
    Upload a full video clip and create initial cut_analysis job.
    
    This endpoint:
    1. Validates the uploaded file is a video
    2. Checks idempotency_key to prevent duplicate uploads
    3. Saves the file to disk in chunks (memory efficient)
    4. Creates a video_asset record in the database
    5. Creates a cut_analysis job for processing
    6. Returns the video_asset_id and job_id
    
    Args:
        file: Video file (multipart/form-data)
        title: Optional video title
        description: Optional video description
        release_date: Optional release date (format: YYYY-MM-DD)
        idempotency_key: Optional key to prevent duplicate uploads
        db: Database session
        
    Returns:
        VideoUploadResponse with video_asset_id, job_id, and message
        
    Raises:
        HTTPException 400: If no file provided or invalid file type
        HTTPException 500: If error saving file or creating database records
    """
    # 1. Validate file presence
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # 2. Validate content type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Expected video/*, got {file.content_type}"
        )
    
    # 3. Check idempotency to prevent duplicate uploads
    if idempotency_key:
        result = await db.execute(
            select(VideoAsset).where(VideoAsset.idempotency_key == idempotency_key)
        )
        existing_asset = result.scalar_one_or_none()
        if existing_asset:
            # Find associated job
            job_result = await db.execute(
                select(Job).where(Job.video_asset_id == existing_asset.id).limit(1)
            )
            existing_job = job_result.scalar_one_or_none()
            return VideoUploadResponse(
                video_asset_id=existing_asset.id,
                job_id=existing_job.id if existing_job else uuid4(),
                message="Upload already exists (idempotency)"
            )
    
    # 4. Generate UUID and extract file extension
    file_uuid = uuid4()
    file_extension = Path(file.filename).suffix or ".mp4"  # Default to .mp4 if no extension
    
    # 5. Create storage directory if it doesn't exist
    storage_dir = Path(settings.VIDEO_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # 6. Build file path (relative for DB, absolute for saving)
    relative_path = f"{settings.VIDEO_STORAGE_DIR}/{file_uuid}{file_extension}"
    absolute_path = storage_dir / f"{file_uuid}{file_extension}"
    
    # 7. Parse release_date if provided
    parsed_release_date = None
    if release_date:
        try:
            parsed_release_date = datetime.fromisoformat(release_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid release_date format. Expected YYYY-MM-DD, got {release_date}"
            )
    
    try:
        # 8. Save file to disk in chunks (memory efficient)
        file_size = 0
        async with aiofiles.open(absolute_path, 'wb') as out_file:
            while chunk := await file.read(CHUNK_SIZE):
                await out_file.write(chunk)
                file_size += len(chunk)
        
        # 9. Create video_asset record in database
        video_asset = VideoAsset(
            id=file_uuid,
            title=title,
            description=description,
            release_date=parsed_release_date,
            file_path=relative_path,
            file_size=file_size,
            duration_ms=None,  # Will be calculated during job processing
            idempotency_key=idempotency_key,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(video_asset)
        await db.flush()  # Flush to get the ID without committing yet
        
        # 10. Create cut_analysis job
        job = Job(
            id=uuid4(),
            job_type="cut_analysis",
            status=JobStatus.PENDING,
            video_asset_id=video_asset.id,
            clip_id=None,
            params={"reason": "initial_cut_from_upload"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(job)
        
        # 11. Commit transaction
        await db.commit()
        await db.refresh(video_asset)
        await db.refresh(job)
        
        # 12. Return response
        return VideoUploadResponse(
            video_asset_id=video_asset.id,
            job_id=job.id,
            message="Upload accepted, analysis job queued"
        )
        
    except Exception as e:
        # Rollback database changes
        await db.rollback()
        
        # Try to clean up the file if it was created
        if absolute_path.exists():
            try:
                absolute_path.unlink()
            except:
                pass  # Best effort cleanup
        
        # Log the error (in production, use proper logging)
        print(f"Error processing upload: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el vídeo: {str(e)}"
        )