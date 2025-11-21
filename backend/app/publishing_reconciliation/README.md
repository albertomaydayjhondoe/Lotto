# Publishing Reconciliation Module

Automatic reconciliation of publication status based on webhook callbacks and timeout rules.

## Overview

This module reconciles the state of publish_logs that have been stuck in "processing" or "retry" status for an extended period. It uses webhook data and timeout rules to determine if publications were successful or failed.

## Problem Statement

When publishing to social media platforms:
1. Worker calls the API → receives `external_post_id`
2. API processes asynchronously → sends webhook when complete
3. If webhook never arrives → log stays in "processing" forever

Reconciliation solves this by:
- Checking for webhook data in `extra_metadata`
- Timing out stale logs after X minutes
- Marking logs as success or failed accordingly

## Architecture

```
POST /publishing/reconcile?since_minutes=10
         ↓
    router.py
         ↓
    recon.py: reconcile_publications()
         ↓
  1. Query logs with status="processing" or "retry"
     WHERE updated_at < (now - since_minutes)
  2. For each log:
     - Check extra_metadata["webhook_received"]
     - If webhook_received && status=="published" → mark_log_success()
     - If !webhook_received → mark_log_failed()
  3. Log "publish_reconciled" events
  4. Return statistics
```

## reconcile_publications Function

**Signature:**
```python
async def reconcile_publications(
    db: AsyncSession,
    *,
    since_minutes: int = 10
) -> Dict[str, Any]
```

**Logic:**

1. **Find Stale Logs:**
   ```sql
   SELECT * FROM publish_logs
   WHERE status IN ('processing', 'retry')
     AND updated_at < (now() - since_minutes)
   ORDER BY updated_at ASC
   ```

2. **Check Webhook Data:**
   - If `extra_metadata["webhook_received"] == True` AND `extra_metadata["webhook_status"] == "published"`
     → Call `mark_log_success()`
   - If `extra_metadata["webhook_received"] == False` or missing
     → Call `mark_log_failed()` with error "No webhook received after X minutes"

3. **Log Events:**
   - Event type: `publish_reconciled`
   - Severity: "info" (success) or "warn" (failed)
   - Metadata: platform, action, reason

4. **Return Statistics:**
   ```json
   {
     "total_checked": 15,
     "marked_success": 8,
     "marked_failed": 5,
     "skipped": 2,
     "success_log_ids": ["uuid1", ...],
     "failed_log_ids": ["uuid3", ...]
   }
   ```

## API Endpoint

**POST /publishing/reconcile**

**Query Parameters:**
- `since_minutes` (int): Look-back period in minutes (default: 10, min: 1, max: 1440)

**Example Usage:**
```bash
# Reconcile logs from last 10 minutes (default)
curl -X POST http://localhost:8000/publishing/reconcile

# Reconcile logs from last 30 minutes
curl -X POST "http://localhost:8000/publishing/reconcile?since_minutes=30"

# Reconcile logs from last 24 hours
curl -X POST "http://localhost:8000/publishing/reconcile?since_minutes=1440"
```

**Response Example:**
```json
{
  "total_checked": 15,
  "marked_success": 8,
  "marked_failed": 5,
  "skipped": 2,
  "success_log_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "c9bf9e57-1685-4c89-bafb-ff5af830be8a"
  ],
  "failed_log_ids": [
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
  ]
}
```

## Integration with Webhooks

### Flow Example

1. **Worker publishes clip:**
   ```python
   result = await publish_clip(db, request)
   # Creates PublishLog with status="processing", external_post_id="ig_123"
   ```

2. **Instagram sends webhook:**
   ```bash
   POST /publishing/webhooks/instagram
   {
     "external_post_id": "ig_123",
     "media_url": "https://instagram.com/p/ABC/",
     "status": "published"
   }
   # Updates extra_metadata["webhook_received"] = True
   ```

3. **Reconciliation runs (manual or cron):**
   ```python
   result = await reconcile_publications(db, since_minutes=10)
   # Finds log with external_post_id="ig_123"
   # Sees webhook_received=True, status="published"
   # Calls mark_log_success()
   # Log now has status="success"
   ```

4. **If webhook never arrives:**
   ```python
   result = await reconcile_publications(db, since_minutes=10)
   # Finds log with external_post_id="ig_123"
   # Sees webhook_received=False (or missing)
   # Calls mark_log_failed(error_message="No webhook received after 10 minutes")
   # Log now has status="failed"
   ```

## Scheduling Reconciliation

### Option 1: Cron Job

```bash
# Every 15 minutes
*/15 * * * * curl -X POST http://localhost:8000/publishing/reconcile?since_minutes=20
```

### Option 2: Background Worker

```python
import asyncio
from app.publishing_reconciliation import reconcile_publications

async def reconciliation_worker(db):
    while True:
        try:
            result = await reconcile_publications(db, since_minutes=15)
            logger.info(f"Reconciliation: {result}")
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
        await asyncio.sleep(900)  # 15 minutes
```

### Option 3: APScheduler

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=15)
async def scheduled_reconciliation():
    async for db in get_db():
        await reconcile_publications(db, since_minutes=20)

scheduler.start()
```

## Event Logging

Reconciliation logs `publish_reconciled` events to SocialSyncLedger:

**Success Event:**
```json
{
  "event_type": "publish_reconciled",
  "severity": "info",
  "entity_type": "publish_log",
  "entity_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "metadata": {
    "platform": "instagram",
    "action": "marked_success",
    "reason": "webhook_confirmed",
    "external_post_id": "ig_post_123"
  }
}
```

**Failure Event:**
```json
{
  "event_type": "publish_reconciled",
  "severity": "warn",
  "entity_type": "publish_log",
  "entity_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "metadata": {
    "platform": "tiktok",
    "action": "marked_failed",
    "reason": "webhook_timeout",
    "timeout_minutes": 10
  }
}
```

## Reconciliation Metadata

When reconciliation marks a log, it adds metadata to `extra_metadata`:

```json
{
  "reconciled": true,
  "reconciled_at": "2024-01-15T10:45:00Z",
  "reconciliation_reason": "webhook_confirmed"  // or "webhook_timeout"
}
```

This allows tracking which logs were auto-reconciled vs manually confirmed.

## Status Transitions

```
pending → processing → [webhook arrives] → reconcile → success
pending → processing → [no webhook] → reconcile → failed
pending → retry → [webhook arrives] → reconcile → success
pending → retry → [no webhook + timeout] → reconcile → failed
```

## Configuration

**Timeout Settings:**
- **since_minutes**: How far back to look for stale logs
  - Development: 5-10 minutes
  - Production: 10-30 minutes
  - Depends on platform API latency

**Reconciliation Frequency:**
- Every 15 minutes (recommended)
- More frequent for high-volume systems
- Less frequent for low-volume or batch systems

## Testing

See `backend/tests/test_publishing_reconciliation.py` for comprehensive tests:
- `test_reconcile_marks_success_when_data_present`
- `test_reconcile_marks_failed_after_timeout`
- `test_reconcile_skips_success_logs`
- `test_reconcile_respects_time_window`

## Monitoring

**Key Metrics:**
- `total_checked`: Number of stale logs found
- `marked_success`: Successfully reconciled
- `marked_failed`: Timed out logs
- `skipped`: Unclear state (needs investigation)

**Alerts:**
- High `marked_failed` rate → platform webhook issues
- High `skipped` rate → incomplete webhook data
- Zero `total_checked` for extended period → all systems healthy

## Future Enhancements

1. **Platform-Specific Timeouts**: Different timeout values per platform
2. **Retry Before Fail**: Auto-retry once before marking as failed
3. **Manual Override**: API to manually mark logs as success/failed
4. **Reconciliation History**: Track all reconciliation attempts
5. **Batch Reconciliation**: Process logs in batches for efficiency
6. **Smart Scheduling**: Reconcile more frequently during peak hours
