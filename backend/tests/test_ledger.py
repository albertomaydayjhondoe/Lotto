"""
Tests for the Ledger system.

Tests cover:
- Basic event logging
- Job event logging
- Clip event logging
- Ledger endpoint functionality
- Graceful failure handling (never breaks flow)
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.models.database import VideoAsset, Job, JobStatus, Clip, ClipStatus
from app.ledger import log_event, log_job_event, log_clip_event, get_recent_events, get_total_events
from app.ledger.models import LedgerEvent, EventSeverity
from tests.test_db import init_test_db, drop_test_db, get_test_session
from app.core.database import get_db


# Override dependency for testing
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_environment():
    """Setup test database and override dependencies"""
    # Initialize test database
    await init_test_db()
    
    # Override get_db dependency
    app.dependency_overrides[get_db] = get_test_session
    
    yield
    
    # Cleanup
    app.dependency_overrides.clear()
    await drop_test_db()


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def client():
    """Provide an async HTTP client for API tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_log_event_basic(db_session: AsyncSession):
    """Test that basic event logging works."""
    # Log a basic event
    event = await log_event(
        db=db_session,
        event_type="test_event",
        entity_type="test_entity",
        entity_id="test_123",
        metadata={"key": "value", "number": 42},
        severity="INFO"
    )
    
    # Commit to persist
    await db_session.commit()
    
    # Verify event was created
    assert event is not None
    assert event.event_type == "test_event"
    assert event.entity_type == "test_entity"
    assert event.entity_id == "test_123"
    assert event.event_data == {"key": "value", "number": 42}
    assert event.severity == EventSeverity.INFO
    assert event.timestamp is not None
    
    # Verify it's in the database
    result = await db_session.execute(
        select(LedgerEvent).where(LedgerEvent.id == event.id)
    )
    db_event = result.scalar_one_or_none()
    
    assert db_event is not None
    assert db_event.event_type == "test_event"
    
    print(f"✓ TEST PASSED - Basic event logged - id: {event.id}")


@pytest.mark.asyncio
async def test_log_job_event_creates_entry(db_session: AsyncSession):
    """Test that log_job_event creates a ledger entry."""
    # Create a test video asset and job
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/tmp/test.mp4",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video_asset)
    
    job = Job(
        id=uuid4(),
        job_type="cut_analysis",
        status=JobStatus.PENDING,
        video_asset_id=video_asset.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(job)
    await db_session.flush()
    
    # Log job event
    event = await log_job_event(
        db=db_session,
        job_id=job.id,
        event_type="job_created",
        metadata={"job_type": "cut_analysis"}
    )
    
    await db_session.commit()
    
    # Verify event
    assert event is not None
    assert event.event_type == "job_created"
    assert event.entity_type == "job"
    assert event.entity_id == str(job.id)
    assert event.job_id == job.id
    assert event.event_data["job_type"] == "cut_analysis"
    
    print(f"✓ TEST PASSED - Job event logged - job_id: {job.id}")


@pytest.mark.asyncio
async def test_log_clip_event_creates_entry(db_session: AsyncSession):
    """Test that log_clip_event creates a ledger entry."""
    # Create test data
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/tmp/test.mp4",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video_asset)
    
    clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=0,
        end_ms=10000,
        duration_ms=10000,
        visual_score=0.85,
        status=ClipStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(clip)
    await db_session.flush()
    
    # Log clip event
    event = await log_clip_event(
        db=db_session,
        clip_id=clip.id,
        event_type="clip_created",
        metadata={
            "start_ms": 0,
            "end_ms": 10000,
            "visual_score": 0.85
        }
    )
    
    await db_session.commit()
    
    # Verify event
    assert event is not None
    assert event.event_type == "clip_created"
    assert event.entity_type == "clip"
    assert event.entity_id == str(clip.id)
    assert event.clip_id == clip.id
    assert event.event_data["visual_score"] == 0.85
    
    print(f"✓ TEST PASSED - Clip event logged - clip_id: {clip.id}")


@pytest.mark.asyncio
async def test_ledger_endpoint_returns_recent_items(client: AsyncClient, db_session: AsyncSession):
    """Test that GET /debug/ledger/recent returns recent events."""
    # Create multiple test events
    for i in range(10):
        await log_event(
            db=db_session,
            event_type=f"test_event_{i}",
            entity_type="test",
            entity_id=f"test_{i}",
            metadata={"index": i}
        )
    
    await db_session.commit()
    
    # Call endpoint
    response = await client.get("/debug/ledger/recent?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "events" in data
    assert "total" in data
    assert "limit" in data
    
    # Verify data
    assert len(data["events"]) <= 5
    assert data["limit"] == 5
    assert data["total"] >= 10
    
    # Verify event structure
    if len(data["events"]) > 0:
        event = data["events"][0]
        assert "id" in event
        assert "timestamp" in event
        assert "event_type" in event
        assert "entity_type" in event
        assert "entity_id" in event
        assert "metadata" in event
        assert "severity" in event
    
    print(f"✓ TEST PASSED - Ledger endpoint returned {len(data['events'])} events")


@pytest.mark.asyncio
async def test_ledger_graceful_failure_does_not_break_flow(db_session: AsyncSession):
    """
    Test that ledger failures are graceful and don't break application flow.
    
    If ledger logging fails (e.g., due to invalid data or DB issues),
    it should return None and log the error, but NOT raise an exception.
    """
    # This should not raise an exception even with invalid severity
    event = await log_event(
        db=db_session,
        event_type="test_event",
        entity_type="test",
        entity_id="test_123",
        metadata={"test": "data"},
        severity="INVALID_SEVERITY"  # This will cause an error
    )
    
    # Should return None on failure
    assert event is None
    
    # Application flow should continue normally
    # (no exception raised)
    
    print("✓ TEST PASSED - Ledger graceful failure handling works")


@pytest.mark.asyncio
async def test_ledger_query_functions(db_session: AsyncSession):
    """Test ledger query utility functions."""
    # Create test events
    job_id = uuid4()
    
    await log_event(
        db=db_session,
        event_type="test_query_event_1",
        entity_type="test",
        entity_id="test_1",
        job_id=job_id
    )
    
    await log_event(
        db=db_session,
        event_type="test_query_event_2",
        entity_type="test",
        entity_id="test_2",
        job_id=job_id
    )
    
    await db_session.commit()
    
    # Test get_recent_events
    recent = await get_recent_events(db_session, limit=10)
    assert len(recent) >= 2
    assert isinstance(recent[0], LedgerEvent)
    
    # Test get_total_events
    total = await get_total_events(db_session)
    assert total >= 2
    
    print(f"✓ TEST PASSED - Query functions work - total events: {total}")


@pytest.mark.asyncio
async def test_ledger_with_different_severities(db_session: AsyncSession):
    """Test logging events with different severity levels."""
    # Log INFO event
    info_event = await log_event(
        db=db_session,
        event_type="info_event",
        entity_type="test",
        entity_id="test_info",
        severity="INFO"
    )
    
    # Log WARN event
    warn_event = await log_event(
        db=db_session,
        event_type="warn_event",
        entity_type="test",
        entity_id="test_warn",
        severity="WARN"
    )
    
    # Log ERROR event
    error_event = await log_event(
        db=db_session,
        event_type="error_event",
        entity_type="test",
        entity_id="test_error",
        severity="ERROR"
    )
    
    await db_session.commit()
    
    # Verify severities
    assert info_event.severity == EventSeverity.INFO
    assert warn_event.severity == EventSeverity.WARN
    assert error_event.severity == EventSeverity.ERROR
    
    print("✓ TEST PASSED - Different severity levels work correctly")
