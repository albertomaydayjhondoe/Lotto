"""
Tests for Dashboard AI Module

Tests analyzer, recommender, and router functionality.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard_ai.analyzer import analyze_system, _calculate_queue_health
from app.dashboard_ai.recommender import generate_recommendations
from app.models.database import (
    VideoAsset,
    Clip,
    ClipVariant,
    PublishLogModel,
    Campaign,
    Job,
    JobStatus,
    ClipStatus,
    CampaignStatus
)


@pytest.mark.asyncio
async def test_analyze_system_empty_db(async_session: AsyncSession):
    """Test system analysis with empty database."""
    analysis = await analyze_system(async_session)
    
    assert analysis is not None
    assert analysis.queue_health == "good"
    assert analysis.orchestrator_health == "good"
    assert analysis.publish_success_rate == 0.0
    assert analysis.pending_scheduled == 0
    assert len(analysis.best_clip_per_platform) == 0


@pytest.mark.asyncio
async def test_analyze_system_with_data(async_session: AsyncSession):
    """Test system analysis with sample data."""
    # Create test data
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    variant = ClipVariant(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="ready",
        visual_score=0.95,
        duration_sec=30
    )
    async_session.add(variant)
    
    # Add publish logs
    success_log = PublishLogModel(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="success",
        requested_at=datetime.utcnow()
    )
    async_session.add(success_log)
    
    await async_session.commit()
    
    # Analyze
    analysis = await analyze_system(async_session)
    
    assert analysis.queue_health in ["good", "warning", "critical"]
    assert analysis.publish_success_rate >= 0.0
    assert "instagram" in analysis.best_clip_per_platform


@pytest.mark.asyncio
async def test_calculate_queue_health_good(async_session: AsyncSession):
    """Test queue health calculation - good status."""
    from app.dashboard_api.schemas import QueueStats
    
    queue = QueueStats(
        pending=5,
        processing=2,
        success=100,
        failed=5,
        avg_processing_time_ms=1000.0,
        oldest_pending_age_seconds=300.0
    )
    
    health = _calculate_queue_health(queue)
    assert health == "good"


@pytest.mark.asyncio
async def test_calculate_queue_health_warning(async_session: AsyncSession):
    """Test queue health calculation - warning status."""
    from app.dashboard_api.schemas import QueueStats
    
    queue = QueueStats(
        pending=35,
        processing=5,
        success=100,
        failed=20,
        avg_processing_time_ms=2000.0,
        oldest_pending_age_seconds=1800.0
    )
    
    health = _calculate_queue_health(queue)
    assert health == "warning"


@pytest.mark.asyncio
async def test_calculate_queue_health_critical(async_session: AsyncSession):
    """Test queue health calculation - critical status."""
    from app.dashboard_api.schemas import QueueStats
    
    queue = QueueStats(
        pending=60,
        processing=10,
        success=100,
        failed=50,
        avg_processing_time_ms=5000.0,
        oldest_pending_age_seconds=7200.0
    )
    
    health = _calculate_queue_health(queue)
    assert health == "critical"


@pytest.mark.asyncio
async def test_generate_recommendations_empty_db(async_session: AsyncSession):
    """Test recommendation generation with empty database."""
    recommendations = await generate_recommendations(async_session)
    
    assert isinstance(recommendations, list)
    # May have some default recommendations
    assert len(recommendations) >= 0


@pytest.mark.asyncio
async def test_generate_recommendations_with_high_score_clips(async_session: AsyncSession):
    """Test recommendations for high-scoring clips."""
    # Create high-scoring clip
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    variant = ClipVariant(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="ready",
        visual_score=0.92,  # High score
        duration_sec=30
    )
    async_session.add(variant)
    
    await async_session.commit()
    
    # Generate recommendations
    recommendations = await generate_recommendations(async_session)
    
    assert len(recommendations) > 0
    
    # Should have publish recommendation
    publish_recs = [r for r in recommendations if r.action == "publish"]
    assert len(publish_recs) > 0
    assert publish_recs[0].payload.get("platform") == "instagram"


@pytest.mark.asyncio
async def test_generate_recommendations_with_failed_publications(async_session: AsyncSession):
    """Test recommendations when there are failed publications."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # Add multiple failed logs
    for i in range(15):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=clip.id,
            platform="instagram",
            status="failed",
            requested_at=datetime.utcnow() - timedelta(hours=i)
        )
        async_session.add(log)
    
    await async_session.commit()
    
    # Generate recommendations
    recommendations = await generate_recommendations(async_session)
    
    # Should have retry recommendation
    retry_recs = [r for r in recommendations if r.action == "retry"]
    assert len(retry_recs) > 0


@pytest.mark.asyncio
async def test_recommendations_sorted_by_severity(async_session: AsyncSession):
    """Test that recommendations are sorted by severity (critical first)."""
    # Create conditions that generate multiple recommendation types
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # High score clip (info recommendation)
    variant = ClipVariant(
        id=uuid4(),
        clip_id=clip.id,
        platform="instagram",
        status="ready",
        visual_score=0.85,
        duration_sec=30
    )
    async_session.add(variant)
    
    # Many pending publications (critical recommendation)
    for i in range(60):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=clip.id,
            platform="instagram",
            status="pending",
            scheduled_for=datetime.utcnow() + timedelta(hours=i),
            requested_at=datetime.utcnow()
        )
        async_session.add(log)
    
    await async_session.commit()
    
    # Generate recommendations
    recommendations = await generate_recommendations(async_session)
    
    assert len(recommendations) > 0
    
    # Check first recommendation is critical
    if len(recommendations) > 1:
        # First should be critical or warning (higher priority than info)
        assert recommendations[0].severity in ["critical", "warning"]


@pytest.mark.asyncio
async def test_analyze_system_detects_queue_overload(async_session: AsyncSession):
    """Test that analyzer detects queue overload."""
    video = VideoAsset(id=uuid4(), filename="test.mp4", storage_url="s3://test")
    async_session.add(video)
    
    clip = Clip(id=uuid4(), video_id=video.id, status=ClipStatus.READY)
    async_session.add(clip)
    
    # Create 60 pending items (overload threshold is 50)
    for i in range(60):
        log = PublishLogModel(
            id=uuid4(),
            clip_id=clip.id,
            platform="instagram",
            status="pending",
            scheduled_for=datetime.utcnow() + timedelta(hours=i),
            requested_at=datetime.utcnow()
        )
        async_session.add(log)
    
    await async_session.commit()
    
    # Analyze
    analysis = await analyze_system(async_session)
    
    # Should detect critical queue health
    assert analysis.queue_health == "critical"
    
    # Should have issue detected
    overload_issues = [issue for issue in analysis.issues_detected if "overload" in issue.get("title", "").lower()]
    assert len(overload_issues) > 0
