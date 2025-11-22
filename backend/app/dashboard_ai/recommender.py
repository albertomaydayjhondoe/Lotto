"""
Dashboard AI Recommender

Generates intelligent recommendations based on system analysis.
"""

from datetime import datetime, timedelta
from typing import List
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.database import (
    Clip,
    ClipVariant,
    PublishLogModel,
    Campaign,
    CampaignStatus
)
from .models import Recommendation, SystemAnalysis
from .analyzer import analyze_system


async def generate_recommendations(db: AsyncSession) -> List[Recommendation]:
    """
    Generate AI recommendations based on system analysis.
    
    Args:
        db: Database session
        
    Returns:
        List of Recommendation objects
    """
    recommendations = []
    
    # Get current system analysis
    analysis = await analyze_system(db)
    
    # Recommendation 1: Publish best clips
    for platform, clip_info in analysis.best_clip_per_platform.items():
        if clip_info.get("score", 0.0) > 0.8:
            recommendations.append(Recommendation(
                id=uuid4(),
                title=f"Publish high-scoring {platform} clip",
                description=f"Clip with score {clip_info['score']:.2f} is ready for {platform}. Optimal for immediate publication.",
                severity="info",
                action="publish",
                payload={
                    "clip_id": clip_info["clip_id"],
                    "variant_id": clip_info["variant_id"],
                    "platform": platform
                },
                created_at=datetime.utcnow()
            ))
    
    # Recommendation 2: Run orchestrator if saturated
    if analysis.orchestrator_health == "critical":
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Run orchestrator tick immediately",
            description="Orchestrator is overloaded. Running a manual tick will process pending decisions.",
            severity="critical",
            action="run_orchestrator",
            payload={},
            created_at=datetime.utcnow()
        ))
    elif analysis.orchestrator_health == "warning":
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Consider running orchestrator tick",
            description="Orchestrator load is elevated. A manual tick may improve throughput.",
            severity="warning",
            action="run_orchestrator",
            payload={},
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 3: Rebalance queue if overloaded
    if analysis.queue_health == "critical":
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Rebalance publishing queue",
            description=f"Queue has {analysis.pending_scheduled} pending items. Rebalancing will optimize scheduling.",
            severity="critical",
            action="rebalance_queue",
            payload={},
            created_at=datetime.utcnow()
        ))
    elif analysis.queue_health == "warning":
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Queue optimization available",
            description="Publishing queue is moderately loaded. Consider rebalancing.",
            severity="warning",
            action="rebalance_queue",
            payload={},
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 4: Retry failed publications
    failed_count = next((issue for issue in analysis.issues_detected if "failed publications" in issue.get("title", "")), None)
    if failed_count:
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Retry failed publications",
            description="Multiple failed publications detected. Retry action may recover them.",
            severity="warning",
            action="retry",
            payload={"status": "failed"},
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 5: Run scheduler tick
    if analysis.pending_scheduled > 20:
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Run scheduler tick",
            description=f"{analysis.pending_scheduled} items pending scheduling. Run scheduler to process them.",
            severity="info",
            action="run_scheduler",
            payload={"dry_run": False},
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 6: Promote clips to campaigns
    inactive_campaigns = await _find_inactive_campaigns(db)
    for campaign in inactive_campaigns[:3]:  # Top 3
        recommendations.append(Recommendation(
            id=uuid4(),
            title=f"Add clips to campaign '{campaign.name}'",
            description=f"Campaign '{campaign.name}' has no recent activity. Consider adding new clips.",
            severity="info",
            action="promote",
            payload={
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name
            },
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 7: Optimize schedule for low-performing platforms
    low_performing = [
        platform for platform, count in analysis.metrics.get("platform_distribution", {}).items()
        if count < 5
    ]
    if low_performing:
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Increase activity on underutilized platforms",
            description=f"Platforms {', '.join(low_performing)} have low activity. Schedule more clips.",
            severity="info",
            action="optimize_schedule",
            payload={"platforms": low_performing},
            created_at=datetime.utcnow()
        ))
    
    # Recommendation 8: Clear old failed items
    if analysis.metrics.get("failed_rate", 0.0) > 0.2:
        recommendations.append(Recommendation(
            id=uuid4(),
            title="Clean up old failed publications",
            description="High failed rate detected. Clear old failed items to improve queue health.",
            severity="info",
            action="clear_failed",
            payload={"older_than_days": 7},
            created_at=datetime.utcnow()
        ))
    
    # Sort by severity: critical -> warning -> info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    recommendations.sort(key=lambda r: severity_order.get(r.severity, 3))
    
    return recommendations


async def _find_inactive_campaigns(db: AsyncSession, days: int = 7) -> List[Campaign]:
    """
    Find campaigns with no recent activity.
    
    Args:
        db: Database session
        days: Number of days to look back
        
    Returns:
        List of inactive Campaign objects
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Find campaigns that are active but haven't been updated recently
    query = (
        select(Campaign)
        .where(
            and_(
                Campaign.status.in_([CampaignStatus.DRAFT, CampaignStatus.ACTIVE]),
                Campaign.updated_at < cutoff_date
            )
        )
        .limit(10)
    )
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return list(campaigns)
