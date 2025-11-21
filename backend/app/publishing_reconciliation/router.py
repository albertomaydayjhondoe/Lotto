"""
Publishing Reconciliation Router.

FastAPI endpoints for manually triggering publication reconciliation.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.database import get_db
from app.publishing_reconciliation import reconcile_publications

router = APIRouter()


@router.post("/reconcile")
async def reconcile_endpoint(
    since_minutes: int = Query(default=10, ge=1, le=1440, description="Look back period in minutes"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger publication reconciliation.
    
    Checks publish_logs in "processing" or "retry" status and reconciles based on:
    - Webhook data: If webhook_received=True, mark as success
    - Timeout: If no webhook after X minutes, mark as failed
    
    Args:
        since_minutes: How many minutes back to check (default: 10, max: 1440/24h)
        
    Returns:
        Statistics about the reconciliation:
        ```json
        {
            "total_checked": 15,
            "marked_success": 8,
            "marked_failed": 5,
            "skipped": 2,
            "success_log_ids": ["uuid1", "uuid2", ...],
            "failed_log_ids": ["uuid3", "uuid4", ...]
        }
        ```
        
    Example:
        ```bash
        # Reconcile logs from last 15 minutes
        curl -X POST "http://localhost:8000/publishing/reconcile?since_minutes=15"
        ```
    """
    return await reconcile_publications(db, since_minutes=since_minutes)
