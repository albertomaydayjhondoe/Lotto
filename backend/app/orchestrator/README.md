# Orchestrator - Autonomous Real-Time Orchestration

## Overview

The **Orchestrator** is the autonomous brain of the Stakazo system. It continuously monitors all subsystems, makes intelligent decisions, and executes actions automatically to maintain optimal system health and performance.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR CYCLE                      │
│                     (Every 2 seconds)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   1. MONITOR     │
                    │  (monitor.py)    │
                    │                  │
                    │  Gather snapshot │
                    │  of entire       │
                    │  system state    │
                    └────────┬─────────┘
                             │
                    Snapshot (JSON)
                             │
                             ▼
                    ┌──────────────────┐
                    │   2. DECIDE      │
                    │  (decider.py)    │
                    │                  │
                    │  Analyze data    │
                    │  Apply heuristics│
                    │  Decide actions  │
                    └────────┬─────────┘
                             │
                    Actions (List)
                             │
                             ▼
                    ┌──────────────────┐
                    │   3. EXECUTE     │
                    │  (executor.py)   │
                    │                  │
                    │  Invoke existing │
                    │  modules to      │
                    │  perform actions │
                    └────────┬─────────┘
                             │
                    Results (Report)
                             │
                             ▼
                    ┌──────────────────┐
                    │   4. LOG         │
                    │  (ledger)        │
                    │                  │
                    │  Record cycle    │
                    │  to audit trail  │
                    └──────────────────┘
                             │
                             ▼
                    Sleep 2s → Repeat
```

## Components

### 1. Monitor (`monitor.py`)

**Purpose:** Gather comprehensive system state snapshot

**Monitors:**
- **Jobs Queue:** pending, processing, retry, failed, completed counts
- **Publish Logs:** pending, scheduled, failed, retry, published counts
- **Scheduler:** Active publishing windows (Instagram 18-23h, TikTok 16-24h, YouTube 17-22h)
- **Campaigns:** Active campaigns with budgets
- **Clips:** Recent clips (24h), visual scores, high performers (>80)
- **Ledger:** Error tracking (last 1h)
- **System Health:** 0-100 score with status (healthy/degraded/critical)

**Health Scoring:**
- Start at 100 points
- Deduct 20 if queue saturated (>50 pending jobs)
- Deduct 15 if old jobs pending (>30min)
- Deduct 10 if publishing failures detected
- Deduct 5 per ledger error
- **Status:** healthy (≥80), degraded (50-79), critical (<50)

**Output:** JSON snapshot with all metrics

### 2. Decider (`decider.py`)

**Purpose:** Analyze snapshot and decide actions

**Action Types:**
1. `schedule_clip` - Schedule high-score clip during active window
2. `retry_failed_log` - Retry failed publication
3. `trigger_reconciliation` - Run reconciliation process
4. `promote_high_score_clip` - Prioritize clip with visual_score > 80
5. `downgrade_low_score_clip` - Postpone low-score clips
6. `force_publish` - Bypass scheduler for urgent clips
7. `rebalance_queue` - Redistribute when queue saturated

**Heuristics:**

| Condition | Action | Priority | Reason |
|-----------|--------|----------|--------|
| `queue_saturated = true` | rebalance_queue | 9 | Queue >50 pending jobs |
| `oldest_pending > 60min` | force_publish | 8 | Jobs stuck too long |
| `recent_failures_1h > 0` | retry_failed_log | 8 | Recent failures need attention |
| `high_score_clips + window_active` | promote_high_score_clip | 7 | Capitalize on quality + timing |
| `high_score_clips > 3` | schedule_clip | 6 | Accumulation of quality clips |
| `ledger.errors_1h > 5` | trigger_reconciliation | 7 | High error rate |
| `health_score < 50` | rebalance_queue (emergency) | 10 | Critical system state |
| `active_campaign + budget > $100` | schedule_clip | 9 | High-value campaign |
| `window_closing_soon` | schedule_clip | 8 | Window ending in 1h |
| `avg_visual_score < 40` | downgrade_low_score_clip | 3 | Low quality trend |

**Output:** Sorted list of `OrchestratorAction` objects

### 3. Executor (`executor.py`)

**Purpose:** Execute actions by invoking existing modules

**Execution Map:**

| Action Type | Module | Function |
|-------------|--------|----------|
| schedule_clip | publishing_intelligence | `analyze_and_publish()` or `schedule_optimal_publish()` |
| retry_failed_log | Direct DB update | Set status="scheduled", increment retry_count |
| trigger_reconciliation | publishing_reconciliation | `reconcile_publish_logs()` |
| promote_high_score_clip | publishing_intelligence | `analyze_and_publish()` for top clips |
| downgrade_low_score_clip | Direct DB update | Postpone scheduled_at +24h |
| force_publish | Direct DB update | Set status="pending", clear scheduled_at |
| rebalance_queue | Direct DB update | Emergency: fail old jobs (>2h) |

**Output:** Execution report with success/error counts

### 4. Runner (`runner.py`)

**Purpose:** Infinite async loop that runs the orchestrator

**Flow:**
```python
while orchestrator_running:
    cycle_start = now()
    
    # 1. Monitor
    snapshot = await monitor_system_state(db)
    
    # 2. Decide
    actions = decide_actions(snapshot)
    
    # 3. Execute
    if actions:
        results = await execute_actions(actions, db)
    
    # 4. Log
    await log_event(cycle_data)
    
    # 5. Sleep
    await asyncio.sleep(2)  # ORCHESTRATOR_INTERVAL_SECONDS
```

**Control Functions:**
- `start_orchestrator()` - Start background task
- `stop_orchestrator()` - Gracefully stop loop
- `is_orchestrator_running()` - Check status
- `run_orchestrator_once()` - Manual single cycle

### 5. Router (`router.py`)

**API Endpoints:**

#### GET `/orchestrator/snapshot`
Get current system state snapshot
```json
{
  "status": "ok",
  "snapshot": {
    "jobs": {...},
    "publish_logs": {...},
    "scheduler": {...},
    "campaigns": {...},
    "clips": {...},
    "ledger": {...},
    "system": {...}
  }
}
```

#### POST `/orchestrator/run-once`
Run single orchestrator cycle manually
```json
{
  "status": "ok",
  "result": {
    "snapshot": {...},
    "decision": {...},
    "execution": {...},
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### POST `/orchestrator/enable`
Start autonomous orchestrator loop
```json
{
  "status": "ok",
  "orchestrator": {
    "status": "started",
    "interval_seconds": 2,
    "enabled": true
  }
}
```

#### POST `/orchestrator/disable`
Stop autonomous orchestrator loop
```json
{
  "status": "ok",
  "orchestrator": {
    "status": "stopped"
  }
}
```

#### GET `/orchestrator/status`
Check if orchestrator is running
```json
{
  "status": "ok",
  "running": true
}
```

## Configuration

In `app/core/config.py`:

```python
# Orchestrator Configuration
ORCHESTRATOR_ENABLED: bool = False  # Set to True to auto-start
ORCHESTRATOR_INTERVAL_SECONDS: int = 2  # Cycle frequency
```

**Environment Variables:**
```bash
ORCHESTRATOR_ENABLED=true
ORCHESTRATOR_INTERVAL_SECONDS=2
```

## Integration

The orchestrator is registered in `main.py`:

```python
from app.orchestrator import orchestrator_router

app.include_router(orchestrator_router, tags=["orchestrator"])
```

To auto-start on application startup, add to lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Auto-start orchestrator if enabled
    if settings.ORCHESTRATOR_ENABLED:
        await start_orchestrator()
    
    yield
    
    # Graceful shutdown
    await stop_orchestrator()
```

## Usage Examples

### Manual Cycle
```bash
curl -X POST http://localhost:8000/orchestrator/run-once
```

### Enable Autonomous Mode
```bash
curl -X POST http://localhost:8000/orchestrator/enable
```

### Get System Snapshot
```bash
curl http://localhost:8000/orchestrator/snapshot
```

### Disable Orchestrator
```bash
curl -X POST http://localhost:8000/orchestrator/disable
```

## Testing

Run tests:
```bash
pytest tests/test_orchestrator.py -v
```

**Test Coverage:**
- ✅ Monitor detects pending jobs
- ✅ Monitor detects publishing failures
- ✅ Monitor detects high-score clips
- ✅ Monitor detects active campaigns
- ✅ Monitor detects ledger errors
- ✅ Decider suggests retry for failures
- ✅ Decider suggests promoting high-score clips
- ✅ Decider suggests rebalance for saturation
- ✅ Executor retries failed logs
- ✅ Decision summary generation
- ✅ Full orchestrator cycle integration
- ✅ Health score calculation
- ✅ Campaign prioritization
- ✅ Empty database handling

## Ledger Integration

Every orchestrator cycle logs to the ledger:

**Events:**
- `orchestrator.cycle_started` - Cycle begins with snapshot summary
- `orchestrator.cycle_completed` - Cycle ends with execution results
- `orchestrator.cycle_idle` - No actions needed, system healthy
- `orchestrator.cycle_error` - Cycle encountered error
- `orchestrator.action_executed` - Individual action succeeded
- `orchestrator.action_failed` - Individual action failed

**Query Example:**
```sql
SELECT * FROM ledger_entries 
WHERE event_type LIKE 'orchestrator%' 
ORDER BY created_at DESC 
LIMIT 100;
```

## Performance Considerations

- **Cycle Time:** 2 seconds (configurable)
- **Database Queries:** ~10-15 per cycle (optimized with counts/aggregates)
- **Action Execution:** Async, non-blocking
- **Memory:** Minimal, snapshot is ephemeral
- **Scalability:** Single-instance design (use distributed locks for multi-instance)

## Safety Features

1. **Graceful Degradation:** If a cycle fails, log error and continue
2. **Action Prioritization:** High-priority actions execute first
3. **Retry Limits:** Failed logs have max retry counts
4. **Emergency Mode:** Critical health triggers emergency rebalance
5. **Manual Override:** Can disable autonomous mode anytime

## Monitoring

**Health Dashboard (Future):**
- Real-time system health score
- Active actions chart
- Cycle time metrics
- Success/failure rates
- Ledger error trends

**Logs:**
```
🤖 Orchestrator started - running every 2s
🔄 Cycle 1: 3 actions to execute
✅ Cycle 1: 3 succeeded, 0 failed
⏸️ Cycle 2: No actions needed, system healthy
🔄 Cycle 3: 1 actions to execute
✅ Cycle 3: 1 succeeded, 0 failed
🛑 Orchestrator stopped
```

## Troubleshooting

**Orchestrator not starting:**
- Check `ORCHESTRATOR_ENABLED=true` in config/env
- Verify database connection
- Check for port conflicts

**Too many actions:**
- Review heuristic thresholds in `decider.py`
- Increase `ORCHESTRATOR_INTERVAL_SECONDS`
- Check system health score

**Actions failing:**
- Check executor logs in ledger
- Verify required modules are available
- Review database permissions

**High cycle time:**
- Optimize database queries
- Reduce monitoring scope
- Increase interval

## Future Enhancements

1. **Machine Learning:** Replace heuristics with trained models
2. **Multi-Instance:** Distributed orchestrator with leader election
3. **Predictive Actions:** Forecast issues before they occur
4. **Custom Rules:** User-defined action triggers
5. **Action History:** Track action effectiveness over time
6. **Dashboard UI:** Real-time visualization of orchestrator state
7. **Alerting:** Notify on critical health drops
8. **A/B Testing:** Test different heuristics in production

## Conclusion

The Orchestrator transforms Stakazo from a reactive system into a **proactive, self-healing platform** that continuously optimizes publishing, manages queues, and maintains system health without human intervention.

**Key Benefits:**
- ✅ Autonomous operation
- ✅ Real-time monitoring
- ✅ Intelligent decision-making
- ✅ Automatic error recovery
- ✅ Campaign prioritization
- ✅ Queue optimization
- ✅ Full audit trail (ledger)
- ✅ Manual override capability
