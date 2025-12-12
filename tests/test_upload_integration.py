"""
Integration tests for POST /upload endpoint
Uses isolated in-memory database and AsyncClient with ASGI transport
"""
import pytest
import pytest_asyncio
import os
import shutil
from io import BytesIO
from pathlib import Path
from httpx import ASGITransport, AsyncClient
from fastapi import status

# Import test database utilities
from test_db import get_test_session, init_test_db, drop_test_db

# Import FastAPI app
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
from app.core.database import get_db
from app.core.config import settings


# Override settings for testing
TEST_STORAGE_DIR = "/tmp/test_storage_videos"
settings.VIDEO_STORAGE_DIR = TEST_STORAGE_DIR


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_environment():
    """
    Setup test environment before each test:
    - Initialize test database
    - Override get_db dependency
    - Create storage directory
    - Cleanup after test
    """
    # Create test storage directory
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)
    
    # Initialize test database
    await init_test_db()
    
    # Override get_db dependency with test session
    app.dependency_overrides[get_db] = get_test_session
    
    yield
    
    # Cleanup after test
    app.dependency_overrides.clear()
    await drop_test_db()
    
    # Clean up storage directory
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR)


@pytest.mark.asyncio
async def test_upload_video_integration():
    """
    Integration test: Upload a video file and verify response + file creation
    
    This test:
    1. Creates a fake video file in memory
    2. Uploads it via POST /upload with title and description
    3. Verifies HTTP 201 response
    4. Verifies JSON response has video_asset_id and job_id
    5. Verifies the file was created in storage directory
    """
    
    # 1. Create a fake video file (small file to simulate video)
    fake_video_content = b"FAKE VIDEO CONTENT FOR TESTING" * 100  # ~3KB
    fake_video_file = BytesIO(fake_video_content)
    
    # 2. Prepare form data
    files = {
        "file": ("test_video.mp4", fake_video_file, "video/mp4")
    }
    data = {
        "title": "Integration Test Video",
        "description": "This is a test upload from pytest"
    }
    
    # 3. Make request to the endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/upload", files=files, data=data)
    
    # 4. Assert HTTP 201 Created
    assert response.status_code == status.HTTP_201_CREATED, \
        f"Expected 201, got {response.status_code}: {response.text}"
    
    # 5. Parse JSON response
    response_json = response.json()
    
    # 6. Assert response structure
    assert "video_asset_id" in response_json, "Response missing video_asset_id"
    assert "job_id" in response_json, "Response missing job_id"
    assert "message" in response_json, "Response missing message"
    
    # 7. Assert IDs are not empty and are valid UUIDs
    video_asset_id = response_json["video_asset_id"]
    job_id = response_json["job_id"]
    
    assert video_asset_id, "video_asset_id is empty"
    assert job_id, "job_id is empty"
    assert len(video_asset_id) == 36, f"Invalid UUID format for video_asset_id: {video_asset_id}"
    assert len(job_id) == 36, f"Invalid UUID format for job_id: {job_id}"
    
    # 8. Assert message indicates success
    assert "queued" in response_json["message"].lower() or "accepted" in response_json["message"].lower(), \
        f"Unexpected message: {response_json['message']}"
    
    # 9. Verify file was created in storage
    storage_path = Path(TEST_STORAGE_DIR) / f"{video_asset_id}.mp4"
    
    assert storage_path.exists(), \
        f"File not found in storage: {storage_path}"
    
    # 10. Verify file size matches uploaded content
    file_size = storage_path.stat().st_size
    assert file_size == len(fake_video_content), \
        f"File size mismatch: expected {len(fake_video_content)}, got {file_size}"
    
    print(f"✓ Integration test passed!")
    print(f"  - video_asset_id: {video_asset_id}")
    print(f"  - job_id: {job_id}")
    print(f"  - message: {response_json['message']}")


@pytest.mark.asyncio
async def test_upload_video_no_file_error():
    """
    Integration test: Verify error response when no file is provided
    """
    
    data = {
        "title": "No File Test",
        "description": "This should fail"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/upload", data=data)
    
    # Should return 400 Bad Request (FastAPI returns 422 for missing required fields)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, 422], \
        f"Expected 400 or 422, got {response.status_code}"
    
    response_json = response.json()
    assert "detail" in response_json, "Error response should have 'detail' field"
    
    print(f"✓ No file error test passed!")


@pytest.mark.asyncio
async def test_upload_video_invalid_type_error():
    """
    Integration test: Verify error response when file is not a video
    """
    
    # Create a fake text file (not a video)
    fake_text_file = BytesIO(b"This is a text file, not a video")
    
    files = {
        "file": ("document.txt", fake_text_file, "text/plain")
    }
    data = {
        "title": "Invalid Type Test",
        "description": "This should fail"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/upload", files=files, data=data)
    
    # Should return 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Expected 400, got {response.status_code}"
    
    response_json = response.json()
    assert "detail" in response_json, "Error response should have 'detail' field"
    assert "video" in response_json["detail"].lower() or "type" in response_json["detail"].lower(), \
        f"Error message should mention invalid type: {response_json['detail']}"
    
    print(f"✓ Invalid type error test passed!")


@pytest.mark.asyncio
async def test_upload_video_with_idempotency():
    """
    Integration test: Verify idempotency - same key returns same result
    """
    
    fake_video_content = b"IDEMPOTENCY TEST VIDEO" * 50
    idempotency_key = "test-idempotency-key-12345"
    
    # First upload
    files1 = {
        "file": ("test_idem.mp4", BytesIO(fake_video_content), "video/mp4")
    }
    data1 = {
        "title": "Idempotency Test 1",
        "description": "First upload",
        "idempotency_key": idempotency_key
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/upload", files=files1, data=data1)
    
    assert response1.status_code == status.HTTP_201_CREATED
    response1_json = response1.json()
    video_id_1 = response1_json["video_asset_id"]
    job_id_1 = response1_json["job_id"]
    
    # Second upload with same idempotency_key
    files2 = {
        "file": ("test_idem2.mp4", BytesIO(fake_video_content), "video/mp4")
    }
    data2 = {
        "title": "Idempotency Test 2",  # Different title
        "description": "Second upload",
        "idempotency_key": idempotency_key  # Same key
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response2 = await client.post("/upload", files=files2, data=data2)
    
    assert response2.status_code == status.HTTP_201_CREATED
    response2_json = response2.json()
    video_id_2 = response2_json["video_asset_id"]
    job_id_2 = response2_json["job_id"]
    
    # Assert both requests returned the SAME IDs (idempotency)
    assert video_id_1 == video_id_2, \
        f"Idempotency failed: different video_asset_ids ({video_id_1} vs {video_id_2})"
    assert job_id_1 == job_id_2, \
        f"Idempotency failed: different job_ids ({job_id_1} vs {job_id_2})"
    
    # Verify message indicates idempotency
    assert "idempotency" in response2_json["message"].lower() or "exists" in response2_json["message"].lower(), \
        f"Second response should indicate idempotency: {response2_json['message']}"
    
    print(f"✓ Idempotency test passed!")
    print(f"  - Both requests returned same IDs: {video_id_1}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
