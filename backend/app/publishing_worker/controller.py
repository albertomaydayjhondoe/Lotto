"""
Publishing Worker Controller.

Provides API endpoints for manual worker control (useful for development/debugging).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.publishing_worker import run_publishing_worker_once
from app.auth.permissions import require_role

router = APIRouter()


@router.post("/worker/process_once")
async def process_once(
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_role("admin", "manager", "operator"))
):
    """
    Manually trigger processing of one pending log from the queue.
    
    This endpoint is useful for:
    - Development and debugging
    - Manual queue processing
    - Testing worker behavior without running the full loop
    
    Returns:
        Processing result with log details and status
        
    Example:
        ```bash
        curl -X POST http://localhost:8000/publishing/worker/process_once
        ```
        
    Response:
        ```json
        {
            "processed": true,
            "log_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "success",
            "error": null,
            "external_post_id": "instagram_post_12345",
            "platform": "instagram"
        }
        ```
    """
    result = await run_publishing_worker_once(db)
    return result
