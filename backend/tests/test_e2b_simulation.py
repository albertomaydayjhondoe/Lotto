"""
Tests for E2B Sandbox Simulation Engine
"""
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    Job, JobStatus, VideoAsset, Clip, ClipStatus
)
from app.e2b import (
    run_e2b_simulation,
    dispatch_e2b_job,
    should_use_e2b_dispatcher,
    process_e2b_callback,
    validate_e2b_callback,
    E2BSandboxRequest,
    E2BSandboxResult,
    FakeCut,
    FakeTrendFeatures,
)
from tests.test_db import init_test_db, drop_test_db, get_test_session


# Test fixtures
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test."""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def video_asset(db_session):
    """Create a test video asset."""
    video = VideoAsset(
        id=uuid4(),
        title="E2B Test Video",
        file_path="/storage/e2b_test.mp4",
        file_size=5000000,
        duration_ms=30000,  # 30 seconds
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest_asyncio.fixture
async def e2b_job(db_session, video_asset):
    """Create a test E2B job."""
    job = Job(
        id=uuid4(),
        job_type="cut_analysis_e2b",
        status=JobStatus.PENDING,
        video_asset_id=video_asset.id,
        params={"test": True}
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.mark.asyncio
async def test_e2b_job_creation(db_session, video_asset):
    """Test creating an E2B job."""
    job_id = uuid4()
    job = Job(
        id=job_id,
        job_type="cut_analysis_e2b",
        status=JobStatus.PENDING,
        video_asset_id=video_asset.id,
        params={"simulation": True}
    )
    
    db_session.add(job)
    await db_session.commit()
    
    # Verify job was created
    stmt = select(Job).where(Job.id == job_id)
    result = await db_session.execute(stmt)
    saved_job = result.scalar_one()
    
    assert saved_job.id == job_id
    assert saved_job.job_type == "cut_analysis_e2b"
    assert saved_job.status == JobStatus.PENDING
    assert saved_job.video_asset_id == video_asset.id


@pytest.mark.asyncio
async def test_e2b_simulation_creates_clips(db_session, e2b_job, video_asset):
    """Test that E2B simulation creates clips in database."""
    # Run simulation
    result = await run_e2b_simulation(job=e2b_job, db=db_session)
    
    # Verify result
    assert result.status == "completed"
    assert result.job_id == e2b_job.id
    assert result.video_asset_id == video_asset.id
    assert len(result.cuts) >= 3  # At least 3 cuts
    assert len(result.cuts) <= 12  # At most 12 cuts
    
    # Verify clips were created in DB
    stmt = select(Clip).where(Clip.video_asset_id == video_asset.id)
    db_result = await db_session.execute(stmt)
    clips = db_result.scalars().all()
    
    assert len(clips) == len(result.cuts)
    
    # Verify all clips are READY
    for clip in clips:
        assert clip.status == ClipStatus.READY
        assert clip.visual_score is not None
        assert 0.0 <= clip.visual_score <= 1.0


@pytest.mark.asyncio
async def test_e2b_scores_are_calculated(db_session, e2b_job):
    """Test that E2B calculates proper scores for cuts."""
    result = await run_e2b_simulation(job=e2b_job, db=db_session)
    
    # Verify all cuts have valid scores
    for cut in result.cuts:
        # Visual score
        assert 0.0 <= cut.visual_score <= 1.0
        
        # Motion intensity
        assert 0.0 <= cut.motion_intensity <= 1.0
        
        # Trend score
        assert 0.0 <= cut.trend_score <= 1.0
        
        # Confidence
        assert 0.0 <= cut.confidence <= 1.0
        
        # Duration makes sense
        assert cut.duration_ms > 0
        assert cut.duration_ms == cut.end_ms - cut.start_ms
        
        # Times are within video duration
        assert cut.start_ms >= 0
        assert cut.end_ms <= 30000  # Video duration


@pytest.mark.asyncio
async def test_e2b_callback_updates_job(db_session, e2b_job, video_asset):
    """Test that E2B callback updates job status."""
    # Create fake callback result
    fake_cuts = [
        FakeCut(
            start_ms=0,
            end_ms=10000,
            duration_ms=10000,
            visual_score=0.85,
            motion_intensity=0.7,
            trend_score=0.6,
            confidence=0.8
        ),
        FakeCut(
            start_ms=10000,
            end_ms=20000,
            duration_ms=10000,
            visual_score=0.9,
            motion_intensity=0.8,
            trend_score=0.75,
            confidence=0.85
        )
    ]
    
    callback_result = E2BSandboxResult(
        job_id=e2b_job.id,
        video_asset_id=video_asset.id,
        status="completed",
        cuts=fake_cuts,
        yolo_detections=[],
        embeddings=[],
        trend_features=FakeTrendFeatures(
            hashtag_relevance=0.8,
            audio_trend_score=0.7,
            visual_trend_score=0.85,
            overall_trend_score=0.78
        ),
        processing_time_ms=1500,
        created_at=datetime.utcnow()
    )
    
    # Process callback
    updated_job = await process_e2b_callback(
        job_id=e2b_job.id,
        result=callback_result,
        db=db_session
    )
    
    # Verify job was updated
    assert updated_job.id == e2b_job.id
    assert updated_job.status == JobStatus.COMPLETED
    assert updated_job.result is not None
    assert updated_job.result["status"] == "completed"
    assert updated_job.result["num_cuts"] == 2
    assert updated_job.result["processing_time_ms"] == 1500


@pytest.mark.asyncio
async def test_e2b_integration_with_job_runner(db_session, e2b_job):
    """Test full E2B integration with job dispatcher."""
    # Verify job type is recognized
    assert should_use_e2b_dispatcher(e2b_job) is True
    
    # Dispatch job
    result = await dispatch_e2b_job(job=e2b_job, db=db_session)
    
    # Verify result
    assert isinstance(result, E2BSandboxResult)
    assert result.status == "completed"
    assert len(result.cuts) >= 3
    
    # Verify job was updated
    await db_session.refresh(e2b_job)
    assert e2b_job.status == JobStatus.COMPLETED
    assert e2b_job.result is not None
    assert e2b_job.result["status"] == "completed"


@pytest.mark.asyncio
async def test_e2b_callback_validation(db_session):
    """Test E2B callback validation."""
    # Valid callback
    valid_result = E2BSandboxResult(
        job_id=uuid4(),
        video_asset_id=uuid4(),
        status="completed",
        cuts=[
            FakeCut(
                start_ms=0,
                end_ms=5000,
                duration_ms=5000,
                visual_score=0.8,
                motion_intensity=0.7,
                trend_score=0.6,
                confidence=0.75
            )
        ],
        yolo_detections=[],
        embeddings=[],
        processing_time_ms=1000
    )
    
    assert validate_e2b_callback(valid_result) is True
    
    # Invalid: no cuts
    invalid_result_no_cuts = E2BSandboxResult(
        job_id=uuid4(),
        video_asset_id=uuid4(),
        status="completed",
        cuts=[],
        yolo_detections=[],
        embeddings=[],
        processing_time_ms=1000
    )
    
    assert validate_e2b_callback(invalid_result_no_cuts) is False
    
    # Invalid: bad scores (should fail at Pydantic validation level)
    with pytest.raises(Exception):  # Pydantic ValidationError
        invalid_result_bad_score = E2BSandboxResult(
            job_id=uuid4(),
            video_asset_id=uuid4(),
            status="completed",
            cuts=[
                FakeCut(
                    start_ms=0,
                    end_ms=5000,
                    duration_ms=5000,
                    visual_score=1.5,  # Invalid: > 1.0
                    motion_intensity=0.7,
                    trend_score=0.6,
                    confidence=0.75
                )
            ],
            yolo_detections=[],
            embeddings=[],
            processing_time_ms=1000
        )
    
    # Invalid status
    invalid_result_bad_status = E2BSandboxResult(
        job_id=uuid4(),
        video_asset_id=uuid4(),
        status="unknown_status",  # Invalid status
        cuts=[
            FakeCut(
                start_ms=0,
                end_ms=5000,
                duration_ms=5000,
                visual_score=0.8,
                motion_intensity=0.7,
                trend_score=0.6,
                confidence=0.75
            )
        ],
        yolo_detections=[],
        embeddings=[],
        processing_time_ms=1000
    )
    
    assert validate_e2b_callback(invalid_result_bad_status) is False


@pytest.mark.asyncio
async def test_e2b_generates_detections_and_embeddings(db_session, e2b_job):
    """Test that E2B generates YOLO detections and embeddings."""
    result = await run_e2b_simulation(job=e2b_job, db=db_session)
    
    # Verify detections exist
    assert len(result.yolo_detections) >= 10
    assert len(result.yolo_detections) <= 30
    
    for detection in result.yolo_detections:
        assert detection.class_name is not None
        assert 0.0 <= detection.confidence <= 1.0
        assert len(detection.bbox) == 4  # [x, y, width, height]
        assert detection.timestamp_ms >= 0
    
    # Verify embeddings exist
    assert len(result.embeddings) > 0
    
    for embedding in result.embeddings:
        assert len(embedding.vector) == 512  # 512-dimensional
        assert embedding.model_name == "fake-clip-vit"
        assert embedding.timestamp_ms >= 0
    
    # Verify trend features
    assert result.trend_features is not None
    assert 0.0 <= result.trend_features.hashtag_relevance <= 1.0
    assert 0.0 <= result.trend_features.audio_trend_score <= 1.0
    assert 0.0 <= result.trend_features.visual_trend_score <= 1.0
    assert 0.0 <= result.trend_features.overall_trend_score <= 1.0
