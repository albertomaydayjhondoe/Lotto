"""
Tests for Live Telemetry

Tests telemetry models, collector, manager, and WebSocket endpoint.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.live_telemetry.models import (
    TelemetryPayload,
    QueueStats,
    SchedulerStats,
    OrchestratorStats,
    PlatformStats,
    WorkerStats
)
from app.live_telemetry.collector import gather_metrics
from app.live_telemetry.telemetry_manager import TelemetryManager
from app.models.database import PublishLogModel, ClipVariant, Job, JobStatus


@pytest.mark.asyncio
async def test_telemetry_payload_shape():
    """Test that TelemetryPayload has correct structure."""
    payload = TelemetryPayload(
        queue=QueueStats(pending=5, processing=2, success=10, failed=1, total=18),
        scheduler=SchedulerStats(scheduled_today=3, scheduled_next_hour=1, overdue=0),
        orchestrator=OrchestratorStats(actions_last_minute=2, decisions_pending=1),
        platforms=PlatformStats(instagram=5, tiktok=3, youtube=2, facebook=1),
        workers=WorkerStats(active_workers=2, tasks_processing=2),
        timestamp=datetime.utcnow()
    )
    
    # Validate structure
    assert payload.queue.pending >= 0
    assert payload.queue.total >= 0
    assert payload.scheduler.scheduled_today >= 0
    assert payload.orchestrator.actions_last_minute >= 0
    assert payload.platforms.instagram >= 0
    assert payload.workers.active_workers >= 0
    assert isinstance(payload.timestamp, datetime)
    
    # Validate JSON serialization
    json_data = payload.model_dump(mode='json')
    assert 'queue' in json_data
    assert 'scheduler' in json_data
    assert 'orchestrator' in json_data
    assert 'platforms' in json_data
    assert 'workers' in json_data
    assert 'timestamp' in json_data
    
    # Validate JSON is serializable
    import json
    json_str = json.dumps(json_data)
    assert len(json_str) > 0


@pytest.mark.asyncio
async def test_collector_basic_metrics(db_session: AsyncSession):
    """Test that collector returns valid metrics structure."""
    # Collect metrics from empty database
    payload = await gather_metrics(db_session)
    
    # Validate all required fields are present
    assert payload.queue is not None
    assert payload.scheduler is not None
    assert payload.orchestrator is not None
    assert payload.platforms is not None
    assert payload.workers is not None
    assert payload.timestamp is not None
    
    # Validate all metrics are non-negative
    assert payload.queue.pending >= 0
    assert payload.queue.processing >= 0
    assert payload.queue.success >= 0
    assert payload.queue.failed >= 0
    assert payload.queue.total >= 0
    
    assert payload.scheduler.scheduled_today >= 0
    assert payload.scheduler.scheduled_next_hour >= 0
    assert payload.scheduler.overdue >= 0
    
    assert payload.orchestrator.actions_last_minute >= 0
    assert payload.orchestrator.decisions_pending >= 0
    
    assert payload.platforms.instagram >= 0
    assert payload.platforms.tiktok >= 0
    assert payload.platforms.youtube >= 0
    assert payload.platforms.facebook >= 0
    
    assert payload.workers.active_workers >= 0
    assert payload.workers.tasks_processing >= 0


@pytest.mark.asyncio
async def test_telemetry_manager_connection():
    """Test TelemetryManager connection management."""
    from unittest.mock import AsyncMock
    
    manager = TelemetryManager()
    
    # Create mock WebSocket
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    # Initially no connections
    assert manager.get_connection_count() == 0
    assert not manager.has_subscribers()
    
    # Connect WebSocket
    await manager.connect(mock_ws)
    
    # Should have 1 connection
    assert manager.get_connection_count() == 1
    assert manager.has_subscribers()
    assert mock_ws.accept.called
    
    # Disconnect
    await manager.disconnect(mock_ws)
    
    # Should have 0 connections
    assert manager.get_connection_count() == 0
    assert not manager.has_subscribers()


@pytest.mark.asyncio
async def test_telemetry_manager_broadcast():
    """Test TelemetryManager broadcasts to all connections."""
    from unittest.mock import AsyncMock
    
    manager = TelemetryManager()
    
    # Create 3 mock WebSockets
    mock_ws1 = AsyncMock()
    mock_ws1.accept = AsyncMock()
    mock_ws1.send_json = AsyncMock()
    
    mock_ws2 = AsyncMock()
    mock_ws2.accept = AsyncMock()
    mock_ws2.send_json = AsyncMock()
    
    mock_ws3 = AsyncMock()
    mock_ws3.accept = AsyncMock()
    mock_ws3.send_json = AsyncMock()
    
    # Connect all 3
    await manager.connect(mock_ws1)
    await manager.connect(mock_ws2)
    await manager.connect(mock_ws3)
    
    assert manager.get_connection_count() == 3
    
    # Create payload
    payload = TelemetryPayload(
        queue=QueueStats(pending=1, processing=0, success=5, failed=0, total=6),
        scheduler=SchedulerStats(scheduled_today=2, scheduled_next_hour=1, overdue=0),
        orchestrator=OrchestratorStats(actions_last_minute=3, decisions_pending=0),
        platforms=PlatformStats(instagram=2, tiktok=1, youtube=1, facebook=0),
        workers=WorkerStats(active_workers=1, tasks_processing=0),
        timestamp=datetime.utcnow()
    )
    
    # Broadcast
    await manager.broadcast(payload)
    
    # All 3 should have received the message
    assert mock_ws1.send_json.called
    assert mock_ws2.send_json.called
    assert mock_ws3.send_json.called


@pytest.mark.asyncio
async def test_telemetry_manager_removes_dead_connections():
    """Test that TelemetryManager removes connections that fail to send."""
    from unittest.mock import AsyncMock
    
    manager = TelemetryManager()
    
    # Create 1 working and 1 broken WebSocket
    mock_ws_working = AsyncMock()
    mock_ws_working.accept = AsyncMock()
    mock_ws_working.send_json = AsyncMock()
    
    mock_ws_broken = AsyncMock()
    mock_ws_broken.accept = AsyncMock()
    mock_ws_broken.send_json = AsyncMock(side_effect=Exception("Connection closed"))
    
    # Connect both
    await manager.connect(mock_ws_working)
    await manager.connect(mock_ws_broken)
    
    assert manager.get_connection_count() == 2
    
    # Create payload
    payload = TelemetryPayload(
        queue=QueueStats(pending=0, processing=0, success=0, failed=0, total=0),
        scheduler=SchedulerStats(scheduled_today=0, scheduled_next_hour=0, overdue=0),
        orchestrator=OrchestratorStats(actions_last_minute=0, decisions_pending=0),
        platforms=PlatformStats(instagram=0, tiktok=0, youtube=0, facebook=0),
        workers=WorkerStats(active_workers=0, tasks_processing=0),
        timestamp=datetime.utcnow()
    )
    
    # Broadcast (should remove broken connection)
    await manager.broadcast(payload)
    
    # Should have 1 connection left (the working one)
    assert manager.get_connection_count() == 1
    assert manager.has_subscribers()


@pytest.mark.asyncio
async def test_collector_reads_real_queue(db_session: AsyncSession):
    """Test that collector reads actual queue data from database."""
    # Create some test data
    log1 = PublishLogModel(
        clip_variant_id=1,
        scheduled_for=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    log2 = PublishLogModel(
        clip_variant_id=2,
        scheduled_for=datetime.utcnow() + timedelta(hours=2),
        status="pending"
    )
    log3 = PublishLogModel(
        clip_variant_id=3,
        scheduled_for=datetime.utcnow() - timedelta(hours=1),
        status="success",
        published_at=datetime.utcnow()
    )
    
    db_session.add(log1)
    db_session.add(log2)
    db_session.add(log3)
    await db_session.commit()
    
    # Collect metrics
    payload = await gather_metrics(db_session)
    
    # Validate queue stats reflect the data
    assert payload.queue.pending == 2
    assert payload.queue.success == 1
    assert payload.queue.total == 3
    
    # Validate scheduler stats
    assert payload.scheduler.scheduled_today >= 2  # At least the 2 we created
    assert payload.scheduler.scheduled_next_hour >= 1  # At least 1 in next hour
