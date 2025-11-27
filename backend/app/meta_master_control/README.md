# Meta Ads Master Control Tower (PASO 10.18)

**Version:** 1.0.0  
**Mode:** STUB (100% functional, ready for LIVE)  
**Purpose:** Centralized orchestration and supervision of ALL Meta Ads modules (10.1-10.17)

---

## 🎯 Overview

The **Meta Ads Master Control Tower** is the unified control and supervision layer for the entire Meta Ads stack. It provides real-time health monitoring, master orchestration commands, emergency procedures, and auto-recovery capabilities across all 17 Meta modules.

### Key Features

✅ **Real-Time Health Monitoring**: Continuous monitoring of all 17 Meta modules  
✅ **Master Orchestration Commands**: High-level control (start/stop/restart/optimize)  
✅ **Emergency Procedures**: Immediate stop and controlled resume  
✅ **Auto-Recovery**: Automatic detection and resolution of common issues  
✅ **System-Wide Reporting**: Comprehensive metrics and recommendations  
✅ **Unified Dashboard**: Centralized view of entire Meta Ads operation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                META MASTER CONTROL TOWER (10.18)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐      ┌───────────────────────────┐   │
│  │  HEALTH MONITOR      │─────▶│  ORCHESTRATION COMMANDER  │   │
│  │  • Check 17 modules  │      │  • Execute commands       │   │
│  │  • Every 1 hour      │      │  • Coordinate operations  │   │
│  │  • Detect anomalies  │      │  • Bulk actions           │   │
│  └──────────────────────┘      └───────────────────────────┘   │
│           │                              │                       │
│           ▼                              ▼                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               AUTO-RECOVERY ENGINE                        │  │
│  │  • Detect issues → Execute recovery → Monitor result     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         │               │                │               │
         ▼               ▼                ▼               ▼
    [10.1-10.5]    [10.6-10.9]     [10.10-10.13]   [10.15-10.17]
```

---

## 📦 Module Integration

The Control Tower monitors and orchestrates **17 Meta Ads modules**:

| Module | Name | Function |
|--------|------|----------|
| 10.1 | Meta Models | Base data layer |
| 10.2 | Meta Ads Client | API communication |
| 10.3 | Meta Orchestrator | Campaign orchestration |
| 10.5 | ROAS Engine | Return on ad spend optimization |
| 10.6 | Optimization Loop | Continuous optimization |
| 10.7 | Autonomous System | Semi-autonomous control |
| 10.8 | Auto-Publisher | Automated publishing |
| 10.9 | Budget Spike Manager | Anomaly detection |
| 10.10 | Creative Variants | Variant generation |
| 10.11 | Full Cycle Manager | End-to-end automation |
| 10.12 | Targeting Optimizer | Audience optimization |
| 10.13 | Creative Intelligence | AI-powered insights |
| 10.15 | Creative Analyzer | Performance analysis |
| 10.16 | Creative Optimizer | Winner selection |
| 10.17 | Creative Production | Autonomous production |

---

## 🔍 Health Monitoring

### System Status Levels

- **HEALTHY**: All modules online and performing well
- **DEGRADED**: Some modules experiencing issues (≤2 degraded, 0 offline)
- **CRITICAL**: Major problems detected (>2 degraded or 1-3 offline)
- **EMERGENCY_STOP**: System halted by administrator

### Module Health Tracking

Each module is monitored for:

- **Status**: ONLINE, DEGRADED, OFFLINE, UNKNOWN
- **Success Rate**: Percentage of successful executions (24h)
- **Execution Time**: Average execution time (ms)
- **Error Count**: Total errors in last 24h
- **API Calls**: Total API calls in last 24h
- **Scheduler Health**: Is scheduler running?
- **Database Health**: Are DB connections healthy?
- **API Health**: Is Meta API responding?
- **Resource Usage**: DB connections, memory, CPU

### Monitoring Frequency

- **Scheduler Cycle**: Every **1 hour** (faster than other modules' 12h/24h)
- **On-Demand**: Via API endpoint `/meta/control-tower/health`

---

## 🎮 Master Orchestration Commands

### Available Commands

```python
class CommandType(str, Enum):
    START_ALL = "start_all"           # Start all schedulers
    STOP_ALL = "stop_all"             # Stop all schedulers
    RESTART_MODULE = "restart_module" # Restart specific module
    EMERGENCY_STOP = "emergency_stop" # Immediate halt
    RESUME_OPERATIONS = "resume"      # Resume after stop
    SYNC_ALL_DATA = "sync_data"       # Force data sync
    OPTIMIZE_ALL = "optimize"         # Run optimization
    RUN_HEALTH_CHECK = "health_check" # Force health check
```

### Command Examples

**Start All Schedulers:**
```bash
curl -X POST "http://localhost:8000/meta/control-tower/command" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "start_all",
    "reason": "Starting Meta Ads stack",
    "execute_immediately": true
  }'
```

**Stop All Schedulers:**
```bash
curl -X POST "http://localhost:8000/meta/control-tower/command" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "stop_all",
    "reason": "Maintenance window",
    "execute_immediately": true
  }'
```

**Restart Specific Module:**
```bash
curl -X POST "http://localhost:8000/meta/control-tower/command" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "restart_module",
    "target_modules": ["10.7"],
    "reason": "Restart Autonomous System",
    "execute_immediately": true
  }'
```

---

## 🚨 Emergency Procedures

### Emergency Stop

Immediately halt all Meta Ads operations:

```bash
curl -X POST "http://localhost:8000/meta/control-tower/emergency-stop" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Budget anomaly detected",
    "stop_schedulers": true,
    "pause_campaigns": true,
    "send_alerts": true
  }'
```

**Actions Taken:**
- ✅ Stop all schedulers
- ✅ Pause active campaigns
- ✅ Send emergency alerts to admins
- ✅ Set system status to EMERGENCY_STOP

### Resume Operations

Resume after emergency stop:

```bash
curl -X POST "http://localhost:8000/meta/control-tower/resume" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_schedulers": true,
    "resume_campaigns": true,
    "run_health_check": true
  }'
```

**Actions Taken:**
- ✅ Resume all schedulers
- ✅ Resume paused campaigns
- ✅ Run comprehensive health check
- ✅ Set system status back to HEALTHY/DEGRADED

---

## 🔧 Auto-Recovery Procedures

### Recovery Actions

```python
class RecoveryAction(str, Enum):
    RESTART_SCHEDULER = "restart_scheduler"  # Restart stuck scheduler
    CLEAR_CACHE = "clear_cache"              # Clear stale caches
    RECONNECT_DB = "reconnect_db"            # Reconnect to database
    RESET_MODULE = "reset_module"            # Reset module state
    ALERT_ADMIN = "alert_admin"              # Escalate to human
```

### Auto-Recovery Logic

The Control Tower automatically executes recovery when:

1. **Module OFFLINE** → `RESTART_SCHEDULER` (confidence 90%)
2. **High Error Rate** (>50 errors/24h) → `RESET_MODULE` (confidence 75%)
3. **Scheduler Not Running** → `RESTART_SCHEDULER` (confidence 95%)
4. **DB Unhealthy** → `RECONNECT_DB` (confidence 85%)

**Auto-Execute Threshold:** Confidence ≥ 85%

---

## 🗄️ Database Schema

### Tables

#### 1. `meta_control_tower_runs`

Tracks each health check or command execution.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| run_type | String | health_check, command, emergency_stop, resume |
| command_type | String | Type of command executed (if applicable) |
| system_status | String | System status at execution time |
| total_modules_checked | Integer | Total modules checked |
| online_modules | Integer | Count of ONLINE modules |
| degraded_modules | Integer | Count of DEGRADED modules |
| offline_modules | Integer | Count of OFFLINE modules |
| module_health_details | JSONB | Dict of module_name → status |
| actions_executed | JSONB | List of actions taken |
| errors_encountered | JSONB | List of errors (if any) |
| recoveries_performed | JSONB | List of recovery procedures executed |
| total_api_calls_24h | Integer | System-wide API calls (24h) |
| total_errors_24h | Integer | System-wide errors (24h) |
| total_campaigns_active | Integer | Total active campaigns |
| total_daily_budget_usd | Float | Total daily budget (USD) |
| db_connection_pool_size | Integer | DB pool size |
| db_active_connections | Integer | Active DB connections |
| db_query_avg_ms | Float | Average query time (ms) |
| execution_time_ms | Integer | Execution time (ms) |
| executed_by | String | Who executed (scheduler, user ID, api) |
| executed_at | DateTime | Execution timestamp |
| recommendations | JSONB | List of recommendations |
| alerts | JSONB | List of alerts |
| mode | String | stub or live |

#### 2. `meta_system_health_logs`

Per-module health logs (17 modules × N checks).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| module_name | String | Module ID (10.1-10.17) |
| module_full_name | String | Full module name |
| health_status | String | ONLINE, DEGRADED, OFFLINE, UNKNOWN |
| success_rate | Float | Success rate (0.0-1.0) |
| avg_execution_time_ms | Integer | Average execution time |
| error_count_24h | Integer | Errors in last 24h |
| api_calls_24h | Integer | API calls in last 24h |
| is_scheduler_running | Boolean | Scheduler status |
| is_db_healthy | Boolean | Database health |
| is_api_healthy | Boolean | API health |
| last_run | DateTime | Last execution |
| next_run | DateTime | Next scheduled execution |
| last_error | String | Last error message |
| last_error_time | DateTime | Last error timestamp |
| recovery_attempts | Integer | Number of recovery attempts |
| last_recovery_action | String | Last recovery action taken |
| recovery_successful | Boolean | Was recovery successful? |
| db_connections | Integer | Active DB connections |
| memory_usage_mb | Float | Memory usage (MB) |
| cpu_usage_pct | Float | CPU usage (%) |
| checked_at | DateTime | Check timestamp |
| mode | String | stub or live |

### Indices

- `ix_control_runs_status_executed`: (system_status, executed_at)
- `ix_control_runs_type_status`: (run_type, system_status)
- `ix_control_runs_command_executed`: (command_type, executed_at)
- `ix_health_logs_module_status`: (module_name, health_status)
- `ix_health_logs_module_checked`: (module_name, checked_at)
- `ix_health_logs_scheduler_db`: (is_scheduler_running, is_db_healthy)
- `ix_health_logs_errors`: (error_count_24h, checked_at)

---

## 🌐 API Endpoints

### 1. Get Control Tower Status

**GET** `/meta/control-tower/status`

```json
{
  "is_operational": true,
  "emergency_stop_active": false,
  "last_health_check": "2025-01-15T10:30:00Z",
  "system_status": "healthy",
  "total_modules_monitored": 17,
  "online_modules": 15,
  "degraded_modules": 2,
  "offline_modules": 0,
  "mode": "stub"
}
```

### 2. Get System Health

**GET** `/meta/control-tower/health`

Returns comprehensive health report with all 17 modules.

### 3. Execute Command

**POST** `/meta/control-tower/command`

Execute master orchestration command.

### 4. Emergency Stop

**POST** `/meta/control-tower/emergency-stop`

Immediate system halt.

### 5. Resume Operations

**POST** `/meta/control-tower/resume`

Resume after emergency stop.

### 6. Get System Report

**GET** `/meta/control-tower/report`

Comprehensive historical report.

---

## 📊 Scheduler Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   SCHEDULER (1h cycle)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Run health check on all 17 modules                      │
│     └─→ Check scheduler, DB, API health                     │
│     └─→ Collect metrics (success rate, errors, etc.)        │
│                                                               │
│  2. Detect degraded/offline modules                          │
│     └─→ Compare against thresholds                          │
│     └─→ Identify anomalies                                  │
│                                                               │
│  3. Generate recovery procedures                             │
│     └─→ Recommend actions (restart, reconnect, reset)       │
│     └─→ Assign confidence scores                            │
│                                                               │
│  4. Execute auto-recovery (confidence ≥ 85%)                 │
│     └─→ Restart schedulers                                  │
│     └─→ Reconnect databases                                 │
│     └─→ Clear caches                                        │
│                                                               │
│  5. Persist to database                                      │
│     └─→ Save run to meta_control_tower_runs                 │
│     └─→ Save logs to meta_system_health_logs (17 entries)   │
│                                                               │
│  6. Generate alerts (if critical)                            │
│     └─→ Log errors                                          │
│     └─→ Send notifications                                  │
│                                                               │
│  ⏰ Wait 1 hour → Repeat                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 STUB vs LIVE Mode

### STUB Mode (Current)

- ✅ 100% functional simulation
- ✅ Generates synthetic health data
- ✅ Simulates all commands
- ✅ Persists to database
- ✅ Ready for testing

### LIVE Mode (Future)

To activate LIVE mode:

1. **Implement real health checks:**
   - Query actual scheduler status
   - Check real DB connections
   - Validate Meta API responses

2. **Implement real commands:**
   - Start/stop actual schedulers
   - Pause/resume real campaigns
   - Execute real recovery procedures

3. **Update mode parameter:**
   ```python
   control_tower = MetaMasterControlTower(mode="live")
   ```

---

## 🧪 Testing

Run all tests:

```bash
pytest app/tests/test_meta_master_control.py -v
```

Expected tests (12+):
- ✅ test_health_monitoring_all_17_modules
- ✅ test_module_health_status_detection
- ✅ test_system_health_report_aggregation
- ✅ test_orchestration_command_start_all
- ✅ test_orchestration_command_stop_all
- ✅ test_emergency_stop_procedures
- ✅ test_resume_operations
- ✅ test_auto_recovery_procedures
- ✅ test_scheduler_1h_cycle
- ✅ test_integration_with_modules
- ✅ test_db_persistence_2_tables
- ✅ test_api_endpoints

---

## 📝 Integration with main.py

Register in `backend/app/main.py`:

```python
from app.meta_master_control.scheduler import master_control_background_task
from app.meta_master_control.router import router as master_control_router

# Register router
app.include_router(master_control_router)

# Register scheduler in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(master_control_background_task())
    yield
    task.cancel()
```

---

## 🎯 Use Cases

### 1. Daily Operations Dashboard

Monitor entire Meta Ads stack from single endpoint:

```bash
curl http://localhost:8000/meta/control-tower/health
```

### 2. Automated Maintenance

Schedule maintenance with graceful shutdown:

```bash
# Stop all
curl -X POST .../command -d '{"command_type": "stop_all"}'

# Perform maintenance
# ...

# Resume all
curl -X POST .../command -d '{"command_type": "start_all"}'
```

### 3. Budget Anomaly Response

Emergency stop when budget spikes detected:

```bash
curl -X POST .../emergency-stop -d '{
  "reason": "Budget spike: $10k in 1h",
  "pause_campaigns": true
}'
```

### 4. Auto-Recovery

Control Tower automatically restarts failed modules without human intervention.

### 5. Performance Optimization

Run system-wide optimization:

```bash
curl -X POST .../command -d '{"command_type": "optimize_all"}'
```

---

## 📈 Success Metrics

- **System Uptime**: % of time system is HEALTHY
- **Auto-Recovery Success Rate**: % of issues resolved automatically
- **Mean Time to Recovery (MTTR)**: Average time to fix issues
- **Module Availability**: % of modules ONLINE
- **Emergency Stop Frequency**: Count per week
- **False Positive Rate**: % of unnecessary alerts

---

## 🚀 Roadmap

### Phase 1: Current (STUB)
- ✅ Health monitoring simulation
- ✅ Command execution simulation
- ✅ Auto-recovery logic
- ✅ Database persistence
- ✅ API endpoints

### Phase 2: LIVE Mode
- ⏳ Real scheduler status checks
- ⏳ Actual command execution
- ⏳ Real-time metric collection
- ⏳ Integration with monitoring tools
- ⏳ Alert notifications (email, Slack)

### Phase 3: Advanced Features
- ⏳ Predictive failure detection (ML)
- ⏳ Automated optimization suggestions
- ⏳ Custom recovery procedures
- ⏳ Multi-region orchestration
- ⏳ Real-time dashboard (WebSockets)

---

## 📚 Related Modules

- **PASO 10.1-10.17**: All Meta Ads modules (monitored by this tower)
- **PASO 11.x**: TikTok Ads modules (future unified control tower)
- **PASO 12.x**: LinkedIn Ads modules (future unified control tower)

---

## 🤝 Contributing

When adding new Meta Ads modules:

1. Add module to `META_MODULES` list in `control_tower.py`
2. Implement health check logic in `_check_module_health()`
3. Update total module count in tests
4. Document integration in this README

---

## ⚠️ Important Notes

- **Admin Access Required**: All control tower endpoints require admin role
- **Emergency Stop Impact**: Immediately halts ALL Meta Ads operations
- **Auto-Recovery**: Only executes for confidence ≥ 85%
- **Scheduler Frequency**: 1h cycle (faster than other modules)
- **Database Load**: Writes 1 run + 17 logs every hour

---

**Last Updated:** 2025-01-15  
**Maintainer:** Stakazo DevOps Team  
**Status:** ✅ STUB Mode Fully Operational
