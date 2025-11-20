"""FastAPI router for Publishing Engine."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.publishing_engine.models import PublishRequest, PublishResult, PublishLogResponse
from app.publishing_engine.service import publish_clip, get_publish_logs_for_clip


router = APIRouter()


@router.post("/publish", response_model=PublishResult)
async def publish_clip_endpoint(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a clip to a social platform.
    
    Workflow:
    1. Validates clip exists
    2. Validates social account (if provided)
    3. Creates publish log
    4. Calls platform simulator
    5. Updates log with result
    6. Logs to SocialSyncLedger
    
    Args:
        request: PublishRequest with clip_id, platform, optional social_account_id
        db: Database session
    
    Returns:
        PublishResult with success status and post details
    
    Raises:
        HTTPException 404: Clip or social account not found
        HTTPException 400: Validation error (e.g., platform mismatch)
        HTTPException 500: Internal error during publish
    """
    try:
        result = await publish_clip(db, request)
        return result
    except ValueError as e:
        # Validation errors (clip not found, account not found, etc.)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during publish: {str(e)}"
        )


@router.get("/logs/{clip_id}", response_model=list[PublishLogResponse])
async def get_publish_logs_endpoint(
    clip_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all publish logs for a specific clip.
    
    Returns logs in descending order by requested_at (newest first).
    
    Args:
        clip_id: UUID of the clip
        db: Database session
    
    Returns:
        List of PublishLogResponse objects
    
    Raises:
        HTTPException 500: Database error
    """
    try:
        logs = await get_publish_logs_for_clip(db, clip_id)
        
        # Convert to response models
        return [
            PublishLogResponse(
                id=log.id,
                clip_id=log.clip_id,
                platform=log.platform,
                social_account_id=log.social_account_id,
                status=log.status,
                external_post_id=log.external_post_id,
                external_url=log.external_url,
                error_message=log.error_message,
                requested_at=log.requested_at,
                published_at=log.published_at,
                created_at=log.created_at,
                updated_at=log.updated_at
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving publish logs: {str(e)}"
        )
