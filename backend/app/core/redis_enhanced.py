"""
Redis Enhanced Configuration

Enhanced Redis configuration with:
- Namespace management
- TTL policies
- Retry logic with exponential backoff
- Dead-letter queue
- Monitoring hooks

Phase 1: STUB mode (in-memory simulation)
Phase 2: Real Redis integration
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class RedisNamespace(str, Enum):
    """Redis namespace prefixes"""
    PUBLISHING = "publishing/"
    ML_JOBS = "ml_jobs/"
    UPLOAD_JOBS = "upload_jobs/"
    SESSIONS = "sessions/"
    CACHE = "cache/"
    DEAD_LETTER = "dead_letter/"


class RedisConfig:
    """Redis configuration"""
    
    # Worker configuration
    WORKERS_COUNT = 3
    
    # TTL values (seconds)
    TTL_VALUES = {
        "default": 1800,      # 30 minutes
        "campaign": 7200,     # 2 hours
        "ml_jobs": 3600,      # 1 hour
        "upload_jobs": 600,   # 10 minutes
        "session": 86400,     # 24 hours
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    BACKOFF_BASE = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0  # exponential backoff
    
    # Dead-letter queue
    DLQ_NAMESPACE = f"{RedisNamespace.PUBLISHING.value}dead_letter"
    DLQ_ALERT_THRESHOLD = 10  # Alert after N jobs in DLQ
    
    # Monitoring
    MONITORING_ENABLED = True
    DASHBOARD_INTEGRATION = True


class RedisJobStatus(str, Enum):
    """Job status in queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"


class RedisJob:
    """Represents a job in Redis queue"""
    
    def __init__(
        self,
        job_id: str,
        namespace: str,
        payload: Dict[str, Any],
        ttl: Optional[int] = None,
        priority: int = 0
    ):
        self.job_id = job_id
        self.namespace = namespace
        self.payload = payload
        self.ttl = ttl or RedisConfig.TTL_VALUES["default"]
        self.priority = priority
        
        self.status = RedisJobStatus.PENDING
        self.retry_count = 0
        self.max_retries = RedisConfig.MAX_RETRIES
        self.error_history: List[str] = []
        
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.expires_at = self.created_at + timedelta(seconds=self.ttl)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "namespace": self.namespace,
            "payload": self.payload,
            "ttl": self.ttl,
            "priority": self.priority,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_history": self.error_history,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat(),
        }


class RedisEnhanced:
    """
    Enhanced Redis client with advanced features (STUB mode)
    
    Phase 1: In-memory simulation
    Phase 2: Real Redis with connection pooling
    """
    
    def __init__(self, mode: str = "STUB"):
        self.mode = mode
        self.config = RedisConfig()
        
        # STUB: In-memory storage
        self.jobs: Dict[str, RedisJob] = {}
        self.namespaces: Dict[str, List[str]] = {ns.value: [] for ns in RedisNamespace}
        self.dead_letter_queue: deque = deque(maxlen=1000)
        
        logger.info(f"RedisEnhanced initialized in {mode} mode")
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff delay"""
        return self.config.BACKOFF_BASE * (self.config.BACKOFF_MULTIPLIER ** retry_count)
    
    async def enqueue(
        self,
        namespace: str,
        job_id: str,
        payload: Dict[str, Any],
        ttl: Optional[int] = None,
        priority: int = 0
    ) -> RedisJob:
        """
        Enqueue a job in specified namespace
        
        Args:
            namespace: Namespace for the job
            job_id: Unique job identifier
            payload: Job data
            ttl: Time to live in seconds
            priority: Job priority (higher = more important)
        
        Returns:
            Created RedisJob
        """
        if self.mode == "STUB":
            job = RedisJob(job_id, namespace, payload, ttl, priority)
            self.jobs[job_id] = job
            
            if namespace not in self.namespaces:
                self.namespaces[namespace] = []
            self.namespaces[namespace].append(job_id)
            
            logger.info(f"[STUB] Enqueued job {job_id} in namespace {namespace}")
            return job
        else:
            # LIVE: Would use real Redis here
            raise NotImplementedError("LIVE mode not implemented yet")
    
    async def dequeue(self, namespace: str) -> Optional[RedisJob]:
        """Dequeue next job from namespace"""
        if self.mode == "STUB":
            job_ids = self.namespaces.get(namespace, [])
            
            if not job_ids:
                return None
            
            # Get highest priority pending job
            pending_jobs = [
                (job_id, self.jobs[job_id])
                for job_id in job_ids
                if job_id in self.jobs and self.jobs[job_id].status == RedisJobStatus.PENDING
            ]
            
            if not pending_jobs:
                return None
            
            # Sort by priority (descending) and created_at (ascending)
            pending_jobs.sort(key=lambda x: (-x[1].priority, x[1].created_at))
            
            job_id, job = pending_jobs[0]
            job.status = RedisJobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            
            logger.info(f"[STUB] Dequeued job {job_id} from namespace {namespace}")
            return job
        else:
            # LIVE: Would use real Redis here
            raise NotImplementedError("LIVE mode not implemented yet")
    
    async def complete(self, job_id: str, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        if self.mode == "STUB":
            if job_id not in self.jobs:
                logger.warning(f"[STUB] Job {job_id} not found")
                return
            
            job = self.jobs[job_id]
            job.status = RedisJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            if result:
                job.payload["result"] = result
            
            logger.info(f"[STUB] Completed job {job_id}")
        else:
            # LIVE: Would use real Redis here
            raise NotImplementedError("LIVE mode not implemented yet")
    
    async def fail(self, job_id: str, error: str, retry: bool = True):
        """
        Mark job as failed and optionally retry
        
        Args:
            job_id: Job identifier
            error: Error message
            retry: Whether to retry the job
        """
        if self.mode == "STUB":
            if job_id not in self.jobs:
                logger.warning(f"[STUB] Job {job_id} not found")
                return
            
            job = self.jobs[job_id]
            job.error_history.append(f"{datetime.utcnow().isoformat()}: {error}")
            
            if retry and job.retry_count < job.max_retries:
                # Retry with backoff
                job.retry_count += 1
                job.status = RedisJobStatus.RETRY
                
                backoff_delay = self._calculate_backoff(job.retry_count)
                logger.info(
                    f"[STUB] Job {job_id} failed, retrying {job.retry_count}/{job.max_retries} "
                    f"after {backoff_delay}s backoff"
                )
                
                # Simulate backoff delay
                await asyncio.sleep(backoff_delay)
                
                # Reset to pending for retry
                job.status = RedisJobStatus.PENDING
                job.started_at = None
            else:
                # Move to dead-letter queue
                job.status = RedisJobStatus.DEAD_LETTER
                self.dead_letter_queue.append(job.to_dict())
                
                logger.error(
                    f"[STUB] Job {job_id} moved to dead-letter queue after "
                    f"{job.retry_count} retries"
                )
                
                # Alert if DLQ threshold reached
                if len(self.dead_letter_queue) >= self.config.DLQ_ALERT_THRESHOLD:
                    logger.warning(
                        f"[STUB] Dead-letter queue threshold reached: "
                        f"{len(self.dead_letter_queue)} jobs"
                    )
        else:
            # LIVE: Would use real Redis here
            raise NotImplementedError("LIVE mode not implemented yet")
    
    def get_job(self, job_id: str) -> Optional[RedisJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_namespace_jobs(self, namespace: str) -> List[RedisJob]:
        """Get all jobs in namespace"""
        job_ids = self.namespaces.get(namespace, [])
        return [self.jobs[jid] for jid in job_ids if jid in self.jobs]
    
    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get dead-letter queue contents"""
        return list(self.dead_letter_queue)
    
    def clear_expired(self) -> int:
        """Clear expired jobs"""
        now = datetime.utcnow()
        expired = []
        
        for job_id, job in self.jobs.items():
            if now > job.expires_at:
                expired.append(job_id)
        
        for job_id in expired:
            job = self.jobs.pop(job_id)
            # Remove from namespace
            if job.namespace in self.namespaces:
                try:
                    self.namespaces[job.namespace].remove(job_id)
                except ValueError:
                    pass
        
        if expired:
            logger.info(f"[STUB] Cleared {len(expired)} expired jobs")
        
        return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "total_jobs": len(self.jobs),
            "by_namespace": {},
            "by_status": {},
            "dead_letter_count": len(self.dead_letter_queue),
        }
        
        for namespace in self.namespaces.keys():
            jobs = self.get_namespace_jobs(namespace)
            stats["by_namespace"][namespace] = len(jobs)
        
        for job in self.jobs.values():
            status = job.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats


# Global instance
redis_enhanced = RedisEnhanced(mode="STUB")
