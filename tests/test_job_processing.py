"""
Integration tests for job processing
Tests the job worker and processing endpoint
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.models.database import Job, JobStatus, VideoAsset
from tests.test_db import init_test_db, drop_test_db, get_test_session, test_engine
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


@pytest.mark.asyncio
async def test_process_cut_analysis_job():
    """
    Test processing a cut_analysis job
    Should create clips based on video analysis
    """
    # Create test video asset and job
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First create a video asset
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                filename="test_video.mp4",
                file_path="storage/test_video.mp4",
                file_size=1024 * 1024,  # 1MB
                duration_ms=60000,  # 1 minute
                title="Test Video",
                description="Test Description",
                release_date=datetime.utcnow().date(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.commit()
            await session.refresh(video_asset)
            video_asset_id = str(video_asset.id)
            
            # Create a job for this video
            job = Job(
                id=uuid4(),
                job_type="cut_analysis",
                status=JobStatus.PENDING,
                video_asset_id=video_asset.id,
                params={"test": True},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            job_id = str(job.id)
            break
        
        # Process the job
        response = await client.post(f"/jobs/{job_id}/process")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "job_id" in result
        assert "status" in result
        assert "clips_generated" in result
        assert "processing_time_ms" in result
        
        # Validate processing results
        assert result["job_id"] == job_id
        assert result["status"] == "completed"
        assert result["clips_generated"] >= 3  # Should generate at least 3 clips
        assert result["processing_time_ms"] > 0
        assert result["error"] is None
        
        print(f"\n✓ Job processing test passed!")
        print(f"  - job_id: {result['job_id']}")
        print(f"  - clips_generated: {result['clips_generated']}")
        print(f"  - processing_time_ms: {result['processing_time_ms']}")


@pytest.mark.asyncio
async def test_process_nonexistent_job():
    """
    Test processing a job that doesn't exist
    Should return 404
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_job_id = str(uuid4())
        response = await client.post(f"/jobs/{fake_job_id}/process")
        
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert result["detail"] == "job not found"
        
        print(f"\n✓ Nonexistent job test passed!")


@pytest.mark.asyncio
async def test_process_completed_job():
    """
    Test processing a job that is already completed
    Should return error in summary
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a completed job
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                filename="test_video2.mp4",
                file_path="storage/test_video2.mp4",
                file_size=1024,
                title="Test Video 2",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.flush()
            
            job = Job(
                id=uuid4(),
                job_type="cut_analysis",
                status=JobStatus.COMPLETED,  # Already completed
                video_asset_id=video_asset.id,
                params={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            job_id = str(job.id)
            break
        
        # Try to process completed job
        response = await client.post(f"/jobs/{job_id}/process")
        
        assert response.status_code == 200
        result = response.json()
        
        # Should return error status
        assert result["status"] == "error"
        assert "cannot process" in result["error"].lower()
        assert result["clips_generated"] == 0
        
        print(f"\n✓ Completed job error test passed!")
        print(f"  - error: {result['error']}")
