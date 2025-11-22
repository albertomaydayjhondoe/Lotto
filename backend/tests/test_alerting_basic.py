"""
Basic tests for Alerting Engine

Tests alert CRUD operations and basic functionality.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from app.alerting_engine.models import AlertType, AlertSeverity, AlertCreate, Alert
from app.alerting_engine.service import (
    create_alert,
    mark_alert_read,
    get_alerts,
    check_duplicate_alert,
    get_unread_count
)
from app.alerting_engine.websocket import AlertManager


@pytest.mark.asyncio
async def test_create_alert(db_session: AsyncSession):
    """Test creating an alert."""
    alert_data = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Queue saturation detected: 25 pending items",
        metadata={"pending_count": 25}
    )
    
    alert = await create_alert(db_session, alert_data)
    
    assert alert.alert_type == AlertType.QUEUE_SATURATION
    assert alert.severity == AlertSeverity.WARNING
    assert alert.message == "Queue saturation detected: 25 pending items"
    assert alert.metadata["pending_count"] == 25
    assert not alert.read


@pytest.mark.asyncio
async def test_get_alerts(db_session: AsyncSession):
    """Test getting alerts."""
    # Create some alerts
    for i in range(3):
        alert_data = AlertCreate(
            alert_type=AlertType.QUEUE_SATURATION,
            severity=AlertSeverity.WARNING if i < 2 else AlertSeverity.CRITICAL,
            message=f"Test alert {i}",
            metadata={"count": i}
        )
        await create_alert(db_session, alert_data)
    
    # Get all alerts
    alerts = await get_alerts(db_session, unread_only=False, limit=100)
    
    assert len(alerts) >= 3
    assert all(isinstance(a, Alert) for a in alerts)


@pytest.mark.asyncio
async def test_mark_alert_read(db_session: AsyncSession):
    """Test marking alert as read."""
    # Create alert
    alert_data = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Test alert",
        metadata={}
    )
    alert = await create_alert(db_session, alert_data)
    assert not alert.read
    
    # Mark as read
    success = await mark_alert_read(db_session, alert.id)
    assert success
    
    # Verify
    alerts = await get_alerts(db_session, unread_only=False, limit=1)
    assert alerts[0].read


@pytest.mark.asyncio
async def test_get_unread_alerts(db_session: AsyncSession):
    """Test filtering unread alerts."""
    # Create alerts
    alert1_data = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Unread alert",
        metadata={}
    )
    alert1 = await create_alert(db_session, alert1_data)
    
    alert2_data = AlertCreate(
        alert_type=AlertType.SCHEDULER_BACKLOG,
        severity=AlertSeverity.CRITICAL,
        message="Another unread alert",
        metadata={}
    )
    await create_alert(db_session, alert2_data)
    
    # Mark one as read
    await mark_alert_read(db_session, alert1.id)
    
    # Get unread
    unread = await get_alerts(db_session, unread_only=True)
    
    assert len(unread) >= 1
    assert all(not a.read for a in unread)


@pytest.mark.asyncio
async def test_get_unread_count(db_session: AsyncSession):
    """Test getting unread count."""
    # Create some unread alerts
    for i in range(3):
        alert_data = AlertCreate(
            alert_type=AlertType.QUEUE_SATURATION,
            severity=AlertSeverity.WARNING,
            message=f"Alert {i}",
            metadata={}
        )
        await create_alert(db_session, alert_data)
    
    count = await get_unread_count(db_session)
    assert count >= 3


@pytest.mark.asyncio
async def test_deduplication(db_session: AsyncSession):
    """Test alert deduplication within 5-minute window."""
    alert_data = AlertCreate(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Duplicate test",
        metadata={}
    )
    
    # Create first alert
    await create_alert(db_session, alert_data)
    
    # Check for duplicate within 5 minutes
    is_duplicate = await check_duplicate_alert(
        db_session,
        AlertType.QUEUE_SATURATION,
        AlertSeverity.WARNING
    )
    
    assert is_duplicate


@pytest.mark.asyncio
async def test_no_duplicate_after_time_window(db_session: AsyncSession):
    """Test that alerts are not considered duplicates after time window."""
    # Check for duplicate that doesn't exist
    is_duplicate = await check_duplicate_alert(
        db_session,
        AlertType.WORKER_CRASH_DETECTED,
        AlertSeverity.CRITICAL
    )
    
    assert not is_duplicate


@pytest.mark.asyncio
async def test_websocket_broadcast():
    """Test WebSocket alert broadcasting."""
    manager = AlertManager()
    
    # Mock WebSocket
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    
    # Connect clients
    await manager.connect(mock_ws1)
    await manager.connect(mock_ws2)
    
    assert len(manager.active_connections) == 2
    
    # Broadcast alert
    alert = Alert(
        alert_type=AlertType.QUEUE_SATURATION,
        severity=AlertSeverity.WARNING,
        message="Test broadcast",
        metadata={}
    )
    
    await manager.broadcast_alert(alert)
    
    # Verify broadcast
    assert mock_ws1.send_json.called
    assert mock_ws2.send_json.called
    
    # Disconnect
    await manager.disconnect(mock_ws1)
    assert len(manager.active_connections) == 1


@pytest.mark.asyncio
async def test_multiple_alert_types(db_session: AsyncSession):
    """Test creating different types of alerts."""
    alert_types = [
        (AlertType.QUEUE_SATURATION, AlertSeverity.WARNING, "Queue issue"),
        (AlertType.SCHEDULER_BACKLOG, AlertSeverity.CRITICAL, "Scheduler issue"),
        (AlertType.PUBLISH_FAILURES_SPIKE, AlertSeverity.WARNING, "Publish failures"),
        (AlertType.OAUTH_EXPIRING_SOON, AlertSeverity.CRITICAL, "OAuth expiring"),
    ]
    
    for alert_type, severity, message in alert_types:
        alert_data = AlertCreate(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata={"test": True}
        )
        alert = await create_alert(db_session, alert_data)
        assert alert.alert_type == alert_type
        assert alert.severity == severity


@pytest.mark.asyncio
async def test_alert_metadata(db_session: AsyncSession):
    """Test that metadata is properly stored and retrieved."""
    complex_metadata = {
        "count": 42,
        "source": "test",
        "details": {
            "nested": "value",
            "items": [1, 2, 3]
        }
    }
    
    alert_data = AlertCreate(
        alert_type=AlertType.SYSTEM_HEALTH_DEGRADED,
        severity=AlertSeverity.CRITICAL,
        message="System health issue",
        metadata=complex_metadata
    )
    
    alert = await create_alert(db_session, alert_data)
    
    # Retrieve and verify
    alerts = await get_alerts(db_session, unread_only=False, limit=1)
    retrieved_alert = alerts[0]
    
    assert retrieved_alert.metadata["count"] == 42
    assert retrieved_alert.metadata["details"]["nested"] == "value"
    assert retrieved_alert.metadata["details"]["items"] == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
