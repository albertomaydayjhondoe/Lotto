"""
Job Worker - Internal async job processor
Handles job execution and clip generation
"""
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Job, JobStatus, Clip, ClipStatus, VideoAsset


async def run_job(job_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Execute a job and process it based on job_type
    
    Args:
        job_id: UUID of the job to process (as string)
        db: Async database session
        
    Returns:
        Dictionary with processing summary:
        {
            "job_id": str,
            "status": str,
            "clips_generated": int,
            "processing_time_ms": int,
            "error": Optional[str]
        }
    """
    start_time = datetime.utcnow()
    
    try:
        # Convert string to UUID
        from uuid import UUID
        job_uuid = UUID(job_id)
        
        # 1. Read job from database
        result = await db.execute(
            select(Job).where(Job.id == job_uuid)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {
                "job_id": job_id,
                "status": "error",
                "error": "Job not found",
                "clips_generated": 0,
                "processing_time_ms": 0
            }
        
        # 2. Validate job status
        if job.status not in [JobStatus.PENDING]:
            return {
                "job_id": job_id,
                "status": "error",
                "error": f"Job is in {job.status} state, cannot process",
                "clips_generated": 0,
                "processing_time_ms": 0
            }
        
        # 3. Change status to PROCESSING
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.utcnow()
        await db.flush()
        
        # 4. Process based on job_type
        if job.job_type == "cut_analysis":
            clips_generated = await _process_cut_analysis(job, db)
        elif job.job_type == "generate_variants":
            clips_generated = await _process_generate_variants(job, db)
        else:
            # Unknown job type - mark as failed
            job.status = JobStatus.FAILED
            job.error_message = f"Unknown job_type: {job.job_type}"
            job.updated_at = datetime.utcnow()
            await db.commit()
            
            return {
                "job_id": str(job.id),
                "status": "failed",
                "error": job.error_message,
                "clips_generated": 0,
                "processing_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
        
        # 5. Mark job as COMPLETED
        job.status = JobStatus.COMPLETED
        job.result = {
            "clips_generated": clips_generated,
            "completed_at": datetime.utcnow().isoformat()
        }
        job.updated_at = datetime.utcnow()
        await db.commit()
        
        # 6. Calculate processing time
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "job_id": str(job.id),
            "status": "completed",
            "clips_generated": clips_generated,
            "processing_time_ms": processing_time_ms,
            "error": None
        }
        
    except Exception as e:
        # Rollback on error
        await db.rollback()
        
        # Try to mark job as failed
        try:
            from uuid import UUID
            job_uuid = UUID(job_id)
            result = await db.execute(
                select(Job).where(Job.id == job_uuid)
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                await db.commit()
        except:
            pass  # Best effort
        
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "clips_generated": 0,
            "processing_time_ms": processing_time_ms
        }


async def _process_cut_analysis(job: Job, db: AsyncSession) -> int:
    """
    Process cut_analysis job: analyze video and generate N clips
    
    Args:
        job: Job object
        db: Database session
        
    Returns:
        Number of clips generated
    """
    # Simulate video analysis processing
    await asyncio.sleep(0.5)  # Simulate processing time
    
    # Get video asset
    if not job.video_asset_id:
        raise ValueError("Job has no associated video_asset_id")
    
    result = await db.execute(
        select(VideoAsset).where(VideoAsset.id == job.video_asset_id)
    )
    video_asset = result.scalar_one_or_none()
    
    if not video_asset:
        raise ValueError(f"VideoAsset {job.video_asset_id} not found")
    
    # Generate fake clips based on video duration
    # Assume default duration if not set
    video_duration_ms = video_asset.duration_ms or 60000  # Default 1 minute
    
    # Generate 3-5 clips depending on video length
    num_clips = min(5, max(3, video_duration_ms // 20000))  # 1 clip per 20 seconds
    
    clips_created = 0
    for i in range(num_clips):
        # Calculate clip timestamps
        segment_duration = video_duration_ms // num_clips
        start_ms = i * segment_duration
        end_ms = start_ms + segment_duration
        
        # Create clip
        clip = Clip(
            id=uuid4(),
            video_asset_id=video_asset.id,
            start_ms=start_ms,
            end_ms=end_ms,
            duration_ms=segment_duration,
            visual_score=0.7 + (i * 0.05),  # Fake scores 0.7-0.9
            status=ClipStatus.READY,
            params={
                "generated_by_job": str(job.id),
                "analysis_method": "fake_cut_analysis",
                "clip_number": i + 1,
                "total_clips": num_clips
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(clip)
        clips_created += 1
    
    await db.flush()
    
    return clips_created


async def _process_generate_variants(job: Job, db: AsyncSession) -> int:
    """
    Process generate_variants job: generate platform-specific variants
    
    Args:
        job: Job object
        db: Database session
        
    Returns:
        Number of variants generated (simulated)
    """
    # Simulate variant generation
    await asyncio.sleep(0.3)
    
    if not job.clip_id:
        raise ValueError("Job has no associated clip_id")
    
    # Simulate generating variants
    # In real implementation, this would call FFmpeg to create platform-specific videos
    
    return 3  # Fake: generated 3 variants (e.g., Instagram, TikTok, YouTube)
