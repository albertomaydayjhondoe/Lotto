# Publishing Queue

## Overview

The **Publishing Queue** module provides a safe, queue-based system for processing social media publications using the `publish_logs` table as the queue storage.

This module is responsible for:
- Fetching pending publish logs in a safe, concurrent manner
- Updating log status throughout the publication lifecycle
- Handling concurrency differences between PostgreSQL and SQLite

## Architecture

### Queue Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Publishing Queue Flow                        │
└─────────────────────────────────────────────────────────────────┘

1. API Request
   └─> publish_clip() creates PublishLogModel with status="pending"
   
2. Queue Processing (PASO 4.2 - Worker)
   ├─> fetch_next_pending_log() [with locking]
   ├─> mark_log_processing()
   ├─> Execute publishing_engine logic
   └─> mark_log_success() OR mark_log_failed()

3. Monitoring
   └─> Query publish_logs by status for dashboards/reports
```

### Database Schema

The queue uses the existing `publish_logs` table:

```sql
publish_logs:
  - id (UUID, PK)
  - clip_id (UUID, FK to clips)
  - social_account_id (UUID, FK to social_accounts, nullable)
  - platform (TEXT: instagram, tiktok, youtube)
  - status (TEXT: pending, processing, success, failed)
  - requested_at (TIMESTAMP)
  - published_at (TIMESTAMP, nullable)
  - external_post_id (TEXT, nullable)
  - external_url (TEXT, nullable)
  - error_message (TEXT, nullable)
  - extra_metadata (JSONB)
  - created_at, updated_at
```

## Core Functions

### `fetch_next_pending_log(db: AsyncSession) -> Optional[PublishLogModel]`

Fetches the next pending publish log from the queue with safe locking.

**Behavior:**
- Selects logs with `status = "pending"`
- Orders by `requested_at ASC` (oldest first)
- Returns only ONE log at a time
- Uses database-specific locking for concurrency safety

**Returns:**
- `PublishLogModel` if a pending log exists
- `None` if the queue is empty

**Example:**
```python
log = await fetch_next_pending_log(db)
if log:
    await mark_log_processing(db, log)
    # Process the log...
```

---

### `mark_log_processing(db: AsyncSession, log: PublishLogModel) -> None`

Marks a log as currently being processed.

**Changes:**
- `status` → `"processing"`
- `updated_at` → current timestamp
- Commits immediately

**Purpose:** Prevents other workers from picking up the same log.

---

### `mark_log_success(db, log, external_post_id, external_url, extra_metadata) -> None`

Marks a log as successfully published.

**Changes:**
- `status` → `"success"`
- `published_at` → current timestamp
- `external_post_id` → platform-assigned ID (e.g., Instagram media ID)
- `external_url` → public URL of the post
- `extra_metadata` → merged with existing metadata
- `updated_at` → current timestamp
- Commits immediately

**Example:**
```python
await mark_log_success(
    db,
    log,
    external_post_id="17841405793187218",
    external_url="https://www.instagram.com/p/ABC123/",
    extra_metadata={"likes": 0, "views": 0}
)
```

---

### `mark_log_failed(db, log, error_message, extra_metadata) -> None`

Marks a log as failed with error details.

**Changes:**
- `status` → `"failed"`
- `error_message` → description of the failure
- `extra_metadata` → merged with existing metadata (error codes, stack traces)
- `updated_at` → current timestamp
- Commits immediately

**Example:**
```python
try:
    await publish_to_instagram(log)
except Exception as e:
    await mark_log_failed(
        db,
        log,
        error_message=str(e),
        extra_metadata={"error_type": type(e).__name__}
    )
```

## Concurrency Handling

### PostgreSQL (Production)

Uses `SELECT FOR UPDATE SKIP LOCKED` for safe concurrent queue processing.

**How it works:**
1. Multiple workers can call `fetch_next_pending_log()` simultaneously
2. Each worker acquires a lock on a different pending log
3. Locked rows are skipped by other workers (`SKIP LOCKED`)
4. No worker ever receives the same log twice

**Advantages:**
- ✅ True concurrent processing with multiple workers
- ✅ No race conditions
- ✅ Optimal throughput

**Query:**
```sql
SELECT * FROM publish_logs
WHERE status = 'pending'
ORDER BY requested_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

---

### SQLite (Development/Testing)

SQLite **does not support** `SKIP LOCKED`, so the behavior is different.

**How it works:**
1. Uses `SELECT FOR UPDATE` (largely ignored by SQLite)
2. Relies on serialized transaction isolation
3. In tests, each test uses an isolated transaction, preventing conflicts
4. In production with SQLite, **only one worker should process the queue**

**Limitations:**
- ⚠️ Concurrent workers may pick up the same log (race condition)
- ⚠️ Best effort: works well for single-worker setups
- ⚠️ Tests are safe due to transaction isolation per test

**Recommendation:**
For production deployments with high concurrency requirements, use **PostgreSQL**.

## Transaction Policy

**All functions commit automatically.**

This design ensures that status updates are immediately visible to other processes:
- `mark_log_processing()` commits → other workers see the log as "processing"
- `mark_log_success()` commits → monitoring sees the log as "success"
- `mark_log_failed()` commits → retry logic sees the log as "failed"

If you need to batch multiple operations, wrap them in a parent transaction:

```python
async with db.begin():
    log = await fetch_next_pending_log(db)
    # The function will commit internally, but parent transaction
    # can still control rollback if needed
```

## Integration with Publishing Engine

This queue module is **independent** of the publishing engine logic.

**PASO 4.1 (Current):** Queue infrastructure only
- ✅ `publishing_queue/queue.py` provides queue operations
- ✅ Tests verify queue behavior
- ❌ No worker loop yet

**PASO 4.2 (Next):** Worker implementation
- Will create `publishing_queue/worker.py`
- Worker loop will:
  1. Call `fetch_next_pending_log()`
  2. Call `publishing_engine.service.publish_clip()`
  3. Call `mark_log_success()` or `mark_log_failed()`

**PASO 4.3 (Future):** Advanced features
- Retry logic for failed logs
- Priority queues (urgent publications first)
- Scheduled publications (process at specific times)
- Rate limiting per platform

## Usage Examples

### Simple Queue Processing (Manual)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.publishing_queue import (
    fetch_next_pending_log,
    mark_log_processing,
    mark_log_success,
    mark_log_failed,
)

async def process_one_log(db: AsyncSession):
    """Process a single pending log."""
    # Fetch next pending log
    log = await fetch_next_pending_log(db)
    if not log:
        print("Queue is empty")
        return
    
    # Mark as processing
    await mark_log_processing(db, log)
    
    try:
        # Simulate publishing (replace with real logic in PASO 4.2)
        result = await publish_to_platform(log)
        
        # Mark success
        await mark_log_success(
            db,
            log,
            external_post_id=result["post_id"],
            external_url=result["url"]
        )
        print(f"Published log {log.id} successfully")
        
    except Exception as e:
        # Mark failure
        await mark_log_failed(db, log, error_message=str(e))
        print(f"Failed to publish log {log.id}: {e}")
```

### Queue Monitoring

```python
from sqlalchemy import select, func
from app.models.database import PublishLogModel

async def get_queue_stats(db: AsyncSession) -> dict:
    """Get current queue statistics."""
    result = await db.execute(
        select(
            PublishLogModel.status,
            func.count(PublishLogModel.id).label("count")
        )
        .group_by(PublishLogModel.status)
    )
    
    stats = {row.status: row.count for row in result}
    return stats

# Example output:
# {
#     "pending": 42,
#     "processing": 3,
#     "success": 1205,
#     "failed": 15
# }
```

## Testing

Tests are located in `tests/test_publishing_queue.py`:

- ✅ `test_fetch_next_pending_log_returns_oldest` - FIFO ordering
- ✅ `test_fetch_next_pending_log_returns_none_when_empty` - Empty queue handling
- ✅ `test_mark_log_processing_changes_status` - Status update to "processing"
- ✅ `test_mark_log_success_fills_fields` - Success with external IDs
- ✅ `test_mark_log_failed_fills_error` - Failure with error message
- ✅ `test_fetch_next_pending_log_ignores_non_pending` - Only fetches "pending" logs

Run tests:
```bash
pytest tests/test_publishing_queue.py -v
```

## Future Enhancements (PASO 4.3+)

1. **Retry Logic**
   - Automatically retry failed logs after backoff period
   - Max retry count before permanent failure

2. **Priority Queue**
   - Add `priority` field to publish_logs
   - Process high-priority logs first

3. **Scheduled Publishing**
   - Add `scheduled_for` timestamp
   - Only process logs when `scheduled_for <= now()`

4. **Rate Limiting**
   - Respect platform API rate limits (e.g., Instagram: 25 posts/day)
   - Track publication counts per platform per day

5. **Dead Letter Queue**
   - Move permanently failed logs to separate table
   - Alerting for investigation

6. **Batch Processing**
   - Process multiple logs in parallel (up to platform limits)
   - Optimal resource utilization

## References

- `app/models/database.py` - PublishLogModel schema
- `app/publishing_engine/service.py` - Publishing logic
- `tests/test_publishing_queue.py` - Queue tests
- PostgreSQL Locking: https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE
