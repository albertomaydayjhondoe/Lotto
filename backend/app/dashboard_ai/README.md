# Dashboard AI - Intelligent Analysis & Actions Layer

## 📋 Overview

The Dashboard AI module is an intelligent layer built on top of the Stakazo dashboard that provides:

- **Real-time System Analysis**: Automated health monitoring and metrics analysis
- **AI-Generated Recommendations**: Context-aware suggestions for system optimization
- **One-Click Actions**: Direct execution of orchestrator, scheduler, and publishing operations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Frontend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ AI Overview │  │ Recommend.  │  │   Actions   │         │
│  │    Page     │  │    Page     │  │    Page     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                 │                 │                 │
│  ┌──────▼─────────────────▼─────────────────▼──────┐        │
│  │           AI Hooks & API Client                  │        │
│  └──────────────────────┬─────────────────────────┘         │
└─────────────────────────┼──────────────────────────────────┘
                          │ HTTP/JSON
┌─────────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Dashboard AI Router                        │   │
│  │  /dashboard/ai/analyze                               │   │
│  │  /dashboard/ai/recommendations                       │   │
│  │  /dashboard/ai/execute                               │   │
│  └──────┬──────────────────────────────────────────────┘   │
│         │                                                    │
│  ┌──────▼───────────┐         ┌───────────────────┐        │
│  │    Analyzer      │         │   Recommender     │        │
│  │                  │         │                   │        │
│  │ - Health Calc    │         │ - Publish Best    │        │
│  │ - Issue Detect   │◄────────┤ - Run Orch Tick   │        │
│  │ - Metrics Agg    │         │ - Rebalance Queue │        │
│  └──────┬───────────┘         │ - Retry Failed    │        │
│         │                     └───────────────────┘        │
│  ┌──────▼─────────────────────────────────────────────┐   │
│  │         Dashboard Actions Router                    │   │
│  │  /dashboard/actions/force-publish                   │   │
│  │  /dashboard/actions/retry-failed                    │   │
│  │  /dashboard/actions/run-orchestrator                │   │
│  │  /dashboard/actions/run-scheduler                   │   │
│  │  /dashboard/actions/rebalance-queue                 │   │
│  │  ... (10 total actions)                             │   │
│  └──────┬──────────────────────────────────────────────┘   │
│         │                                                    │
│  ┌──────▼───────────┐                                       │
│  │ Actions Executor │                                       │
│  │                  │                                       │
│  │ Delegates to:    │                                       │
│  │ - Orchestrator   │                                       │
│  │ - Scheduler      │                                       │
│  │ - Publishing     │                                       │
│  │ - Queue Worker   │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

### Analysis Flow

```
Database State
    ↓
Dashboard API (PASO 6.1)
    ↓
Analyzer
    ├─ Calculate Health Statuses
    ├─ Detect Issues
    ├─ Find Best Clips
    └─ Aggregate Metrics
    ↓
SystemAnalysis Object
    ↓
Frontend (React Query Cache)
    ↓
UI Components (Health Cards, Charts, Issues List)
```

### Recommendation Flow

```
SystemAnalysis
    ↓
Recommender
    ├─ Analyze Current State
    ├─ Apply Rules & Heuristics
    └─ Generate Recommendations
    ↓
List[Recommendation]
    ├─ Sorted by Severity
    ├─ With Action Payloads
    └─ Executable
    ↓
Frontend
    ↓
User Clicks "Execute"
    ↓
POST /dashboard/ai/execute
    ↓
Actions Executor
    ↓
System Operation Performed
```

## 🔍 Analyzer Module

**Location**: `backend/app/dashboard_ai/analyzer.py`

### Health Calculation

```python
Queue Health:
  - Good: < 30 items, < 15% failed rate
  - Warning: 30-50 items, 15-30% failed rate
  - Critical: > 50 items, > 30% failed rate

Orchestrator Health:
  - Good: saturation < 70%
  - Warning: saturation 70-90%
  - Critical: saturation > 90%

Campaigns Health:
  - Good: < 15% failed jobs
  - Warning: 15-30% failed jobs, > 20 pending
  - Critical: > 30% failed jobs
```

### Detected Issues

1. **Queue Overload** (Critical): > 50 items in queue
2. **High Saturation** (Warning): 30-50 items in queue
3. **Multiple Failed Publications** (Warning): > 10 failed items
4. **Orchestrator Overloaded** (Critical): Saturation > 90%
5. **Orchestrator High Load** (Warning): Saturation 70-90%
6. **Low Success Rate** (Critical): < 70% success
7. **Below Target Success Rate** (Warning): < 85% success
8. **Pending Jobs Accumulating** (Warning): > 20 pending jobs
9. **Stale Pending Publications** (Warning): Oldest > 2 hours old

## 💡 Recommender Module

**Location**: `backend/app/dashboard_ai/recommender.py`

### Recommendation Types

| Action | Severity | Trigger Condition |
|--------|----------|-------------------|
| `publish` | info | High-scoring clip available (> 0.8) |
| `run_orchestrator` | critical | Orchestrator saturated (> 90%) |
| `run_orchestrator` | warning | Orchestrator elevated (> 70%) |
| `rebalance_queue` | critical | Queue overloaded (> 50 items) |
| `rebalance_queue` | warning | Queue moderately loaded (> 30 items) |
| `retry` | warning | Multiple failed publications detected |
| `run_scheduler` | info | Many pending items (> 20) |
| `promote` | info | Inactive campaigns (no activity in 7 days) |
| `optimize_schedule` | info | Low activity on platforms (< 5 posts) |
| `clear_failed` | info | High failed rate (> 20%) |

## ⚡ Actions Executor

**Location**: `backend/app/dashboard_actions/executor.py`

### Available Actions

#### 1. force_publish
Immediately publish a clip to a platform.

```python
Payload:
{
  "clip_id": "uuid",
  "platform": "instagram",  # optional
  "account_id": "uuid"      # optional
}
```

#### 2. retry_failed
Reset all failed publications to pending status.

```python
Payload: {}
Result: {"retry_count": 15}
```

#### 3. run_orchestrator_tick
Manually trigger orchestrator decision cycle.

```python
Payload: {}
Result: {
  "actions_executed": 5,
  "decisions_made": 12
}
```

#### 4. run_scheduler_tick
Process pending clips and schedule publications.

```python
Payload: {
  "dry_run": false  # optional
}
Result: {
  "scheduled_count": 20,
  "dry_run": false
}
```

#### 5. rebalance_queue
Optimize scheduled times with even distribution.

```python
Payload: {}
Result: {"rebalanced_count": 30}
```

#### 6. promote_clip
Add best clip from video to a campaign.

```python
Payload: {
  "video_id": "uuid",
  "campaign_id": "uuid"  # optional
}
```

#### 7. publish_best_clip
Publish highest-scoring clip from a video.

```python
Payload: {
  "video_id": "uuid",
  "platform": "instagram"  # optional
}
```

#### 8. reschedule
Change publication scheduled time.

```python
Payload: {
  "log_id": "uuid",
  "new_time": "2025-11-22T14:00:00"
}
```

#### 9. clear_failed
Remove old failed publication records.

```python
Payload: {
  "older_than_days": 7  # default
}
```

#### 10. optimize_schedule
Adjust schedules to optimal time windows.

```python
Payload: {
  "platforms": ["instagram", "tiktok"]
}
```

## 🎨 Frontend Components

### Pages

#### `/dashboard/ai` - AI Overview
- 4 health status cards (queue, orchestrator, campaigns, success rate)
- 2 charts (platform distribution, system metrics)
- 3 key metrics cards
- Best clips per platform grid
- Issues list

#### `/dashboard/ai/recommendations` - Recommendations
- Grouped by severity (critical, warning, info)
- Interactive recommendation cards
- One-click execute buttons
- Real-time refresh

#### `/dashboard/ai/actions` - Manual Actions
- Critical actions section (orchestrator, scheduler)
- Queue management section
- System operations section
- Action guidelines

### UI Components

#### HealthCard
Status indicator with icon, badge, and metric display.

```tsx
<HealthCard
  title="Queue Health"
  status="good"
  metric="15 pending"
  description="Publishing queue status"
/>
```

#### RecommendationCard
Interactive card with severity indicator and execute button.

```tsx
<RecommendationCard
  recommendation={rec}
  onExecute={handleExecute}
  isExecuting={executing}
/>
```

#### ActionButton
Button with loading state for manual actions.

```tsx
<ActionButton
  label="Run Orchestrator"
  onClick={handleAction}
  isLoading={loading}
  icon={<Zap />}
  variant="destructive"
/>
```

#### IssuesList
Organized list of detected issues with severity badges.

```tsx
<IssuesList issues={analysis.issues_detected} />
```

## 🔌 API Integration

### React Query Hooks

```typescript
// Analysis
const { data, isLoading, error } = useSystemAnalysis()

// Recommendations
const { data: recommendations } = useRecommendations()

// Actions
const executeAction = useExecuteAction()
const retryFailed = useRetryFailed()
const runOrchestrator = useRunOrchestrator()
const runScheduler = useRunScheduler()
const rebalanceQueue = useRebalanceQueue()
```

### API Client

```typescript
import { aiApi } from "@/lib/ai/api"

// Get analysis
const analysis = await aiApi.getAnalysis()

// Get recommendations
const recs = await aiApi.getRecommendations()

// Execute action
const result = await aiApi.executeAction({
  action: "publish",
  payload: { clip_id: "..." }
})
```

## 📝 Example JSON Responses

### SystemAnalysis

```json
{
  "timestamp": "2025-11-22T10:30:00",
  "queue_health": "warning",
  "orchestrator_health": "good",
  "campaigns_status": "good",
  "publish_success_rate": 0.89,
  "pending_scheduled": 35,
  "best_clip_per_platform": {
    "instagram": {
      "clip_id": "550e8400-e29b-41d4-a716-446655440000",
      "variant_id": "550e8400-e29b-41d4-a716-446655440001",
      "score": 0.95,
      "duration": 30,
      "created_at": "2025-11-22T09:00:00"
    }
  },
  "issues_detected": [
    {
      "severity": "warning",
      "title": "High queue saturation",
      "description": "Publishing queue has 35 items."
    }
  ],
  "metrics": {
    "total_clips_ready": 78,
    "avg_processing_time_ms": 2145.5,
    "platform_distribution": {
      "instagram": 25,
      "tiktok": 30,
      "youtube": 15,
      "facebook": 8
    },
    "total_in_queue": 35,
    "failed_rate": 0.11
  }
}
```

### Recommendation

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Publish high-scoring Instagram clip",
  "description": "Clip with score 0.95 is ready for Instagram. Optimal for immediate publication.",
  "severity": "info",
  "action": "publish",
  "payload": {
    "clip_id": "550e8400-e29b-41d4-a716-446655440001",
    "variant_id": "550e8400-e29b-41d4-a716-446655440002",
    "platform": "instagram"
  },
  "created_at": "2025-11-22T10:30:00"
}
```

### ExecuteActionResponse

```json
{
  "success": true,
  "action": "rebalance_queue",
  "message": "Queue rebalanced: 35 items rescheduled",
  "result": {
    "rebalanced_count": 35
  },
  "executed_at": "2025-11-22T10:31:00"
}
```

## 🧪 Testing

### Backend Tests

**Location**: `backend/tests/test_dashboard_ai.py`, `backend/tests/test_dashboard_actions.py`

```bash
# Run AI tests
pytest backend/tests/test_dashboard_ai.py -v

# Run actions tests
pytest backend/tests/test_dashboard_actions.py -v
```

**Coverage**:
- 10 tests for analyzer and recommender
- 10 tests for actions executor
- Total: 20 tests

### Frontend Tests

Tests would be added to `dashboard/__tests__/` for AI components.

## 🚀 Usage Examples

### Get System Analysis

```python
# Backend
from app.dashboard_ai.analyzer import analyze_system

analysis = await analyze_system(db)
print(f"Queue health: {analysis.queue_health}")
print(f"Issues detected: {len(analysis.issues_detected)}")
```

```typescript
// Frontend
const { data } = useSystemAnalysis()
console.log(`Success rate: ${data.publish_success_rate * 100}%`)
```

### Execute Action

```python
# Backend
from app.dashboard_actions.executor import execute_action

result = await execute_action(
    action_type="retry",
    payload={},
    db=db
)
```

```typescript
// Frontend
const retryFailed = useRetryFailed()
await retryFailed.mutateAsync()
```

## 🔧 Configuration

No additional configuration required. The module uses existing:
- Database connection
- Dashboard API endpoints
- Orchestrator/Scheduler/Publishing services

## 📈 Performance

- Analysis query: ~200ms (aggregates from existing dashboard stats)
- Recommendations generation: ~150ms
- Action execution: Variable (depends on action type)
  - Simple actions (retry, clear): ~50ms
  - Complex actions (orchestrator tick): ~2-5s

## 🔐 Security

- All endpoints protected by same auth as dashboard
- Actions logged to ledger
- No sensitive data exposed in responses
- Rate limiting recommended for execute endpoint

## 🎯 Future Enhancements

1. **Machine Learning Integration**: Use historical data for smarter recommendations
2. **Scheduled Actions**: Queue actions for future execution
3. **Notification System**: Alert on critical issues
4. **Custom Rules Engine**: User-defined recommendation rules
5. **A/B Testing**: Test different strategies automatically
6. **Predictive Analytics**: Forecast system behavior
7. **Auto-Healing**: Execute critical actions automatically
8. **Recommendation History**: Track executed recommendations

## 📚 Related Documentation

- [Dashboard API (PASO 6.1)](../dashboard_api/README.md)
- [Dashboard UI (PASO 6.2)](../../dashboard/README.md)
- [Orchestrator](../orchestrator/README.md)
- [Publishing Scheduler](../publishing_scheduler/README.md)
- [Publishing Engine](../publishing_engine/README.md)

## 🐛 Troubleshooting

### Issue: Recommendations not updating
**Solution**: Check React Query refetch interval (default: 60s). Manually refresh with button.

### Issue: Action execution fails
**Solution**: Check backend logs for specific error. Verify related services are running.

### Issue: Health status incorrect
**Solution**: Verify dashboard API endpoints returning correct data. Check database connection.

## 📄 License

Part of the Stakazo project. Same license applies.
