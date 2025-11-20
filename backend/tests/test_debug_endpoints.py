"""
Integration tests for Debug Endpoints
Tests monitoring and health check functionality
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch

from app.main import app
from app.models.database import Job, JobStatus, VideoAsset, Clip, ClipStatus
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


@pytest.mark.asyncio
async def test_debug_jobs_summary():
    """
    Test GET /debug/jobs/summary
    
    Creates jobs in different statuses and verifies the summary endpoint
    returns correct counts.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create video asset for jobs
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                file_path="storage/test_video.mp4",
                file_size=1024,
                title="Test Video",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.flush()
            
            # Create jobs in different statuses
            jobs_data = [
                (JobStatus.PENDING, 3),
                (JobStatus.PROCESSING, 1),
                (JobStatus.COMPLETED, 5),
                (JobStatus.FAILED, 2),
                (JobStatus.RETRY, 1),
            ]
            
            total_jobs = 0
            for status, count in jobs_data:
                for _ in range(count):
                    job = Job(
                        id=uuid4(),
                        job_type="cut_analysis",
                        status=status,
                        video_asset_id=video_asset.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(job)
                    total_jobs += 1
            
            await session.commit()
            break
        
        # Call the endpoint
        response = await client.get("/debug/jobs/summary")
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify structure
        assert "total" in result
        assert "by_status" in result
        
        # Verify total
        assert result["total"] == total_jobs
        assert result["total"] == 12  # 3+1+5+2+1
        
        # Verify by_status has all expected keys
        by_status = result["by_status"]
        assert "pending" in by_status
        assert "processing" in by_status
        assert "retry" in by_status
        assert "completed" in by_status
        assert "failed" in by_status
        
        # Verify counts
        assert by_status["pending"] == 3
        assert by_status["processing"] == 1
        assert by_status["completed"] == 5
        assert by_status["failed"] == 2
        assert by_status["retry"] == 1
        
        print(f"\n✓ TEST PASSED - Jobs summary")
        print(f"  - total: {result['total']}")
        print(f"  - by_status: {by_status}")


@pytest.mark.asyncio
async def test_debug_clips_summary():
    """
    Test GET /debug/clips/summary
    
    Creates clips in different statuses and verifies the summary endpoint
    returns correct counts.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create video asset for clips
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                file_path="storage/test_video.mp4",
                file_size=1024,
                title="Test Video",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.flush()
            
            # Create clips in different statuses
            clips_data = [
                (ClipStatus.PENDING, 2),
                (ClipStatus.PROCESSING, 1),
                (ClipStatus.READY, 8),
                (ClipStatus.PUBLISHED, 3),
                (ClipStatus.FAILED, 1),
            ]
            
            total_clips = 0
            for status, count in clips_data:
                for i in range(count):
                    clip = Clip(
                        id=uuid4(),
                        video_asset_id=video_asset.id,
                        start_ms=i * 1000,
                        end_ms=(i + 1) * 1000,
                        duration_ms=1000,
                        status=status,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(clip)
                    total_clips += 1
            
            await session.commit()
            break
        
        # Call the endpoint
        response = await client.get("/debug/clips/summary")
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify structure
        assert "total" in result
        assert "by_status" in result
        
        # Verify total
        assert result["total"] == total_clips
        assert result["total"] == 15  # 2+1+8+3+1
        
        # Verify by_status has all expected keys
        by_status = result["by_status"]
        assert "pending" in by_status
        assert "processing" in by_status
        assert "ready" in by_status
        assert "published" in by_status
        assert "failed" in by_status
        
        # Verify counts
        assert by_status["pending"] == 2
        assert by_status["processing"] == 1
        assert by_status["ready"] == 8
        assert by_status["published"] == 3
        assert by_status["failed"] == 1
        
        print(f"\n✓ TEST PASSED - Clips summary")
        print(f"  - total: {result['total']}")
        print(f"  - by_status: {by_status}")


@pytest.mark.asyncio
async def test_debug_health_ok():
    """
    Test GET /debug/health with healthy database
    
    Verifies that health check returns 200 with status="ok" when
    database is functioning correctly.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Call health endpoint
        response = await client.get("/debug/health")
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert "status" in result
        assert result["status"] == "ok"
        
        print(f"\n✓ TEST PASSED - Health check OK")
        print(f"  - status: {result['status']}")


@pytest.mark.asyncio
async def test_debug_health_db_error():
    """
    Test GET /debug/health with database error
    
    Simulates a database error and verifies that health check
    returns 500 with status="error".
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Override get_db to provide a session that will fail
        async def failing_get_db():
            # Create a mock session that raises on execute
            from unittest.mock import AsyncMock, MagicMock
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Simulated database connection failure"))
            yield mock_session
        
        # Override the dependency
        app.dependency_overrides[get_db] = failing_get_db
        
        try:
            # Call health endpoint
            response = await client.get("/debug/health")
            
            # Should return 500
            assert response.status_code == 500
            result = response.json()
            
            # Verify error response
            assert "detail" in result
            assert "database" in result["detail"].lower() or "failed" in result["detail"].lower()
            
            print(f"\n✓ TEST PASSED - Health check error handling")
            print(f"  - status_code: {response.status_code}")
            print(f"  - detail: {result['detail']}")
        finally:
            # Restore original dependency
            app.dependency_overrides[get_db] = get_test_session


@pytest.mark.asyncio
async def test_debug_jobs_summary_empty():
    """
    Test GET /debug/jobs/summary with no jobs
    
    Verifies that summary works correctly when database is empty.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Don't create any jobs
        
        response = await client.get("/debug/jobs/summary")
        
        assert response.status_code == 200
        result = response.json()
        
        # Should return zero counts
        assert result["total"] == 0
        assert all(count == 0 for count in result["by_status"].values())
        
        print(f"\n✓ TEST PASSED - Empty jobs summary")
        print(f"  - total: {result['total']}")


@pytest.mark.asyncio
async def test_debug_clips_summary_empty():
    """
    Test GET /debug/clips/summary with no clips
    
    Verifies that summary works correctly when database is empty.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Don't create any clips
        
        response = await client.get("/debug/clips/summary")
        
        assert response.status_code == 200
        result = response.json()
        
        # Should return zero counts
        assert result["total"] == 0
        assert all(count == 0 for count in result["by_status"].values())
        
        print(f"\n✓ TEST PASSED - Empty clips summary")
        print(f"  - total: {result['total']}")
