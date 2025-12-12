"""
Integration tests for Job Runner system
Tests the complete job processing pipeline with queue, dispatcher, and handlers
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.models.database import Job, JobStatus, VideoAsset
from tests.test_db import init_test_db, drop_test_db, get_test_session
from app.core.database import get_db
from app.worker import process_single_job


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
async def test_process_job_from_queue():
    """
    TEST 1 - Process job from queue
    
    Flow:
    1. Create video_asset
    2. Create job PENDING
    3. Execute POST /jobs/process
    4. Verify:
       - status COMPLETED
       - clips created
       - result correct
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create video asset
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                file_path="storage/test_video.mp4",
                file_size=1024 * 1024,
                duration_ms=60000,  # 1 minute
                title="Test Video for Queue",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.flush()
            
            # Create PENDING job
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
        
        # Process job from queue
        response = await client.post("/jobs/process")
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response
        assert result["processed"] is True
        assert result["job_id"] == job_id
        assert result["job_type"] == "cut_analysis"
        assert result["status"] == "completed"
        assert result["error"] is None
        
        # Validate result content
        assert "result" in result
        job_result = result["result"]
        assert job_result["clips_created"] >= 3
        assert job_result["duration"] == 60000
        assert len(job_result["variants"]) >= 3
        
        # Verify processing time
        assert result["processing_time_ms"] > 0
        
        print(f"\n✓ TEST 1 PASSED - Job processed from queue")
        print(f"  - job_id: {result['job_id']}")
        print(f"  - clips_created: {job_result['clips_created']}")
        print(f"  - processing_time: {result['processing_time_ms']}ms")


@pytest.mark.asyncio
async def test_no_reprocess_completed_jobs():
    """
    TEST 2 - No reprocess completed jobs
    
    Flow:
    1. Create job COMPLETED
    2. Call POST /jobs/process
    3. Verify: returns {"processed": false}
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create video asset
        async for session in get_test_session():
            video_asset = VideoAsset(
                id=uuid4(),
                file_path="storage/completed_video.mp4",
                file_size=1024,
                title="Completed Video",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(video_asset)
            await session.flush()
            
            # Create COMPLETED job (already processed)
            job = Job(
                id=uuid4(),
                job_type="cut_analysis",
                status=JobStatus.COMPLETED,
                video_asset_id=video_asset.id,
                result={"clips_created": 3},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(job)
            await session.commit()
            break
        
        # Try to process - should find no PENDING jobs
        response = await client.post("/jobs/process")
        
        assert response.status_code == 200
        result = response.json()
        
        # Should not process
        assert result["processed"] is False
        assert "No pending jobs" in result.get("message", "")
        
        print(f"\n✓ TEST 2 PASSED - Completed jobs not reprocessed")
        print(f"  - message: {result.get('message')}")


@pytest.mark.asyncio
async def test_unknown_job_type_fails():
    """
    TEST 3 - Handler UNKNOWN fails
    
    Flow:
    1. Create job with job_type="xx_invalid"
    2. Worker processes it
    3. Verify: marked as FAILED with appropriate error
    """
    async for session in get_test_session():
        # Create video asset
        video_asset = VideoAsset(
            id=uuid4(),
            file_path="storage/invalid_job_video.mp4",
            file_size=1024,
            title="Invalid Job Video",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(video_asset)
        await session.flush()
        
        # Create job with INVALID job_type
        job = Job(
            id=uuid4(),
            job_type="xx_invalid",  # Unknown handler
            status=JobStatus.PENDING,
            video_asset_id=video_asset.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = str(job.id)
        
        # Process job directly
        result = await process_single_job(session)
        
        # Should mark as FAILED
        assert result["processed"] is True
        assert result["job_id"] == job_id
        assert result["job_type"] == "xx_invalid"
        assert result["status"] == "failed"
        assert "Unknown job_type" in result["error"]
        
        # Verify job in database
        await session.refresh(job)
        assert job.status == JobStatus.FAILED
        assert "Unknown job_type" in job.error_message
        
        print(f"\n✓ TEST 3 PASSED - Unknown job type marked as FAILED")
        print(f"  - job_id: {result['job_id']}")
        print(f"  - error: {result['error']}")
        
        break


@pytest.mark.asyncio
async def test_concurrent_queue_processing():
    """
    TEST 4 - Concurrent queue processing
    
    Flow:
    1. Create 3 PENDING jobs
    2. Process each manually (simulating concurrent workers)
    3. Verify: all 3 complete successfully without conflicts
    """
    async for session in get_test_session():
        # Create video asset
        video_asset = VideoAsset(
            id=uuid4(),
            file_path="storage/concurrent_video.mp4",
            file_size=1024 * 1024,
            duration_ms=60000,
            title="Concurrent Test Video",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(video_asset)
        await session.flush()
        
        # Create 3 PENDING jobs
        job_ids = []
        for i in range(3):
            job = Job(
                id=uuid4(),
                job_type="cut_analysis",
                status=JobStatus.PENDING,
                video_asset_id=video_asset.id,
                params={"batch": i},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(job)
            job_ids.append(str(job.id))
        
        await session.commit()
        
        # Process jobs sequentially (simulating concurrent workers)
        results = []
        for _ in range(3):
            result = await process_single_job(session)
            results.append(result)
        
        # Verify all processed successfully
        processed_count = sum(1 for r in results if r.get("processed"))
        assert processed_count == 3, f"Expected 3 processed, got {processed_count}"
        
        completed_jobs = [r for r in results if r.get("status") == "completed"]
        assert len(completed_jobs) == 3
        
        # Verify all job IDs match
        processed_ids = [r["job_id"] for r in results if r.get("processed")]
        assert set(processed_ids) == set(job_ids)
        
        # Verify no duplicates (each job processed once)
        assert len(processed_ids) == len(set(processed_ids))
        
        print(f"\n✓ TEST 4 PASSED - Concurrent queue processing")
        print(f"  - jobs_created: 3")
        print(f"  - jobs_processed: {processed_count}")
        print(f"  - all_completed: {len(completed_jobs) == 3}")
        
        break


@pytest.mark.asyncio
async def test_queue_empty_returns_false():
    """
    TEST 5 - Empty queue handling
    
    Flow:
    1. Ensure no PENDING jobs exist
    2. Call process_single_job
    3. Verify: returns {"processed": false}
    """
    async for session in get_test_session():
        # Don't create any jobs
        
        result = await process_single_job(session)
        
        assert result["processed"] is False
        assert "No pending jobs" in result.get("message", "")
        
        print(f"\n✓ TEST 5 PASSED - Empty queue handled correctly")
        print(f"  - processed: {result['processed']}")
        
        break
