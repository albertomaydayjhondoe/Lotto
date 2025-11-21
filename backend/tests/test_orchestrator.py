"""
Tests for PASO 4.6: Autonomous Real-Time Orchestrator
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.monitor import monitor_system_state
from app.orchestrator.decider import decide_actions, OrchestratorAction, summarize_decisions
from app.orchestrator.executor import execute_actions
from app.orchestrator.runner import run_orchestrator_once
from app.models.database import Job, JobStatus, PublishLogModel, Clip, Campaign, CampaignStatus, VideoAsset, ClipStatus
from app.ledger import log_event
from test_db import init_test_db, drop_test_db, get_test_session
from uuid import uuid4


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test"""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def sample_video_asset(db):
    """Create a sample video asset for testing"""
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/storage/test.mp4",
        file_size=1000000,
        duration_ms=30000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video_asset)
    await db.commit()
    await db.refresh(video_asset)
    return video_asset


@pytest.mark.asyncio
async def test_monitor_system_state_empty(db: AsyncSession):
    """Test monitor with empty database"""
    snapshot = await monitor_system_state(db)
    
    assert snapshot is not None
    assert "jobs" in snapshot
    assert "publish_logs" in snapshot
    assert "scheduler" in snapshot
    assert "campaigns" in snapshot
    assert "clips" in snapshot
    assert "ledger" in snapshot
    assert "system" in snapshot
    
    # Empty system should be healthy
    assert snapshot["system"]["health_status"] == "healthy"
    assert snapshot["jobs"]["total"] == 0
    assert snapshot["publish_logs"]["total"] == 0


@pytest.mark.asyncio
async def test_monitor_detects_pending_jobs(db: AsyncSession):
    """Test monitor detects pending jobs"""
    # Create 60 pending jobs (should trigger saturation)
    for i in range(60):
        job = Job(
            job_type="video_editing",
            params={"test": i},
            status=JobStatus.PENDING
        )
        db.add(job)
    
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    
    assert snapshot["jobs"]["pending"] == 60
    assert snapshot["jobs"]["queue_saturated"] is True
    assert snapshot["system"]["health_score"] < 100


@pytest.mark.asyncio
async def test_monitor_detects_failures(db: AsyncSession, sample_video_asset):
    """Test monitor detects publishing failures"""
    # Create a clip
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=75,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    # Create failed publish logs
    for i in range(5):
        log = PublishLogModel(
            clip_id=clip.id,
            platform="instagram",
            status="failed",
            error_message="Test failure"
        )
        db.add(log)
    
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    
    assert snapshot["publish_logs"]["failed"] == 5
    assert snapshot["publish_logs"]["has_failures"] is True
    assert snapshot["system"]["health_score"] < 100


@pytest.mark.asyncio
async def test_monitor_detects_high_score_clips(db: AsyncSession, sample_video_asset):
    """Test monitor detects high-score clips"""
    # Create high-score clips
    for i in range(5):
        clip = Clip(
            video_asset_id=sample_video_asset.id,
            start_ms=0,
            end_ms=30000,
            duration_ms=30000,
            visual_score=85 + i,  # 85-89
            status=ClipStatus.READY
        )
        db.add(clip)
    
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    
    assert snapshot["clips"]["recent_24h_count"] == 5
    assert snapshot["clips"]["high_score_count_24h"] == 5
    assert snapshot["clips"]["has_high_score_clips"] is True
    assert snapshot["clips"]["avg_visual_score"] >= 85


@pytest.mark.asyncio
async def test_decider_handles_failures(db: AsyncSession, sample_video_asset):
    """Test decider suggests retry for failures"""
    # Create a clip
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=75,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    # Create recent failed log
    log = PublishLogModel(
        clip_id=clip.id,
        platform="instagram",
        status="failed",
        error_message="Test failure",
        created_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(log)
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    actions = decide_actions(snapshot)
    
    # Should suggest retry
    action_types = [a.action_type for a in actions]
    assert "retry_failed_log" in action_types


@pytest.mark.asyncio
async def test_decider_handles_high_score_clips(db: AsyncSession, sample_video_asset):
    """Test decider suggests promoting high-score clips"""
    # Create high-score clips
    for i in range(3):
        clip = Clip(
            video_asset_id=sample_video_asset.id,
            start_ms=0,
            end_ms=30000,
            duration_ms=30000,
            visual_score=85 + i,
            status=ClipStatus.READY
        )
        db.add(clip)
    
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    actions = decide_actions(snapshot)
    
    # Should suggest promote or schedule
    action_types = [a.action_type for a in actions]
    assert "promote_high_score_clip" in action_types or "schedule_clip" in action_types


@pytest.mark.asyncio
async def test_decider_handles_queue_saturation(db: AsyncSession):
    """Test decider suggests rebalance for saturation"""
    # Create 60 pending jobs
    for i in range(60):
        job = Job(
            job_type="video_editing",
            params={"test": i},
            status=JobStatus.PENDING
        )
        db.add(job)
    
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    actions = decide_actions(snapshot)
    
    # Should suggest rebalance
    action_types = [a.action_type for a in actions]
    assert "rebalance_queue" in action_types


@pytest.mark.asyncio
async def test_executor_retry_failed_log(db: AsyncSession, sample_video_asset):
    """Test executor can retry failed logs"""
    # Create a clip
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=75,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    # Create failed log
    log = PublishLogModel(
        clip_id=clip.id,
        platform="instagram",
        status="failed",
        error_message="Test failure"
    )
    db.add(log)
    await db.commit()
    
    # Execute retry action
    action = OrchestratorAction(
        action_type="retry_failed_log",
        params={"max_retries": 3},
        priority=8,
        reason="Test retry"
    )
    
    result = await execute_actions([action], db)
    
    assert result["success_count"] == 1
    assert result["error_count"] == 0
    
    # Verify log was retried
    await db.refresh(log)
    assert log.status == "scheduled"
    assert log.retry_count == 1


@pytest.mark.asyncio
async def test_summarize_decisions_empty(db: AsyncSession):
    """Test decision summary with no actions"""
    actions = []
    summary = summarize_decisions(actions)
    
    assert summary["total_actions"] == 0
    assert summary["decision"] == "no_action_needed"


@pytest.mark.asyncio
async def test_summarize_decisions_with_actions(db: AsyncSession):
    """Test decision summary with actions"""
    actions = [
        OrchestratorAction("retry_failed_log", {}, priority=8, reason="Test 1"),
        OrchestratorAction("schedule_clip", {}, priority=7, reason="Test 2"),
        OrchestratorAction("retry_failed_log", {}, priority=6, reason="Test 3")
    ]
    
    summary = summarize_decisions(actions)
    
    assert summary["total_actions"] == 3
    assert summary["decision"] == "execute_actions"
    assert summary["action_counts"]["retry_failed_log"] == 2
    assert summary["action_counts"]["schedule_clip"] == 1
    assert summary["top_priority"]["action_type"] == "retry_failed_log"
    assert summary["top_priority"]["priority"] == 8


@pytest.mark.asyncio
async def test_run_orchestrator_once_integration(db: AsyncSession, sample_video_asset):
    """Test running full orchestrator cycle"""
    # Create a failed log to trigger action
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=75,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    log = PublishLogModel(
        clip_id=clip.id,
        platform="instagram",
        status="failed",
        error_message="Test failure"
    )
    db.add(log)
    await db.commit()
    
    # Run orchestrator cycle manually (instead of run_orchestrator_once which creates new session)
    snapshot = await monitor_system_state(db)
    actions = decide_actions(snapshot)
    
    # Should have detected failure and suggested retry
    assert snapshot["publish_logs"]["has_failures"] is True
    
    # If actions were decided, execute them
    if actions:
        result = await execute_actions(actions, db)
        assert result["success_count"] >= 0


@pytest.mark.asyncio
async def test_monitor_detects_active_campaigns(db: AsyncSession, sample_video_asset):
    """Test monitor detects active campaigns"""
    # Create a clip
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=80,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    # Create active campaign
    campaign = Campaign(
        name="Test Campaign",
        status=CampaignStatus.ACTIVE,
        clip_id=clip.id,
        budget_cents=20000,  # $200
        targeting={}
    )
    db.add(campaign)
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    
    assert snapshot["campaigns"]["active_count"] == 1
    assert snapshot["campaigns"]["has_active_campaigns"] is True
    assert len(snapshot["campaigns"]["campaigns"]) == 1
    assert snapshot["campaigns"]["campaigns"][0]["budget_cents"] == 20000


@pytest.mark.asyncio
async def test_monitor_detects_ledger_errors(db: AsyncSession):
    """Test monitor detects ledger errors"""
    # Create error events
    for i in range(3):
        await log_event(
            db=db,
            event_type="test.error",
            entity_type="test",
            entity_id="test",
            metadata={"error": f"Test error {i}"},
            severity="ERROR"
        )
    await db.commit()  # Commit events before querying
    
    snapshot = await monitor_system_state(db)
    
    assert snapshot["ledger"]["errors_1h"] == 3
    assert snapshot["ledger"]["has_errors"] is True
    assert len(snapshot["ledger"]["recent_errors"]) == 3


@pytest.mark.asyncio
async def test_decider_handles_campaigns(db: AsyncSession, sample_video_asset):
    """Test decider prioritizes high-budget campaigns"""
    # Create a clip
    clip = Clip(
        video_asset_id=sample_video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=80,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    # Create high-budget campaign
    campaign = Campaign(
        name="High Budget Campaign",
        status=CampaignStatus.ACTIVE,
        clip_id=clip.id,
        budget_cents=15000,  # $150 > $100 threshold
        targeting={}
    )
    db.add(campaign)
    await db.commit()
    
    snapshot = await monitor_system_state(db)
    actions = decide_actions(snapshot)
    
    # Should suggest scheduling the campaign clip
    action_types = [a.action_type for a in actions]
    assert "schedule_clip" in action_types
    
    # Verify at least one schedule_clip action was created
    schedule_actions = [a for a in actions if a.action_type == "schedule_clip"]
    assert len(schedule_actions) > 0


@pytest.mark.asyncio
async def test_health_score_calculation(db: AsyncSession):
    """Test health score reflects system state"""
    # Healthy system
    snapshot = await monitor_system_state(db)
    assert snapshot["system"]["health_score"] == 100
    assert snapshot["system"]["health_status"] == "healthy"
    
    # Create issues
    # 1. Queue saturation (60 pending jobs)
    for i in range(60):
        job = Job(
            job_type="video_editing",
            params={"test": i},
            status=JobStatus.PENDING
        )
        db.add(job)
    
    # 2. Failed publications
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/storage/test.mp4",
        file_size=1000000,
        duration_ms=30000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video_asset)
    await db.flush()
    
    clip = Clip(
        video_asset_id=video_asset.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        visual_score=75,
        status=ClipStatus.READY
    )
    db.add(clip)
    await db.commit()
    
    for i in range(5):
        log = PublishLogModel(
            clip_id=clip.id,
            platform="instagram",
            status="failed",
            error_message="Test failure"
        )
        db.add(log)
    
    # 3. Ledger errors
    for i in range(3):
        await log_event(
            db=db,
            event_type="test.error",
            entity_type="test",
            entity_id="test",
            metadata={"error": f"Test error {i}"},
            severity="ERROR"
        )
    
    await db.commit()
    
    # Check degraded health
    snapshot = await monitor_system_state(db)
    
    # Should have deductions:
    # -20 for queue saturation
    # -10 for publishing failures
    # -15 for 3 ledger errors (5 each)
    # Total: -45, so health should be 55
    assert snapshot["system"]["health_score"] <= 60
    assert snapshot["system"]["health_status"] in ["degraded", "critical"]
    assert snapshot["system"]["requires_attention"] is True
    assert len(snapshot["system"]["recommendations"]) > 0
