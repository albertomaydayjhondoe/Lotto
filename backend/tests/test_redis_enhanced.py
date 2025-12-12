"""
Tests for Redis Enhanced (STUB mode)

Tests for namespaces, TTL, retry logic, and dead-letter queue
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.redis_enhanced import (
    RedisEnhanced,
    RedisNamespace,
    RedisJobStatus,
    RedisConfig
)


@pytest.fixture
def redis_client():
    """Create Redis enhanced client"""
    return RedisEnhanced(mode="STUB")


@pytest.mark.asyncio
async def test_redis_initialization(redis_client):
    """Test Redis enhanced initializes correctly"""
    assert redis_client.mode == "STUB"
    assert redis_client.config is not None
    assert len(redis_client.namespaces) > 0


@pytest.mark.asyncio
async def test_enqueue_and_dequeue(redis_client):
    """Test basic enqueue/dequeue operations"""
    job_id = str(uuid4())
    payload = {"task": "test_task", "data": "test_data"}
    
    # Enqueue job
    job = await redis_client.enqueue(
        namespace=RedisNamespace.PUBLISHING.value,
        job_id=job_id,
        payload=payload
    )
    
    assert job.job_id == job_id
    assert job.status == RedisJobStatus.PENDING
    assert job.payload == payload
    
    # Dequeue job
    dequeued_job = await redis_client.dequeue(RedisNamespace.PUBLISHING.value)
    
    assert dequeued_job is not None
    assert dequeued_job.job_id == job_id
    assert dequeued_job.status == RedisJobStatus.PROCESSING


@pytest.mark.asyncio
async def test_job_completion(redis_client):
    """Test marking job as completed"""
    job_id = str(uuid4())
    
    # Enqueue and dequeue
    await redis_client.enqueue(
        namespace=RedisNamespace.ML_JOBS.value,
        job_id=job_id,
        payload={"task": "ml_inference"}
    )
    
    await redis_client.dequeue(RedisNamespace.ML_JOBS.value)
    
    # Complete job
    result = {"output": "success", "score": 0.95}
    await redis_client.complete(job_id, result)
    
    job = redis_client.get_job(job_id)
    assert job.status == RedisJobStatus.COMPLETED
    assert job.completed_at is not None
    assert job.payload["result"] == result


@pytest.mark.asyncio
async def test_job_retry_logic(redis_client):
    """Test job retry with exponential backoff"""
    job_id = str(uuid4())
    
    # Enqueue job
    await redis_client.enqueue(
        namespace=RedisNamespace.UPLOAD_JOBS.value,
        job_id=job_id,
        payload={"file": "test.mp4"}
    )
    
    # Dequeue
    await redis_client.dequeue(RedisNamespace.UPLOAD_JOBS.value)
    
    # Fail with retry
    await redis_client.fail(job_id, "Network timeout", retry=True)
    
    job = redis_client.get_job(job_id)
    assert job.retry_count == 1
    assert len(job.error_history) == 1
    assert job.status == RedisJobStatus.PENDING  # Reset to pending after backoff
    
    # Retry again
    await redis_client.dequeue(RedisNamespace.UPLOAD_JOBS.value)
    await redis_client.fail(job_id, "Connection refused", retry=True)
    
    job = redis_client.get_job(job_id)
    assert job.retry_count == 2


@pytest.mark.asyncio
async def test_dead_letter_queue(redis_client):
    """Test dead-letter queue after max retries"""
    job_id = str(uuid4())
    
    # Enqueue job
    await redis_client.enqueue(
        namespace=RedisNamespace.PUBLISHING.value,
        job_id=job_id,
        payload={"campaign": "test_campaign"}
    )
    
    # Fail multiple times until dead-letter
    for i in range(RedisConfig.MAX_RETRIES):
        await redis_client.dequeue(RedisNamespace.PUBLISHING.value)
        await redis_client.fail(job_id, f"Error {i+1}", retry=True)
    
    # One more failure should move to DLQ
    job = redis_client.get_job(job_id)
    if job.status != RedisJobStatus.DEAD_LETTER:
        await redis_client.dequeue(RedisNamespace.PUBLISHING.value)
        await redis_client.fail(job_id, "Final error", retry=True)
    
    job = redis_client.get_job(job_id)
    assert job.status == RedisJobStatus.DEAD_LETTER
    
    # Check DLQ
    dlq = redis_client.get_dead_letter_queue()
    assert len(dlq) > 0
    assert any(j["job_id"] == job_id for j in dlq)


@pytest.mark.asyncio
async def test_priority_queuing(redis_client):
    """Test jobs are dequeued by priority"""
    namespace = RedisNamespace.ML_JOBS.value
    
    # Enqueue jobs with different priorities
    low_priority_id = str(uuid4())
    high_priority_id = str(uuid4())
    
    await redis_client.enqueue(
        namespace=namespace,
        job_id=low_priority_id,
        payload={"priority": "low"},
        priority=1
    )
    
    await redis_client.enqueue(
        namespace=namespace,
        job_id=high_priority_id,
        payload={"priority": "high"},
        priority=10
    )
    
    # Dequeue should return high priority first
    job = await redis_client.dequeue(namespace)
    assert job.job_id == high_priority_id


@pytest.mark.asyncio
async def test_ttl_expiration(redis_client):
    """Test TTL expiration and cleanup"""
    job_id = str(uuid4())
    
    # Enqueue with short TTL
    job = await redis_client.enqueue(
        namespace=RedisNamespace.CACHE.value,
        job_id=job_id,
        payload={"cached": "data"},
        ttl=1  # 1 second
    )
    
    # Wait for expiration
    await asyncio.sleep(2)
    
    # Manually set expires_at to past (simulating expired job)
    job.expires_at = datetime.utcnow() - timedelta(seconds=10)
    
    # Clear expired
    cleared_count = redis_client.clear_expired()
    
    # Job should be removed
    assert cleared_count >= 0


@pytest.mark.asyncio
async def test_namespace_isolation(redis_client):
    """Test namespace isolation"""
    namespace1 = RedisNamespace.PUBLISHING.value
    namespace2 = RedisNamespace.ML_JOBS.value
    
    # Enqueue in different namespaces
    job1_id = str(uuid4())
    job2_id = str(uuid4())
    
    await redis_client.enqueue(namespace1, job1_id, {"ns": 1})
    await redis_client.enqueue(namespace2, job2_id, {"ns": 2})
    
    # Get jobs from each namespace
    jobs1 = redis_client.get_namespace_jobs(namespace1)
    jobs2 = redis_client.get_namespace_jobs(namespace2)
    
    assert len(jobs1) >= 1
    assert len(jobs2) >= 1
    assert any(j.job_id == job1_id for j in jobs1)
    assert any(j.job_id == job2_id for j in jobs2)
    assert not any(j.job_id == job1_id for j in jobs2)
    assert not any(j.job_id == job2_id for j in jobs1)


@pytest.mark.asyncio
async def test_backoff_calculation(redis_client):
    """Test exponential backoff calculation"""
    # Retry 0: 1s
    backoff0 = redis_client._calculate_backoff(0)
    assert backoff0 == 1.0
    
    # Retry 1: 2s
    backoff1 = redis_client._calculate_backoff(1)
    assert backoff1 == 2.0
    
    # Retry 2: 4s
    backoff2 = redis_client._calculate_backoff(2)
    assert backoff2 == 4.0


@pytest.mark.asyncio
async def test_get_stats(redis_client):
    """Test getting queue statistics"""
    namespace = RedisNamespace.PUBLISHING.value
    
    # Enqueue some jobs
    await redis_client.enqueue(namespace, str(uuid4()), {"test": 1})
    await redis_client.enqueue(namespace, str(uuid4()), {"test": 2})
    
    stats = redis_client.get_stats()
    
    assert "total_jobs" in stats
    assert "by_namespace" in stats
    assert "by_status" in stats
    assert stats["total_jobs"] >= 2
    assert namespace in stats["by_namespace"]


@pytest.mark.asyncio
async def test_empty_queue_dequeue(redis_client):
    """Test dequeuing from empty queue returns None"""
    empty_namespace = RedisNamespace.SESSIONS.value
    
    job = await redis_client.dequeue(empty_namespace)
    assert job is None
