"""Core publishing service logic."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Clip, SocialAccountModel, PublishLogModel
from app.publishing_engine.models import PublishRequest, PublishResult
from app.publishing_engine.simulator import get_simulator
from app.ledger import log_event

# TODO: Replace simulators with real API clients when credentials available
from app.publishing_integrations import get_provider_client  # noqa: F401


async def publish_clip(
    db: AsyncSession,
    request: PublishRequest
) -> PublishResult:
    """
    Publish a clip to a social platform.
    
    Complete workflow:
    1. Validate clip exists
    2. Validate social account if provided
    3. Create pending PublishLog
    4. Call platform simulator
    5. Update log with result
    6. Log events to SocialSyncLedger
    
    Args:
        db: Database session
        request: PublishRequest with clip_id, platform, optional social_account_id
    
    Returns:
        PublishResult with success status and details
    
    Raises:
        ValueError: If clip not found or social account not found
    """
    # 1. Validate clip exists
    stmt = select(Clip).where(Clip.id == request.clip_id)
    result = await db.execute(stmt)
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise ValueError(f"Clip {request.clip_id} not found")
    
    # 2. Validate social account if provided
    if request.social_account_id:
        stmt = select(SocialAccountModel).where(
            SocialAccountModel.id == request.social_account_id
        )
        result = await db.execute(stmt)
        social_account = result.scalar_one_or_none()
        
        if not social_account:
            raise ValueError(f"Social account {request.social_account_id} not found")
        
        # Verify platform matches
        if social_account.platform != request.platform:
            raise ValueError(
                f"Social account platform {social_account.platform} "
                f"does not match request platform {request.platform}"
            )
    
    # 3. Create pending PublishLog
    publish_log = PublishLogModel(
        id=uuid4(),
        clip_id=request.clip_id,
        platform=request.platform,
        social_account_id=request.social_account_id,
        status="pending",
        requested_at=datetime.utcnow(),
        extra_metadata=request.extra_metadata or {}
    )
    
    db.add(publish_log)
    await db.flush()
    
    # Log publish started
    await log_event(
        db=db,
        event_type="publish_started",
        entity_type="clip",
        entity_id=str(request.clip_id),
        metadata={
            "platform": request.platform,
            "social_account_id": str(request.social_account_id) if request.social_account_id else None,
            "publish_log_id": str(publish_log.id)
        }
    )
    
    # 4. Call platform simulator
    try:
        simulator = await get_simulator(request.platform)
        publish_result = await simulator(request)
    except ValueError as e:
        # Unsupported platform
        publish_log.status = "failed"
        publish_log.error_message = str(e)
        await db.commit()
        
        await log_event(
            db=db,
            event_type="publish_failed",
            entity_type="clip",
            entity_id=str(request.clip_id),
            metadata={
                "platform": request.platform,
                "error": str(e),
                "publish_log_id": str(publish_log.id)
            }
        )
        
        return PublishResult(
            success=False,
            external_post_id=None,
            external_url=None,
            error_message=str(e),
            platform=request.platform,
            clip_id=request.clip_id,
            social_account_id=request.social_account_id
        )
    
    # 5. Update log with result
    if publish_result.success:
        publish_log.status = "success"
        publish_log.external_post_id = publish_result.external_post_id
        publish_log.external_url = publish_result.external_url
        publish_log.published_at = datetime.utcnow()
        
        await db.commit()
        
        # Log success
        await log_event(
            db=db,
            event_type="publish_successful",
            entity_type="clip",
            entity_id=str(request.clip_id),
            metadata={
                "platform": request.platform,
                "external_post_id": publish_result.external_post_id,
                "external_url": publish_result.external_url,
                "publish_log_id": str(publish_log.id)
            }
        )
    else:
        publish_log.status = "failed"
        publish_log.error_message = publish_result.error_message
        
        await db.commit()
        
        # Log failure
        await log_event(
            db=db,
            event_type="publish_failed",
            entity_type="clip",
            entity_id=str(request.clip_id),
            metadata={
                "platform": request.platform,
                "error": publish_result.error_message,
                "publish_log_id": str(publish_log.id)
            }
        )
    
    return publish_result


async def get_publish_logs_for_clip(
    db: AsyncSession,
    clip_id: UUID
) -> list[PublishLogModel]:
    """
    Get all publish logs for a specific clip.
    
    Args:
        db: Database session
        clip_id: UUID of the clip
    
    Returns:
        List of PublishLogModel instances
    """
    stmt = select(PublishLogModel).where(
        PublishLogModel.clip_id == clip_id
    ).order_by(PublishLogModel.requested_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()
