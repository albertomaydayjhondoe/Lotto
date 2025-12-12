"""
Dashboard AI Analyzer

Analyzes system state and detects issues.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.database import (
    Clip,
    ClipVariant,
    PublishLogModel,
    Campaign,
    Job,
    JobStatus,
    ClipStatus,
    CampaignStatus
)
from app.dashboard_api.service import (
    get_overview_stats,
    get_queue_stats,
    get_orchestrator_stats,
    get_platform_stats
)
from .models import SystemAnalysis


async def analyze_system(db: AsyncSession) -> SystemAnalysis:
    """
    Perform complete system analysis.
    
    Args:
        db: Database session
        
    Returns:
        SystemAnalysis with health metrics and detected issues
    """
    # Get stats from dashboard API
    overview = await get_overview_stats(db)
    queue = await get_queue_stats(db)
    orchestrator = await get_orchestrator_stats(db)
    platforms = await get_platform_stats(db)
    
    # Calculate health statuses
    queue_health = _calculate_queue_health(queue)
    orchestrator_health = _calculate_orchestrator_health(orchestrator)
    campaigns_health = _calculate_campaigns_health(overview)
    
    # Calculate success rate
    total_logs = overview.success_logs + overview.failed_logs
    success_rate = overview.success_logs / total_logs if total_logs > 0 else 0.0
    
    # Find best clips per platform
    best_clips = await _find_best_clips_per_platform(db)
    
    # Detect issues
    issues = []
    
    # Queue saturation check
    total_queue = queue.pending + queue.processing
    if total_queue > 50:
        issues.append({
            "severity": "critical",
            "title": "Queue overload",
            "description": f"Publishing queue has {total_queue} items. Consider running rebalance or increasing workers."
        })
    elif total_queue > 30:
        issues.append({
            "severity": "warning",
            "title": "High queue saturation",
            "description": f"Publishing queue has {total_queue} items."
        })
    
    # Failed publications check
    if queue.failed > 10:
        issues.append({
            "severity": "warning",
            "title": "Multiple failed publications",
            "description": f"{queue.failed} failed publications detected. Consider retry action."
        })
    
    # Orchestrator saturation check
    if orchestrator.saturation_rate and orchestrator.saturation_rate > 0.9:
        issues.append({
            "severity": "critical",
            "title": "Orchestrator overloaded",
            "description": f"Orchestrator saturation at {orchestrator.saturation_rate:.1%}. Run manual tick."
        })
    elif orchestrator.saturation_rate and orchestrator.saturation_rate > 0.7:
        issues.append({
            "severity": "warning",
            "title": "Orchestrator high load",
            "description": f"Orchestrator saturation at {orchestrator.saturation_rate:.1%}."
        })
    
    # Success rate check
    if success_rate < 0.7:
        issues.append({
            "severity": "critical",
            "title": "Low success rate",
            "description": f"Publication success rate is {success_rate:.1%}. Check platform integrations."
        })
    elif success_rate < 0.85:
        issues.append({
            "severity": "warning",
            "title": "Below target success rate",
            "description": f"Publication success rate is {success_rate:.1%} (target: 85%+)."
        })
    
    # Pending jobs check
    if overview.pending_jobs > 20:
        issues.append({
            "severity": "warning",
            "title": "Pending jobs accumulating",
            "description": f"{overview.pending_jobs} jobs pending. Check worker status."
        })
    
    # Old pending items check
    if queue.oldest_pending_age_seconds and queue.oldest_pending_age_seconds > 7200:  # 2 hours
        hours = queue.oldest_pending_age_seconds / 3600
        issues.append({
            "severity": "warning",
            "title": "Stale pending publications",
            "description": f"Oldest pending item is {hours:.1f} hours old. May need rescheduling."
        })
    
    # Calculate metrics
    metrics = {
        "total_clips_ready": await _count_ready_clips(db),
        "avg_processing_time_ms": queue.avg_processing_time_ms,
        "platform_distribution": {
            "instagram": platforms.instagram.total_posts,
            "tiktok": platforms.tiktok.total_posts,
            "youtube": platforms.youtube.total_posts,
            "facebook": platforms.facebook.total_posts
        },
        "total_in_queue": total_queue,
        "failed_rate": queue.failed / total_logs if total_logs > 0 else 0.0
    }
    
    return SystemAnalysis(
        timestamp=datetime.utcnow(),
        queue_health=queue_health,
        orchestrator_health=orchestrator_health,
        campaigns_status=campaigns_health,
        publish_success_rate=success_rate,
        pending_scheduled=queue.pending,
        best_clip_per_platform=best_clips,
        issues_detected=issues,
        metrics=metrics
    )


def _calculate_queue_health(queue) -> str:
    """Calculate queue health based on metrics."""
    total_queue = queue.pending + queue.processing
    failed_rate = queue.failed / (queue.success + queue.failed) if (queue.success + queue.failed) > 0 else 0.0
    
    if total_queue > 50 or failed_rate > 0.3:
        return "critical"
    elif total_queue > 30 or failed_rate > 0.15:
        return "warning"
    else:
        return "good"


def _calculate_orchestrator_health(orchestrator) -> str:
    """Calculate orchestrator health based on saturation."""
    if orchestrator.saturation_rate is None:
        return "good"
    
    if orchestrator.saturation_rate > 0.9:
        return "critical"
    elif orchestrator.saturation_rate > 0.7:
        return "warning"
    else:
        return "good"


def _calculate_campaigns_health(overview) -> str:
    """Calculate campaigns health based on job status."""
    if overview.total_campaigns == 0:
        return "good"
    
    failed_rate = overview.failed_jobs / overview.total_jobs if overview.total_jobs > 0 else 0.0
    
    if failed_rate > 0.3:
        return "critical"
    elif failed_rate > 0.15 or overview.pending_jobs > 20:
        return "warning"
    else:
        return "good"


async def _find_best_clips_per_platform(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
    """
    Find best scoring clip for each platform.
    
    Args:
        db: Database session
        
    Returns:
        Dict mapping platform to best clip info
    """
    platforms = ["instagram", "tiktok", "youtube", "facebook"]
    result = {}
    
    for platform in platforms:
        # Find clip variants ready for this platform
        query = (
            select(ClipVariant, Clip)
            .join(Clip, ClipVariant.clip_id == Clip.id)
            .where(
                and_(
                    ClipVariant.platform == platform,
                    ClipVariant.status == "ready",
                    ClipVariant.visual_score.isnot(None)
                )
            )
            .order_by(ClipVariant.visual_score.desc())
            .limit(1)
        )
        
        result_row = await db.execute(query)
        row = result_row.first()
        
        if row:
            variant, clip = row
            result[platform] = {
                "clip_id": str(clip.id),
                "variant_id": str(variant.id),
                "score": float(variant.visual_score) if variant.visual_score else 0.0,
                "duration": variant.duration_sec,
                "created_at": clip.created_at.isoformat() if clip.created_at else None
            }
    
    return result


async def _count_ready_clips(db: AsyncSession) -> int:
    """Count total clips ready for publication."""
    result = await db.execute(
        select(func.count(ClipVariant.id))
        .where(ClipVariant.status == "ready")
    )
    return result.scalar() or 0
