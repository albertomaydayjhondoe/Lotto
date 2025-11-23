"""
PASO 8.1 - AI Memory Layer Service

Service layer for persisting and querying AI Global Worker reasoning history.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AIReasoningHistoryModel
from app.ai_global_worker.schemas import AIReasoningOutput, AIRecommendation
from app.core.config import settings


# === Save Functions ===

async def save_reasoning_to_history(
    db: AsyncSession,
    reasoning: AIReasoningOutput,
    triggered_by: str = "worker"
) -> AIReasoningHistoryModel:
    """
    Save an AIReasoningOutput to the history table.
    
    Args:
        db: Database session
        reasoning: AIReasoningOutput object to persist
        triggered_by: Source of the run ("worker", "manual", "debug")
    
    Returns:
        The created AIReasoningHistoryModel
    """
    # Determine status based on health score
    status = _determine_status(reasoning.summary.health_score)
    
    # Count critical issues
    critical_count = _count_critical_issues(reasoning.recommendations)
    
    # Serialize data
    snapshot_json = _serialize_snapshot(reasoning.snapshot)
    summary_json = _serialize_summary(reasoning.summary)
    recommendations_json = _serialize_recommendations(reasoning.recommendations)
    action_plan_json = _serialize_action_plan(reasoning.action_plan)
    
    # Create history record
    history = AIReasoningHistoryModel(
        run_id=reasoning.reasoning_id,
        triggered_by=triggered_by,
        health_score=int(reasoning.summary.health_score),
        status=status,
        critical_issues_count=critical_count,
        recommendations_count=len(reasoning.recommendations),
        snapshot_json=snapshot_json,
        summary_json=summary_json,
        recommendations_json=recommendations_json,
        action_plan_json=action_plan_json,
        duration_ms=reasoning.execution_time_ms,
        meta={
            "overall_health": reasoning.summary.overall_health,
            "generated_at": reasoning.timestamp.isoformat(),
        }
    )
    
    db.add(history)
    await db.commit()
    await db.refresh(history)
    
    return history


# === Query Functions ===

async def get_history(
    db: AsyncSession,
    *,
    limit: int = 20,
    offset: int = 0,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    status: Optional[str] = None,
    only_critical: bool = False,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> List[AIReasoningHistoryModel]:
    """
    Get history with optional filters.
    
    Args:
        db: Database session
        limit: Max number of results (capped at AI_HISTORY_MAX_LIMIT)
        offset: Pagination offset
        min_score: Minimum health score filter
        max_score: Maximum health score filter
        status: Status filter ("ok", "degraded", "critical")
        only_critical: If True, only return runs with critical issues
        from_date: Filter runs from this date
        to_date: Filter runs until this date
    
    Returns:
        List of AIReasoningHistoryModel ordered by created_at DESC
    """
    # Cap limit
    limit = min(limit, settings.AI_HISTORY_MAX_LIMIT)
    
    # Build query
    query = select(AIReasoningHistoryModel)
    
    # Apply filters
    filters = []
    
    if min_score is not None:
        filters.append(AIReasoningHistoryModel.health_score >= min_score)
    
    if max_score is not None:
        filters.append(AIReasoningHistoryModel.health_score <= max_score)
    
    if status:
        filters.append(AIReasoningHistoryModel.status == status)
    
    if only_critical:
        filters.append(AIReasoningHistoryModel.critical_issues_count > 0)
    
    if from_date:
        filters.append(AIReasoningHistoryModel.created_at >= from_date)
    
    if to_date:
        filters.append(AIReasoningHistoryModel.created_at <= to_date)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by created_at DESC (most recent first)
    query = query.order_by(desc(AIReasoningHistoryModel.created_at))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_history_item(
    db: AsyncSession,
    history_id: UUID
) -> Optional[AIReasoningHistoryModel]:
    """
    Get a single history item by ID.
    
    Args:
        db: Database session
        history_id: UUID of the history record
    
    Returns:
        AIReasoningHistoryModel or None if not found
    """
    query = select(AIReasoningHistoryModel).where(
        AIReasoningHistoryModel.id == str(history_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_history_by_run_id(
    db: AsyncSession,
    run_id: str
) -> Optional[AIReasoningHistoryModel]:
    """
    Get a history item by reasoning run_id.
    
    Args:
        db: Database session
        run_id: reasoning_id from AIReasoningOutput
    
    Returns:
        AIReasoningHistoryModel or None if not found
    """
    query = select(AIReasoningHistoryModel).where(
        AIReasoningHistoryModel.run_id == run_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# === Helper Functions ===

def _determine_status(health_score: float) -> str:
    """Determine status based on health score."""
    if health_score >= 70:
        return "ok"
    elif health_score >= 40:
        return "degraded"
    else:
        return "critical"


def _count_critical_issues(recommendations: List[AIRecommendation]) -> int:
    """Count recommendations with priority='critical'."""
    return sum(1 for rec in recommendations if rec.priority == "critical")


def _serialize_snapshot(snapshot) -> dict:
    """Serialize SystemSnapshot to compact JSON."""
    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "queue_pending": snapshot.queue_pending,
        "queue_processing": snapshot.queue_processing,
        "queue_failed": snapshot.queue_failed,
        "clips_ready": snapshot.clips_ready,
        "clips_published": snapshot.clips_published,
        "jobs_pending": snapshot.jobs_pending,
        "jobs_completed": snapshot.jobs_completed,
        "campaigns_active": snapshot.campaigns_active,
        "campaigns_paused": snapshot.campaigns_paused,
        "alerts_critical": snapshot.alerts_critical,
        "alerts_warning": snapshot.alerts_warning,
        "system_errors_recent": snapshot.system_errors_recent,
    }


def _serialize_summary(summary) -> dict:
    """Serialize HealthSummary to JSON."""
    return {
        "overall_health": summary.overall_health,
        "health_score": summary.health_score,
        "key_insights": summary.key_insights,
        "concerns": summary.concerns,
        "positives": summary.positives,
        "generated_at": summary.generated_at.isoformat(),
    }


def _serialize_recommendations(recommendations: List[AIRecommendation]) -> List[dict]:
    """Serialize list of Recommendations to JSON."""
    return [
        {
            "id": rec.id,
            "priority": rec.priority,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "impact": rec.impact,
            "effort": rec.effort,
            "action_type": rec.action_type,
            "action_payload": rec.action_payload,
        }
        for rec in recommendations
    ]


def _serialize_action_plan(action_plan) -> dict:
    """Serialize ActionPlan to JSON."""
    return {
        "plan_id": action_plan.plan_id,
        "title": action_plan.title,
        "objective": action_plan.objective,
        "steps": action_plan.steps,  # Already Dict[str, Any]
        "estimated_duration": action_plan.estimated_duration,
        "risk_level": action_plan.risk_level,
        "automated": action_plan.automated,
    }
