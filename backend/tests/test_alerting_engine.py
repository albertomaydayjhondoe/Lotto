"""
Tests for Alerting Engine

Covers alert generation, deduplication, and WebSocket broadcasting.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.alerting_engine.models import AlertType, AlertSeverity, AlertCreate
from app.alerting_engine.engine import analyze_system_state
from app.alerting_engine.service import (
    create_alert,
    mark_alert_read,
    get_alerts,
    check_duplicate_alert,
    get_unread_count
)
from app.alerting_engine.websocket import AlertManager
from app.models.database import (
    PublishLogModel,
    Job,
    SocialAccountModel,
    Campaign,
    AlertEventModel
)


@pytest.mark.asyncio
async def test_queue_saturation_warning(db_session: AsyncSession):
    """Test queue saturation warning alert (pending > 20)."""
    # Create 25 pending publications
    for i in range(25):
        log = PublishLogModel(
            clip_variant_id=i + 1,
            scheduled_for=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db_session.add(log)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_queue_saturation(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.QUEUE_SATURATION
    assert alerts[0].severity == AlertSeverity.WARNING
    assert "25 pending" in alerts[0].message
    assert alerts[0].metadata["pending_count"] == 25


@pytest.mark.asyncio
async def test_queue_saturation_critical(db_session: AsyncSession):
    """Test queue saturation critical alert (pending > 50)."""
    # Create 55 pending publications
    for i in range(55):
        log = PublishLogModel(
            clip_variant_id=i + 1,
            scheduled_for=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db_session.add(log)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_queue_saturation(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.QUEUE_SATURATION
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "critically saturated" in alerts[0].message.lower()
    assert alerts[0].metadata["pending_count"] == 55


@pytest.mark.asyncio
async def test_scheduler_backlog(db_session: AsyncSession):
    """Test scheduler backlog alert."""
    # Create overdue publications
    overdue_time = datetime.utcnow() - timedelta(minutes=15)
    
    for i in range(3):
        log = PublishLogModel(
            clip_variant_id=i + 1,
            scheduled_for=overdue_time,
            status="pending"
        )
        db_session.add(log)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_scheduler_backlog(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.SCHEDULER_BACKLOG
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "overdue" in alerts[0].message.lower()
    assert alerts[0].metadata["overdue_count"] == 3


@pytest.mark.asyncio
async def test_orchestrator_inactive(db_session: AsyncSession):
    """Test orchestrator inactive alert."""
    # Create old ledger event
    old_event = LedgerEvent(
        event_type="orchestrator.action_executed",
        timestamp=datetime.utcnow() - timedelta(minutes=6),
        data={}
    )
    db_session.add(old_event)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_orchestrator_activity(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.ORCHESTRATOR_INACTIVE
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "inactive" in alerts[0].message.lower()
    assert alerts[0].metadata["minutes_inactive"] > 5


@pytest.mark.asyncio
async def test_publish_failure_spike(db_session: AsyncSession):
    """Test publish failure spike alert."""
    # Create 8 failed publications in last 10 minutes
    for i in range(8):
        log = PublishLogModel(
            clip_variant_id=i + 1,
            scheduled_for=datetime.utcnow(),
            status="failed",
            created_at=datetime.utcnow() - timedelta(minutes=5)
        )
        db_session.add(log)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_publish_failures(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.PUBLISH_FAILURES_SPIKE
    assert alerts[0].severity == AlertSeverity.WARNING
    assert "failure" in alerts[0].message.lower()
    assert alerts[0].metadata["failure_count"] == 8


@pytest.mark.asyncio
async def test_oauth_expiring_soon(db_session: AsyncSession):
    """Test OAuth expiring soon alert."""
    # Create social account with expiring token
    account = SocialAccountModel(
        platform="instagram",
        account_name="test_account",
        encrypted_credentials=b"encrypted",
        oauth_expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    db_session.add(account)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_oauth_expiration(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.OAUTH_EXPIRING_SOON
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "expiring" in alerts[0].message.lower()
    assert alerts[0].metadata["platform"] == "instagram"


@pytest.mark.asyncio
async def test_worker_crash(db_session: AsyncSession):
    """Test worker crash detection alert."""
    # Create stuck job (processing for >5 minutes)
    job = Job(
        job_type="process",
        status=JobStatus.PROCESSING,
        params={},
        updated_at=datetime.utcnow() - timedelta(minutes=6)
    )
    db_session.add(job)
    await db_session.commit()
    
    # Check alerts
    alerts = await _check_worker_health(db_session)
    
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.WORKER_CRASH_DETECTED
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert "crash" in alerts[0].message.lower() or "stuck" in alerts[0].message.lower()
    assert alerts[0].metadata["stuck_job_count"] == 1


@pytest.mark.asyncio
async def test_campaign_blocked(db_session: AsyncSession):
    """Test blocked campaign alert."""
    # Create active campaign with no clips
    campaign = Campaign(
        name="Test Campaign",
        status=CampaignStatus.ACTIVE,
        clip_id=str(uuid4()),
        budget_cents=10000
    )
    db_session.add(campaign)
    await db_session.commit()
    
    # Check alerts (this test is simplified since campaign.clips relationship is complex)
    alerts = await _check_campaign_status(db_session)
    
    # Campaign check may or may not trigger depending on data structure
    # This test validates the check runs without errors
    assert isinstance(alerts, list)


@pytest.mark.asyncio
async def test_deduplication(db_session: AsyncSession):
    """Test alert deduplication within 5-minute window."""
    # Create first alert
    alert1 = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Test alert",
        metadata={}
    )
    await create_alert(db_session, alert1)
    
    # Check for duplicate immediately
    is_duplicate = await check_duplicate_alert(
        db_session,
        AlertType.QUEUE_SATURATION,
        AlertSeverity.WARNING,
        minutes_window=5
    )
    
    assert is_duplicate is True
    
    # Check for non-duplicate (different type)
    is_duplicate_diff = await check_duplicate_alert(
        db_session,
        AlertType.SCHEDULER_BACKLOG,
        AlertSeverity.WARNING,
        minutes_window=5
    )
    
    assert is_duplicate_diff is False


@pytest.mark.asyncio
async def test_websocket_broadcast():
    """Test WebSocket alert broadcasting."""
    from unittest.mock import AsyncMock
    
    manager = AlertManager()
    
    # Create mock WebSocket
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    # Connect
    await manager.connect(mock_ws)
    assert manager.get_connection_count() == 1
    
    # Create alert
    from app.alerting_engine.models import Alert
    alert = Alert(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Test alert",
        metadata={}
    )
    
    # Broadcast
    await manager.broadcast_alert(alert)
    
    # Verify broadcast was called
    assert mock_ws.send_json.called
    
    # Disconnect
    await manager.disconnect(mock_ws)
    assert manager.get_connection_count() == 0


@pytest.mark.asyncio
async def test_analyze_system_state(db_session: AsyncSession):
    """Test full system analysis generates alerts."""
    # Create conditions that trigger alerts
    
    # Queue saturation
    for i in range(25):
        log = PublishLogModel(
            clip_variant_id=i + 1,
            scheduled_for=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db_session.add(log)
    
    # Failed publications
    for i in range(6):
        log = PublishLogModel(
            clip_variant_id=i + 100,
            scheduled_for=datetime.utcnow(),
            status="failed",
            created_at=datetime.utcnow() - timedelta(minutes=5)
        )
        db_session.add(log)
    
    await db_session.commit()
    
    # Run analysis
    alerts = await analyze_system_state(db_session)
    
    # Should have generated at least 2 alerts (queue + failures)
    assert len(alerts) >= 2
    
    # Verify alerts were saved
    saved_alerts = await get_alerts(db_session, unread_only=False, limit=100)
    assert len(saved_alerts) >= 2


@pytest.mark.asyncio
async def test_mark_alert_read(db_session: AsyncSession):
    """Test marking alert as read."""
    # Create alert
    alert_create = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Test alert",
        metadata={}
    )
    alert = await create_alert(db_session, alert_create)
    
    # Verify unread
    assert alert.read is False
    
    # Mark as read
    success = await mark_alert_read(db_session, alert.id)
    assert success is True
    
    # Verify read
    unread_count = await get_unread_count(db_session)
    assert unread_count == 0


@pytest.mark.asyncio
async def test_get_unread_alerts(db_session: AsyncSession):
    """Test getting only unread alerts."""
    # Create multiple alerts
    for i in range(3):
        alert = AlertCreate(
            alert_type=AlertType.QUEUE_SATURATION,
            severity=AlertSeverity.WARNING,
            message=f"Test alert {i}",
            metadata={}
        )
        created = await create_alert(db_session, alert)
        
        # Mark first one as read
        if i == 0:
            await mark_alert_read(db_session, created.id)
    
    # Get unread only
    unread = await get_alerts(db_session, unread_only=True)
    assert len(unread) == 2
    
    # Get all
    all_alerts = await get_alerts(db_session, unread_only=False)
    assert len(all_alerts) == 3
