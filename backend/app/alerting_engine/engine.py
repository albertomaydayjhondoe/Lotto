"""
Alerting Engine

Analyzes system state and generates alerts based on various conditions.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.database import (
    PublishLogModel,
    Job,
    JobStatus,
    SocialAccountModel,
    Campaign,
    CampaignStatus
)
from app.ledger import get_recent_events
from .models import Alert, AlertCreate, AlertType, AlertSeverity
from .service import create_alert, check_duplicate_alert


async def analyze_system_state(db: AsyncSession) -> list[Alert]:
    """
    Analyze system state and generate alerts for issues.
    
    Detects:
    1. Queue saturation (pending publications)
    2. Scheduler backlog (overdue scheduled items)
    3. Orchestrator inactivity
    4. Publish failure spikes
    5. OAuth tokens expiring soon
    6. Worker crashes
    7. Blocked campaigns
    8. System health degradation
    
    Args:
        db: Database session
        
    Returns:
        List of generated Alert instances
    """
    alerts = []
    
    # 1. Check queue saturation
    queue_alerts = await _check_queue_saturation(db)
    alerts.extend(queue_alerts)
    
    # 2. Check scheduler backlog
    scheduler_alerts = await _check_scheduler_backlog(db)
    alerts.extend(scheduler_alerts)
    
    # 3. Check orchestrator activity
    orchestrator_alerts = await _check_orchestrator_activity(db)
    alerts.extend(orchestrator_alerts)
    
    # 4. Check publish failure spikes
    failure_alerts = await _check_publish_failures(db)
    alerts.extend(failure_alerts)
    
    # 5. Check OAuth expiration
    oauth_alerts = await _check_oauth_expiration(db)
    alerts.extend(oauth_alerts)
    
    # 6. Check worker health
    worker_alerts = await _check_worker_health(db)
    alerts.extend(worker_alerts)
    
    # 7. Check campaign status
    campaign_alerts = await _check_campaign_status(db)
    alerts.extend(campaign_alerts)
    
    # 8. Check system health
    health_alerts = await _check_system_health(db)
    alerts.extend(health_alerts)
    
    # Save alerts to database (with deduplication)
    saved_alerts = []
    for alert_data in alerts:
        # Check for duplicate in last 5 minutes
        is_duplicate = await check_duplicate_alert(
            db,
            alert_data.alert_type,
            alert_data.severity,
            minutes_window=5
        )
        
        if not is_duplicate:
            alert_create = AlertCreate(
                alert_type=alert_data.alert_type,
                severity=alert_data.severity,
                message=alert_data.message,
                metadata=alert_data.metadata
            )
            saved_alert = await create_alert(db, alert_create)
            saved_alerts.append(saved_alert)
    
    return saved_alerts


async def _check_queue_saturation(db: AsyncSession) -> list[Alert]:
    """
    Check if publication queue is saturated.
    
    pending > 50 → critical
    pending > 20 → warning
    """
    alerts = []
    
    # Count pending publications
    query = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "pending"
    )
    result = await db.execute(query)
    pending_count = result.scalar() or 0
    
    if pending_count > 50:
        alerts.append(Alert(
            alert_type=AlertType.QUEUE_SATURATION,
            severity=AlertSeverity.CRITICAL,
            message=f"Queue is critically saturated with {pending_count} pending publications",
            metadata={
                "pending_count": pending_count,
                "threshold": 50,
                "severity_level": "critical"
            }
        ))
    elif pending_count > 20:
        alerts.append(Alert(
            alert_type=AlertType.QUEUE_SATURATION,
            severity=AlertSeverity.WARNING,
            message=f"Queue saturation warning: {pending_count} pending publications",
            metadata={
                "pending_count": pending_count,
                "threshold": 20,
                "severity_level": "warning"
            }
        ))
    
    return alerts


async def _check_scheduler_backlog(db: AsyncSession) -> list[Alert]:
    """
    Check if scheduler has overdue items.
    
    scheduled_for < now() and still scheduled → warning
    scheduled_for < now()-10min → critical
    """
    alerts = []
    now = datetime.utcnow()
    ten_min_ago = now - timedelta(minutes=10)
    
    # Check critically overdue (>10 minutes)
    query_critical = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.status == "pending",
            PublishLogModel.scheduled_for < ten_min_ago,
            PublishLogModel.scheduled_for.isnot(None)
        )
    )
    result = await db.execute(query_critical)
    critical_overdue = result.scalar() or 0
    
    if critical_overdue > 0:
        alerts.append(Alert(
            alert_type=AlertType.SCHEDULER_BACKLOG,
            severity=AlertSeverity.CRITICAL,
            message=f"Scheduler critically behind: {critical_overdue} items overdue by >10 minutes",
            metadata={
                "overdue_count": critical_overdue,
                "delay_minutes": 10,
                "severity_level": "critical"
            }
        ))
        return alerts
    
    # Check any overdue
    query_warning = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.status == "pending",
            PublishLogModel.scheduled_for < now,
            PublishLogModel.scheduled_for.isnot(None)
        )
    )
    result = await db.execute(query_warning)
    overdue_count = result.scalar() or 0
    
    if overdue_count > 0:
        alerts.append(Alert(
            alert_type=AlertType.SCHEDULER_BACKLOG,
            severity=AlertSeverity.WARNING,
            message=f"Scheduler backlog: {overdue_count} overdue publications",
            metadata={
                "overdue_count": overdue_count,
                "severity_level": "warning"
            }
        ))
    
    return alerts


async def _check_orchestrator_activity(db: AsyncSession) -> list[Alert]:
    """
    Check if orchestrator is inactive.
    
    No actions in > 2 min → warning
    No actions in > 5 min → critical
    """
    alerts = []
    
    # Get recent orchestrator events
    recent_events = await get_recent_events(
        db=db,
        event_type="orchestrator.action_executed",
        limit=1
    )
    
    if not recent_events:
        # No orchestrator events at all
        alerts.append(Alert(
            alert_type=AlertType.ORCHESTRATOR_INACTIVE,
            severity=AlertSeverity.CRITICAL,
            message="Orchestrator has never run or no actions recorded",
            metadata={
                "last_action": None,
                "severity_level": "critical"
            }
        ))
        return alerts
    
    last_event = recent_events[0]
    time_since_last = datetime.utcnow() - last_event.timestamp
    minutes_inactive = time_since_last.total_seconds() / 60
    
    if minutes_inactive > 5:
        alerts.append(Alert(
            alert_type=AlertType.ORCHESTRATOR_INACTIVE,
            severity=AlertSeverity.CRITICAL,
            message=f"Orchestrator critically inactive for {minutes_inactive:.1f} minutes",
            metadata={
                "minutes_inactive": minutes_inactive,
                "last_action": last_event.timestamp.isoformat(),
                "threshold_minutes": 5,
                "severity_level": "critical"
            }
        ))
    elif minutes_inactive > 2:
        alerts.append(Alert(
            alert_type=AlertType.ORCHESTRATOR_INACTIVE,
            severity=AlertSeverity.WARNING,
            message=f"Orchestrator inactive for {minutes_inactive:.1f} minutes",
            metadata={
                "minutes_inactive": minutes_inactive,
                "last_action": last_event.timestamp.isoformat(),
                "threshold_minutes": 2,
                "severity_level": "warning"
            }
        ))
    
    return alerts


async def _check_publish_failures(db: AsyncSession) -> list[Alert]:
    """
    Check for publish failure spikes.
    
    >5 failures in last 10min → warning
    >10 failures in last 10min → critical
    """
    alerts = []
    ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
    
    # Count recent failures
    query = select(func.count(PublishLogModel.id)).where(
        and_(
            PublishLogModel.status == "failed",
            PublishLogModel.created_at >= ten_min_ago
        )
    )
    result = await db.execute(query)
    failure_count = result.scalar() or 0
    
    if failure_count > 10:
        alerts.append(Alert(
            alert_type=AlertType.PUBLISH_FAILURES_SPIKE,
            severity=AlertSeverity.CRITICAL,
            message=f"Critical failure spike: {failure_count} publish failures in last 10 minutes",
            metadata={
                "failure_count": failure_count,
                "time_window_minutes": 10,
                "threshold": 10,
                "severity_level": "critical"
            }
        ))
    elif failure_count > 5:
        alerts.append(Alert(
            alert_type=AlertType.PUBLISH_FAILURES_SPIKE,
            severity=AlertSeverity.WARNING,
            message=f"Publish failure spike: {failure_count} failures in last 10 minutes",
            metadata={
                "failure_count": failure_count,
                "time_window_minutes": 10,
                "threshold": 5,
                "severity_level": "warning"
            }
        ))
    
    return alerts


async def _check_oauth_expiration(db: AsyncSession) -> list[Alert]:
    """
    Check for OAuth tokens expiring soon.
    
    expires_at < 20 min → warning
    expires_at < 5 min → critical
    """
    alerts = []
    now = datetime.utcnow()
    critical_threshold = now + timedelta(minutes=5)
    warning_threshold = now + timedelta(minutes=20)
    
    # Check for critically expiring tokens (<5 min)
    query_critical = select(SocialAccountModel).where(
        and_(
            SocialAccountModel.oauth_expires_at.isnot(None),
            SocialAccountModel.oauth_expires_at <= critical_threshold,
            SocialAccountModel.oauth_expires_at > now
        )
    )
    result = await db.execute(query_critical)
    critical_accounts = result.scalars().all()
    
    for account in critical_accounts:
        time_remaining = (account.oauth_expires_at - now).total_seconds() / 60
        alerts.append(Alert(
            alert_type=AlertType.OAUTH_EXPIRING_SOON,
            severity=AlertSeverity.CRITICAL,
            message=f"OAuth token for {account.platform} account expiring in {time_remaining:.1f} minutes",
            metadata={
                "account_id": account.id,
                "platform": account.platform,
                "expires_at": account.oauth_expires_at.isoformat() if account.oauth_expires_at else None,
                "minutes_remaining": time_remaining,
                "severity_level": "critical"
            }
        ))
    
    # Check for warning-level expiring tokens (<20 min)
    if not critical_accounts:  # Only if no critical alerts
        query_warning = select(SocialAccountModel).where(
            and_(
                SocialAccountModel.oauth_expires_at.isnot(None),
                SocialAccountModel.oauth_expires_at <= warning_threshold,
                SocialAccountModel.oauth_expires_at > critical_threshold
            )
        )
        result = await db.execute(query_warning)
        warning_accounts = result.scalars().all()
        
        for account in warning_accounts:
            time_remaining = (account.oauth_expires_at - now).total_seconds() / 60
            alerts.append(Alert(
                alert_type=AlertType.OAUTH_EXPIRING_SOON,
                severity=AlertSeverity.WARNING,
                message=f"OAuth token for {account.platform} account expiring in {time_remaining:.1f} minutes",
                metadata={
                    "account_id": account.id,
                    "platform": account.platform,
                    "expires_at": account.oauth_expires_at.isoformat() if account.oauth_expires_at else None,
                    "minutes_remaining": time_remaining,
                    "severity_level": "warning"
                }
            ))
    
    return alerts


async def _check_worker_health(db: AsyncSession) -> list[Alert]:
    """
    Check for worker crashes.
    
    If processing_time_ms = None for processing jobs → critical
    """
    alerts = []
    
    # Check for stuck processing jobs (simple heuristic)
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    
    query = select(Job).where(
        and_(
            Job.status == JobStatus.PROCESSING,
            Job.updated_at < five_min_ago
        )
    )
    result = await db.execute(query)
    stuck_jobs = result.scalars().all()
    
    if stuck_jobs:
        alerts.append(Alert(
            alert_type=AlertType.WORKER_CRASH_DETECTED,
            severity=AlertSeverity.CRITICAL,
            message=f"Worker crash detected: {len(stuck_jobs)} jobs stuck in processing for >5 minutes",
            metadata={
                "stuck_job_count": len(stuck_jobs),
                "stuck_job_ids": [str(job.id) for job in stuck_jobs[:5]],
                "severity_level": "critical"
            }
        ))
    
    return alerts


async def _check_campaign_status(db: AsyncSession) -> list[Alert]:
    """
    Check for blocked campaigns.
    
    clips = 0 but status = ACTIVE → warning
    """
    alerts = []
    
    # Get active campaigns with no ready clips
    query = select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    for campaign in campaigns:
        # Check if campaign has any clips
        # Note: This is a simplified check; in production you'd query ClipVariant
        # For now, we'll use a heuristic
        if hasattr(campaign, 'clips') and len(campaign.clips) == 0:
            alerts.append(Alert(
                alert_type=AlertType.CAMPAIGN_BLOCKED,
                severity=AlertSeverity.WARNING,
                message=f"Active campaign '{campaign.name}' has no clips available",
                metadata={
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "severity_level": "warning"
                }
            ))
    
    return alerts


async def _check_system_health(db: AsyncSession) -> list[Alert]:
    """
    Check overall system health.
    
    Multiple failures across subsystems → critical
    """
    alerts = []
    
    # This is a meta-check that looks at overall system state
    # Count total pending items across all subsystems
    
    # Count pending jobs
    query_jobs = select(func.count(Job.id)).where(Job.status == JobStatus.PENDING)
    result = await db.execute(query_jobs)
    pending_jobs = result.scalar() or 0
    
    # Count pending publications
    query_pubs = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "pending"
    )
    result = await db.execute(query_pubs)
    pending_pubs = result.scalar() or 0
    
    # Count failed items
    query_failed = select(func.count(PublishLogModel.id)).where(
        PublishLogModel.status == "failed"
    )
    result = await db.execute(query_failed)
    failed_pubs = result.scalar() or 0
    
    # Calculate health score
    total_items = pending_jobs + pending_pubs + failed_pubs
    health_issues = 0
    
    if pending_jobs > 10:
        health_issues += 1
    if pending_pubs > 30:
        health_issues += 1
    if failed_pubs > 20:
        health_issues += 1
    
    if health_issues >= 3:
        alerts.append(Alert(
            alert_type=AlertType.SYSTEM_HEALTH_DEGRADED,
            severity=AlertSeverity.CRITICAL,
            message="System health critically degraded across multiple subsystems",
            metadata={
                "pending_jobs": pending_jobs,
                "pending_publications": pending_pubs,
                "failed_publications": failed_pubs,
                "health_issues": health_issues,
                "severity_level": "critical"
            }
        ))
    elif health_issues >= 2:
        alerts.append(Alert(
            alert_type=AlertType.SYSTEM_HEALTH_DEGRADED,
            severity=AlertSeverity.WARNING,
            message="System health degraded in multiple areas",
            metadata={
                "pending_jobs": pending_jobs,
                "pending_publications": pending_pubs,
                "failed_publications": failed_pubs,
                "health_issues": health_issues,
                "severity_level": "warning"
            }
        ))
    
    return alerts
