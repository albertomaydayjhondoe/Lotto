# Publishing Worker

## Overview

The **Publishing Worker** is an async background worker that continuously processes pending publication requests from the `publish_logs` queue. It integrates the **Publishing Queue** (PASO 4.1) with the **Publishing Engine** (PASO 2) to provide automated, reliable publication processing.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Publishing Worker Flow                        │
└─────────────────────────────────────────────────────────────────┘

1. Worker Loop
   └─> fetch_next_pending_log() [with locking]
   
2. Mark as Processing
   └─> mark_log_processing()
   
3. Execute Publishing
   └─> publish_clip() [Publishing Engine]
   
4. Update Status
   ├─> Success: mark_log_success()
   └─> Failure: mark_log_failed()
   
5. Log Events
   └─> SocialSyncLedger events
   
6. Wait & Repeat
   └─> asyncio.sleep(poll_interval)
```

### Worker Types

#### Continuous Worker (`run_publishing_worker`)

Runs indefinitely in the background, polling the queue at regular intervals.

**Use cases:**
- Production deployment
- Long-running background processing
- Automated publication processing

**Behavior:**
- ✅ Infinite loop until cancelled
- ✅ Resilient to errors (never crashes)
- ✅ Logs all events to SocialSyncLedger
- ✅ Configurable poll interval
- ✅ Unique worker_id for tracking

---

#### Single Iteration (`run_publishing_worker_once`)

Processes exactly one log from the queue and returns.

**Use cases:**
- Manual queue processing
- Testing worker behavior
- Development/debugging
- API-triggered processing

**Behavior:**
- ✅ Processes 0 or 1 log
- ✅ Returns immediately
- ✅ Returns detailed result dict
- ✅ No infinite loop

---

## Core Functions

### `run_publishing_worker(db, *, worker_id, poll_interval=1.0)`

Run the worker loop continuously.

**Parameters:**
- `db: AsyncSession` - Database session
- `worker_id: str` - Unique identifier for this worker (e.g., "worker-1")
- `poll_interval: float` - Seconds between queue polls (default: 1.0)

**Behavior:**
1. Fetch next pending log with `fetch_next_pending_log()`
2. If log exists:
   - Mark as processing
   - Call `publish_clip()`
   - Mark as success/failed
   - Log events
3. Wait `poll_interval` seconds
4. Repeat from step 1

**Error Handling:**
- Worker **never crashes** - all exceptions are caught and logged
- Logs errors to SocialSyncLedger
- Continues processing after errors
- Waits 2x poll_interval after error

**Cancellation:**
- Responds to `asyncio.CancelledError`
- Logs shutdown event
- Re-raises for proper cleanup

**Example:**
```python
import asyncio
from app.core.database import get_db
from app.publishing_worker import run_publishing_worker

async def main():
    async with get_db() as db:
        try:
            await run_publishing_worker(
                db,
                worker_id="worker-1",
                poll_interval=2.0
            )
        except asyncio.CancelledError:
            print("Worker stopped")

asyncio.run(main())
```

---

### `run_publishing_worker_once(db) -> Dict`

Process a single log from the queue (one iteration only).

**Parameters:**
- `db: AsyncSession` - Database session

**Returns:**
```python
{
    "processed": bool,          # Whether a log was processed
    "log_id": str | None,       # ID of processed log
    "status": str | None,       # "success" or "failed"
    "error": str | None,        # Error message if failed
    "external_post_id": str | None,  # Platform post ID if success
    "platform": str | None      # Platform name
}
```

**Example:**
```python
result = await run_publishing_worker_once(db)

if result["processed"]:
    print(f"✅ Processed log {result['log_id']}")
    print(f"   Status: {result['status']}")
    print(f"   Platform: {result['platform']}")
    if result["status"] == "success":
        print(f"   Post ID: {result['external_post_id']}")
    else:
        print(f"   Error: {result['error']}")
else:
    print("ℹ️  Queue is empty")
```

---

## API Endpoints

### `POST /publishing/worker/process_once`

Manually trigger processing of one log from the queue.

**Use cases:**
- Development/debugging
- Manual queue clearing
- Testing without running full worker

**Request:**
```bash
curl -X POST http://localhost:8000/publishing/worker/process_once
```

**Response (Success):**
```json
{
    "processed": true,
    "log_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "success",
    "error": null,
    "external_post_id": "instagram_post_12345",
    "platform": "instagram"
}
```

**Response (Queue Empty):**
```json
{
    "processed": false,
    "log_id": null,
    "status": null,
    "error": null,
    "external_post_id": null,
    "platform": null
}
```

**Response (Failed):**
```json
{
    "processed": true,
    "log_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "failed",
    "error": "Authentication failed: Invalid API key",
    "external_post_id": null,
    "platform": "instagram"
}
```

---

## Concurrency & Scaling

### Multiple Workers (PostgreSQL)

With PostgreSQL's `SKIP LOCKED`, you can run **multiple workers safely**:

```python
# Worker 1
await run_publishing_worker(db, worker_id="worker-1")

# Worker 2 (different process/container)
await run_publishing_worker(db, worker_id="worker-2")

# Worker 3
await run_publishing_worker(db, worker_id="worker-3")
```

**How it works:**
- Each worker calls `fetch_next_pending_log()`
- PostgreSQL's `SKIP LOCKED` ensures each worker gets a **different** log
- No race conditions
- Parallel processing for maximum throughput

**Recommended setup:**
- 1-3 workers for low volume
- 5-10 workers for medium volume
- 10+ workers for high volume

---

### Single Worker (SQLite)

SQLite doesn't support `SKIP LOCKED`, so use **one worker only**:

```python
# Only run ONE worker with SQLite
await run_publishing_worker(db, worker_id="worker-1")
```

**Why?**
- Multiple workers may pick up the same log (race condition)
- SQLite is intended for development/testing
- Production should use PostgreSQL

---

## Event Logging (SocialSyncLedger)

The worker logs all events to the `SocialSyncLedger` for monitoring and debugging:

### Event Types

| Event | Severity | Description |
|-------|----------|-------------|
| `publish_worker_started` | info | Worker loop started |
| `publish_worker_log_taken` | info | Worker picked up a log |
| `publish_worker_log_success` | info | Log published successfully |
| `publish_worker_log_failed` | error | Log publishing failed |
| `publish_worker_idle` | debug | Queue empty, worker waiting |
| `publish_worker_error` | error | Unexpected worker error |
| `publish_worker_stopped` | info | Worker loop stopped |

### Query Events

```python
from app.ledger import get_events_by_entity

# Get all events for a specific log
events = await get_events_by_entity(db, "publish_log", log_id)

# Get all worker events
events = await get_events_by_entity(db, "worker", worker_id)
```

---

## Integration with Publishing Engine

The worker calls `publish_clip()` from the Publishing Engine:

```python
from app.publishing_engine import publish_clip
from app.publishing_engine.models import PublishRequest

# Build request from log
request = PublishRequest(
    clip_id=log.clip_id,
    platform=log.platform,
    social_account_id=log.social_account_id
)

# Execute publishing
result = await publish_clip(db, request)

# result.external_post_id → platform post ID
# result.external_url → public URL
# result.success → True/False
```

**Current Behavior (PASO 2):**
- Uses **simulators** (no real API calls)
- Always succeeds with fake post IDs
- Instant execution (no delays)

**Future Behavior (PASO 3+):**
- Uses **real API clients** (Instagram, TikTok, YouTube)
- Real API calls with credentials
- Rate limiting and error handling

---

## Error Handling

### Worker Resilience

The worker is designed to **never crash**:

```python
try:
    # Process log
    result = await publish_clip(db, request)
    await mark_log_success(db, log, ...)
    
except Exception as e:
    # Mark log as failed
    await mark_log_failed(db, log, error_message=str(e))
    
    # Log to ledger
    await log_event(db, event_type="publish_worker_log_failed", ...)
    
    # Worker continues (doesn't crash)
```

### Error Types

| Error | Behavior |
|-------|----------|
| Publishing fails | Mark log as failed, continue |
| Database error | Log error, wait 2x interval, continue |
| Unexpected exception | Log error, wait 2x interval, continue |
| `CancelledError` | Log shutdown, exit cleanly |

---

## Deployment

### Development (Manual)

```bash
# Start FastAPI server
cd /workspaces/stakazo/backend
uvicorn app.main:app --reload

# In another terminal, call the API
curl -X POST http://localhost:8000/publishing/worker/process_once

# Or use run_once in Python
python -c "
import asyncio
from app.core.database import get_db
from app.publishing_worker import run_publishing_worker_once

async def main():
    async with get_db() as db:
        result = await run_publishing_worker_once(db)
        print(result)

asyncio.run(main())
"
```

---

### Production (Background Worker)

**Option 1: Standalone Python Script**

Create `backend/scripts/run_worker.py`:
```python
import asyncio
import signal
from app.core.database import get_db
from app.publishing_worker import run_publishing_worker

worker_task = None

async def main():
    global worker_task
    async with get_db() as db:
        worker_task = asyncio.create_task(
            run_publishing_worker(
                db,
                worker_id="worker-1",
                poll_interval=1.0
            )
        )
        
        # Wait for cancellation
        await worker_task

def shutdown(signum, frame):
    if worker_task:
        worker_task.cancel()

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

asyncio.run(main())
```

Run:
```bash
python scripts/run_worker.py
```

---

**Option 2: Docker Compose**

```yaml
version: '3.8'
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    
  worker-1:
    build: .
    command: python scripts/run_worker.py
    environment:
      - WORKER_ID=worker-1
      
  worker-2:
    build: .
    command: python scripts/run_worker.py
    environment:
      - WORKER_ID=worker-2
```

---

**Option 3: Kubernetes CronJob (Batch Processing)**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: publishing-worker
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: worker
            image: myapp:latest
            command: ["python", "scripts/process_queue_batch.py"]
          restartPolicy: OnFailure
```

---

## Monitoring

### Queue Statistics

```python
from sqlalchemy import select, func
from app.models.database import PublishLogModel

async def get_queue_stats(db):
    result = await db.execute(
        select(
            PublishLogModel.status,
            func.count(PublishLogModel.id).label("count")
        )
        .group_by(PublishLogModel.status)
    )
    
    return {row.status: row.count for row in result}

# Example output:
# {
#     "pending": 42,
#     "processing": 3,
#     "success": 1205,
#     "failed": 15
# }
```

### Worker Activity

```python
from app.ledger import get_recent_events

# Get recent worker events
events = await get_recent_events(db, limit=100)

# Filter by event type
worker_starts = [e for e in events if e.event_type == "publish_worker_started"]
successes = [e for e in events if e.event_type == "publish_worker_log_success"]
failures = [e for e in events if e.event_type == "publish_worker_log_failed"]

print(f"Active workers: {len(worker_starts)}")
print(f"Successes: {len(successes)}")
print(f"Failures: {len(failures)}")
```

---

## Testing

Tests are in `tests/test_publishing_worker.py`:

- ✅ `test_worker_processes_pending_log_success` - Success path
- ✅ `test_worker_marks_failed_on_exception` - Error handling
- ✅ `test_worker_skips_when_no_pending` - Empty queue
- ✅ `test_worker_follows_fifo_order` - FIFO processing
- ✅ `test_worker_resilient_multiple_iterations` - Multiple logs

Run tests:
```bash
pytest tests/test_publishing_worker.py -v
```

---

## Differences from Publishing Queue (PASO 4.1)

| Aspect | PASO 4.1 (Queue) | PASO 4.2 (Worker) |
|--------|------------------|-------------------|
| **Purpose** | Queue operations | Automated processing |
| **Functions** | Low-level (fetch, mark) | High-level (run loop) |
| **Integration** | None | Calls Publishing Engine |
| **Execution** | Manual/API-triggered | Background loop |
| **Events** | None | Full ledger logging |
| **Error Handling** | Raises exceptions | Catches and logs |
| **Use Case** | Building blocks | Production worker |

---

## Future Enhancements (PASO 4.3+)

1. **Priority Queue**
   - Process urgent logs first
   - Add `priority` field to publish_logs

2. **Retry Logic**
   - Automatically retry failed logs
   - Exponential backoff
   - Max retry count

3. **Rate Limiting**
   - Respect platform API limits
   - Track publications per day/hour
   - Delay processing when limit reached

4. **Scheduled Publishing**
   - Add `scheduled_for` timestamp
   - Only process when time reached
   - Timezone support

5. **Worker Health Checks**
   - Heartbeat mechanism
   - Dead worker detection
   - Auto-recovery

6. **Metrics & Dashboards**
   - Prometheus metrics
   - Grafana dashboards
   - Real-time monitoring

---

## References

- `app/publishing_queue/` - Queue operations (PASO 4.1)
- `app/publishing_engine/` - Publishing logic (PASO 2)
- `app/ledger.py` - Event logging
- `tests/test_publishing_worker.py` - Worker tests
- PostgreSQL Locking: https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE
