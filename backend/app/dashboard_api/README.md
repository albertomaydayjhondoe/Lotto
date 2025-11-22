# Dashboard API Module

Internal API layer for administrative panel backend. Provides aggregated statistics and metrics endpoints for monitoring the Stakazo publishing system.

## Overview

This module exposes read-only REST API endpoints that aggregate data from the database to provide real-time insights into:
- System-wide statistics (videos, clips, jobs, campaigns)
- Publication queue metrics
- Orchestrator activity
- Platform-specific performance
- Campaign status summaries

**Note**: This is PASO 6.1 - **Backend API only**. No frontend/UI is included (that's PASO 6.2).

## Architecture

```
┌──────────────────────┐
│   FastAPI Router     │  ← Exposes /dashboard/* endpoints
│   (router.py)        │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│   Service Layer      │  ← Business logic + optimized queries
│   (service.py)       │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│   Pydantic Schemas   │  ← Response models
│   (schemas.py)       │
└──────────────────────┘
```

## Endpoints

All endpoints are prefixed with `/dashboard` and tagged as `dashboard`.

### 1. GET /dashboard/stats/overview

**Summary**: Global system statistics

**Response Schema**: `OverviewStats`

```json
{
  "total_videos": 150,
  "total_clips": 320,
  "total_jobs": 89,
  "total_campaigns": 12,
  "pending_jobs": 5,
  "processing_jobs": 2,
  "failed_jobs": 8,
  "success_logs": 245,
  "failed_logs": 23,
  "scheduled_publications": 42
}
```

**Metrics**:
- `total_videos`: Count of all VideoAsset records
- `total_clips`: Count of all Clip records
- `total_jobs`: Count of all Job records
- `total_campaigns`: Count of all Campaign records
- `pending_jobs`: Jobs with status='pending'
- `processing_jobs`: Jobs with status='processing'
- `failed_jobs`: Jobs with status='failed'
- `success_logs`: PublishLogModel records with status='success'
- `failed_logs`: PublishLogModel records with status='failed'
- `scheduled_publications`: PublishLogModel records with status='pending'

**Queries**: 6 aggregation queries (total, jobs by status, campaigns, publish logs)

---

### 2. GET /dashboard/stats/queue

**Summary**: Publication queue statistics

**Response Schema**: `QueueStats`

```json
{
  "pending": 15,
  "processing": 3,
  "success": 189,
  "failed": 12,
  "avg_processing_time_ms": 2345.67,
  "oldest_pending_age_seconds": 3600.0
}
```

**Metrics**:
- `pending`: Queue items with status='pending'
- `processing`: Queue items with status='processing'
- `success`: Queue items with status='success'
- `failed`: Queue items with status='failed'
- `avg_processing_time_ms`: Average time from requested_at to published_at (milliseconds)
- `oldest_pending_age_seconds`: Age of oldest pending item (seconds from requested_at to now)

**Calculation Details**:
```python
# Processing time calculation
processing_time_ms = (published_at - requested_at) * 1000

# Age calculation  
age_seconds = (now - requested_at).total_seconds()
```

**Queries**: 3 queries (status counts, avg processing time, oldest pending)

---

### 3. GET /dashboard/stats/orchestrator

**Summary**: Orchestrator activity metrics

**Response Schema**: `OrchestratorStats`

```json
{
  "last_run_at": "2025-11-22T10:30:00",
  "actions_last_run": 5,
  "actions_last_24h": 87,
  "queue_saturation": 0.35,
  "active_workers": 4
}
```

**Metrics**:
- `last_run_at`: Timestamp of most recent publish log creation (proxy for orchestrator run)
- `actions_last_run`: Publish logs created in last hour (simulated orchestrator run)
- `actions_last_24h`: Publish logs created in last 24 hours
- `queue_saturation`: Ratio of active items (pending+processing) to total items (0.0-1.0)
- `active_workers`: Count of unique social_account_id with processing status

**Queue Saturation Formula**:
```python
saturation = (pending + processing) / total_logs
saturation = min(saturation, 1.0)  # Cap at 1.0
```

**Queries**: 5 queries (last run, 24h actions, 1h actions, saturation, workers)

---

### 4. GET /dashboard/stats/platforms

**Summary**: Platform-specific statistics

**Response Schema**: `PlatformStats`

```json
{
  "instagram": {
    "clips_ready": 45,
    "clips_published": 123,
    "avg_score": 0.78,
    "jobs_completed": 89,
    "jobs_failed": 5
  },
  "tiktok": {
    "clips_ready": 32,
    "clips_published": 98,
    "avg_score": 0.82,
    "jobs_completed": 67,
    "jobs_failed": 3
  },
  "youtube": {
    "clips_ready": 18,
    "clips_published": 56,
    "avg_score": 0.85,
    "jobs_completed": 45,
    "jobs_failed": 2
  },
  "other": {
    "clips_ready": 5,
    "clips_published": 12,
    "avg_score": 0.70,
    "jobs_completed": 8,
    "jobs_failed": 1
  }
}
```

**Per-Platform Metrics**:
- `clips_ready`: Distinct clips with publish logs in pending/scheduled status for this platform
- `clips_published`: Distinct clips with publish logs in success status for this platform
- `avg_score`: Average visual_score from clips associated with this platform's logs
- `jobs_completed`: Jobs with status='completed' and params.platform=<platform>
- `jobs_failed`: Jobs with status='failed' and params.platform=<platform>

**Implementation Note**: Platform association is via `PublishLogModel.platform` field, not direct clip field.

**Queries**: 5 queries per platform × 4 platforms = 20 total queries

---

### 5. GET /dashboard/stats/campaigns

**Summary**: Campaign status summary

**Response Schema**: `CampaignStats`

```json
{
  "draft": 3,
  "active": 8,
  "paused": 2,
  "completed": 15,
  "total_budget_spent": 0.0
}
```

**Metrics**:
- `draft`: Campaigns with status='draft'
- `active`: Campaigns with status='active'
- `paused`: Campaigns with status='paused'
- `completed`: Campaigns with status='completed'
- `total_budget_spent`: Sum of budget spent (currently simulated as 0.0, structure ready)

**Queries**: 1 aggregation query

---

## Query Optimization

### Design Principles

1. **No N+1 Queries**: All aggregations use single SQL queries with GROUP BY or CASE statements
2. **Efficient Aggregations**: Use SQLAlchemy `func.count()`, `func.sum()`, `func.avg()` instead of loops
3. **Async Queries**: All database calls use async SQLAlchemy sessions
4. **Minimal Data Transfer**: Only retrieve aggregate results, not full rows

### Example Optimization

**❌ Bad (N+1 queries)**:
```python
jobs = await db.execute(select(Job))
pending_count = 0
for job in jobs:
    if job.status == "pending":
        pending_count += 1
```

**✅ Good (Single aggregation query)**:
```python
result = await db.execute(
    select(func.sum(case((Job.status == JobStatus.PENDING, 1), else_=0)))
)
pending_count = result.scalar() or 0
```

### Query Patterns

**Status Counts**:
```python
select(
    func.sum(case((Model.status == "status1", 1), else_=0)).label("count1"),
    func.sum(case((Model.status == "status2", 1), else_=0)).label("count2")
)
```

**Time Calculations**:
```python
select(
    func.avg(
        (func.extract('epoch', end_time) - func.extract('epoch', start_time)) * 1000
    )
)
```

**JSON Field Filtering**:
```python
from sqlalchemy import cast, String
select(...).where(cast(Job.params["platform"], String) == "instagram")
```

## Integration with Main App

Added to `main.py`:

```python
from app.dashboard_api import dashboard_router

app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
```

**OpenAPI Documentation**: Available at `/docs` with full schema definitions

## Usage Examples

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
    # Get overview
    response = await client.get("/dashboard/stats/overview")
    stats = response.json()
    print(f"Total clips: {stats['total_clips']}")
    
    # Get queue stats
    response = await client.get("/dashboard/stats/queue")
    queue = response.json()
    print(f"Pending: {queue['pending']}, Processing: {queue['processing']}")
    
    # Get platform breakdown
    response = await client.get("/dashboard/stats/platforms")
    platforms = response.json()
    print(f"Instagram ready: {platforms['instagram']['clips_ready']}")
```

### cURL

```bash
# Overview stats
curl http://localhost:8000/dashboard/stats/overview

# Queue stats
curl http://localhost:8000/dashboard/stats/queue

# Platform stats
curl http://localhost:8000/dashboard/stats/platforms

# Orchestrator stats
curl http://localhost:8000/dashboard/stats/orchestrator

# Campaign stats
curl http://localhost:8000/dashboard/stats/campaigns
```

### JavaScript (Fetch API)

```javascript
// Get all stats concurrently
const [overview, queue, orchestrator, platforms, campaigns] = await Promise.all([
  fetch('/dashboard/stats/overview').then(r => r.json()),
  fetch('/dashboard/stats/queue').then(r => r.json()),
  fetch('/dashboard/stats/orchestrator').then(r => r.json()),
  fetch('/dashboard/stats/platforms').then(r => r.json()),
  fetch('/dashboard/stats/campaigns').then(r => r.json())
]);

console.log('System Overview:', overview);
console.log('Queue Saturation:', orchestrator.queue_saturation);
```

## Database Schema Dependencies

### Tables Used

- `video_assets`: Video storage
- `clips`: Generated clip segments
- `jobs`: Processing tasks
- `campaigns`: Ad campaigns
- `publish_logs`: Publication tracking (primary data source for queue/platform stats)

### Key Relationships

```
VideoAsset 1──N Clip
VideoAsset 1──N Job
Clip 1──N PublishLogModel
Clip 1──N Campaign
Job N──1 Clip (optional)
```

## Performance Considerations

### Expected Query Times

| Endpoint | Queries | Typical Time |
|----------|---------|--------------|
| /stats/overview | 6 | < 100ms |
| /stats/queue | 3 | < 50ms |
| /stats/orchestrator | 5 | < 80ms |
| /stats/platforms | 20 | < 200ms |
| /stats/campaigns | 1 | < 30ms |

### Optimization Strategies

1. **Database Indexing**: Add indexes on frequently queried fields:
   ```sql
   CREATE INDEX idx_jobs_status ON jobs(status);
   CREATE INDEX idx_publish_logs_status ON publish_logs(status);
   CREATE INDEX idx_publish_logs_platform ON publish_logs(platform);
   CREATE INDEX idx_campaigns_status ON campaigns(status);
   ```

2. **Caching**: Add Redis cache for dashboard stats (TTL: 30 seconds):
   ```python
   @cache(ttl=30)
   async def get_overview_stats(db):
       ...
   ```

3. **Connection Pooling**: Ensure async database pool is configured:
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=10
   )
   ```

## Testing

### Running Tests

```bash
# Run all dashboard API tests
pytest backend/tests/test_dashboard_api.py -v

# Run specific test
pytest backend/tests/test_dashboard_api.py::test_overview_stats -v

# Run with coverage
pytest backend/tests/test_dashboard_api.py --cov=app.dashboard_api -v
```

### Test Coverage

**10 comprehensive tests** covering:
1. ✅ Overview stats with sample data
2. ✅ Queue stats with sample data
3. ✅ Orchestrator stats with sample data
4. ✅ Platform stats with sample data
5. ✅ Campaign stats with sample data
6. ✅ Empty database returns zeros (no crashes)
7. ✅ Optional fields handling (None values)
8. ✅ Schema validation (Pydantic model serialization)
9. ✅ Processing time calculation accuracy
10. ✅ Platform stats aggregation correctness

### Test Results

```
==================== 10 passed, 206 warnings in 1.23s ====================
```

## Error Handling

### Graceful Degradation

All endpoints handle edge cases gracefully:

- **Empty database**: Returns zeros, not errors
- **Missing optional fields**: Uses None or 0.0 as default
- **Division by zero**: Checks before calculating ratios
- **No data in timeframe**: Returns 0 for counts, None for averages

### Example Error Prevention

```python
# Safe division
if total_count > 0:
    saturation = min(active_count / total_count, 1.0)
else:
    saturation = 0.0

# Safe average
avg_score = avg_score_result.scalar()
avg_score = float(avg_score) if avg_score is not None else 0.0

# Safe age calculation
if oldest_pending:
    age_delta = datetime.utcnow() - oldest_pending
    oldest_pending_age_seconds = age_delta.total_seconds()
else:
    oldest_pending_age_seconds = None
```

## Future Enhancements (PASO 6.2+)

1. **WebSocket Support**: Real-time stats streaming
2. **Historical Data**: Time-series endpoints for trends
3. **Filtering**: Query parameters for date ranges, specific platforms
4. **Pagination**: For endpoints with large result sets
5. **Export**: CSV/Excel download functionality
6. **Alerts**: Configurable thresholds with notifications
7. **Custom Dashboards**: User-defined metric combinations

## Security Considerations

**Current Status**: No authentication required (internal API)

**Production Recommendations**:
1. Add API key authentication
2. Rate limiting per client
3. IP whitelist for internal network only
4. CORS restrictions
5. Audit logging for sensitive endpoints

```python
# Example security middleware
@router.get("/stats/overview", dependencies=[Depends(verify_api_key)])
async def overview_stats_endpoint(...):
    ...
```

## Troubleshooting

### Common Issues

**Issue**: "Queue saturation always 0.0"
- **Cause**: No publish logs in database
- **Solution**: Verify publishing engine is creating logs

**Issue**: "Platform stats all zeros"
- **Cause**: PublishLogModel.platform field not populated
- **Solution**: Check publishing worker sets platform correctly

**Issue**: "Slow response times"
- **Cause**: Missing database indexes
- **Solution**: Run index creation SQL (see Performance section)

**Issue**: "avg_processing_time_ms is negative"
- **Cause**: published_at before requested_at (data error)
- **Solution**: Fixed in service layer with proper epoch extraction

## Module Structure

```
backend/app/dashboard_api/
├── __init__.py          # Module exports
├── router.py            # FastAPI endpoints (114 lines)
├── service.py           # Business logic + queries (338 lines)
├── schemas.py           # Pydantic response models (241 lines)
└── README.md            # This file
```

## Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: Async ORM + query builder
- **Pydantic**: Response validation
- **Python 3.12+**: Async/await support

No additional packages required beyond existing project dependencies.

## License

Part of Stakazo publishing system - PASO 6.1 implementation.
