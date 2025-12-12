# Meta Optimization Loop

**PASO 10.6 Implementation** - Automated optimization system that reads ROAS/pixel outcomes and produces optimization actions (scale up/down, pause, reallocate).

---

## 📊 Overview

The Meta Optimization Loop is an autonomous system that continuously monitors campaign performance using ROAS metrics from the ROAS Engine (PASO 10.5) and generates/executes optimization actions to maximize advertising ROI.

### Key Features

- **Automated Monitoring**: Continuously evaluates active campaigns
- **Smart Actions**: Generates scale-up, scale-down, pause, and budget reallocation actions
- **Two Modes**:
  - **Suggest Mode** (default): Creates actions for manual review
  - **Auto Mode**: Executes safe actions automatically with guard rails
- **Safety First**: Multiple guard rails prevent excessive changes
- **Audit Trail**: All actions logged to event ledger

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│               Meta Optimization Loop                        │
└────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Scheduler   │  (every N hours)
│  (Runner)    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   Optimization Service                    │
│   ┌────────────────────────────────────┐ │
│   │  1. Fetch Active Campaigns         │ │
│   │  2. Get ROAS Metrics (PASO 10.5)   │ │
│   │  3. Evaluate Performance           │ │
│   │  4. Generate Actions               │ │
│   │  5. Apply Guard Rails              │ │
│   │  6. Enqueue/Execute Actions        │ │
│   └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   Action Queue (Database)                 │
│   ┌────────────────────────────────────┐ │
│   │  optimization_actions table        │ │
│   │  - SUGGESTED (awaiting review)     │ │
│   │  - PENDING (approved)              │ │
│   │  - EXECUTING (in progress)         │ │
│   │  - EXECUTED (completed)            │ │
│   │  - FAILED (error)                  │ │
│   └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   Execution Layer                         │
│   ┌────────────────────────────────────┐ │
│   │  • Update Meta Ads API             │ │
│   │  • Adjust budgets                  │ │
│   │  • Pause/Resume ads                │ │
│   │  • Create ledger events            │ │
│   └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   Event Ledger (Audit Trail)             │
│   - optimization_suggested                │
│   - optimization_executed                 │
│   - optimization_failed                   │
└──────────────────────────────────────────┘
```

---

## 🎯 Optimization Actions

### 1. Scale Up

**Trigger**: ROAS ≥ 2.0 (configurable), confidence ≥ 0.65

**Action**: Increase ad budget by 10-100% based on performance:
- ROAS ≥ 5.0: +100%
- ROAS ≥ 4.0: +75%
- ROAS ≥ 3.5: +50%
- ROAS ≥ 3.0: +25%
- ROAS ≥ 2.0: +10%

**Example**:
```json
{
  "action_type": "scale_up",
  "target": "META_AD_123",
  "amount_pct": 0.50,
  "old_budget_usd": 100.0,
  "new_budget_usd": 150.0,
  "reason": "high_roas_performance",
  "roas_value": 4.2,
  "confidence": 0.85
}
```

### 2. Scale Down

**Trigger**: ROAS ≤ 1.5 (configurable)

**Action**: Decrease ad budget by 30%

**Example**:
```json
{
  "action_type": "scale_down",
  "target": "META_AD_456",
  "amount_pct": -0.30,
  "old_budget_usd": 100.0,
  "new_budget_usd": 70.0,
  "reason": "roas_below_threshold",
  "roas_value": 1.2,
  "confidence": 0.75
}
```

### 3. Pause

**Trigger**: ROAS < 0.8 (critically low)

**Action**: Stop ad spending completely

**Example**:
```json
{
  "action_type": "pause",
  "target": "META_AD_789",
  "amount_pct": -1.0,
  "reason": "roas_critically_low",
  "roas_value": 0.5,
  "confidence": 0.80
}
```

### 4. Budget Reallocation

**Trigger**: 
- Campaign has ≥ 3 ads
- ROAS variance > 1.5x (max/min ratio)

**Action**: Redistribute budget proportionally by ROAS × confidence

**Example**:
```json
{
  "action_type": "reallocate",
  "target": "META_CAMPAIGN_ABC",
  "reallocation_plan": {
    "total_budget": 1000.0,
    "allocations": [
      {"ad_id": "AD_1", "old_budget": 333, "new_budget": 500, "roas": 5.0},
      {"ad_id": "AD_2", "old_budget": 333, "new_budget": 350, "roas": 3.0},
      {"ad_id": "AD_3", "old_budget": 334, "new_budget": 150, "roas": 1.5}
    ]
  },
  "affected_ad_ids": ["AD_1", "AD_2", "AD_3"],
  "confidence": 0.70
}
```

---

## 🛡️ Guard Rails (Safety Limits)

The optimizer has multiple layers of protection to prevent excessive changes:

### 1. Confidence Threshold
- Minimum confidence: **0.65** (65%)
- Auto-execution requires: **0.75** (75%)

### 2. Budget Change Limits
- Max daily change: **20%** per action
- Auto-execution max: **10%** (50% of normal limit)
- Exception: Pause actions (always allowed)

### 3. Embargo Period
- New campaigns: **48 hours** before optimization
- Prevents premature optimization with insufficient data

### 4. Cooldown Period
- After optimization: **24 hours** before next action on same ad
- Prevents rapid oscillation

### 5. Minimum Data Requirements
- Min spend: **$100 USD**
- Min impressions: **1,000**
- Ensures statistical validity

### 6. Action Limits
- Max actions per campaign: **5** per run
- Max actions per run: **50** total
- Prevents system overload

### 7. Auto-Execution Restrictions
- Only for high-confidence actions (≥0.75)
- No reallocation (too complex)
- Budget changes ≤ 10%
- Pause always allowed (safety measure)

---

## ⚙️ Configuration

Add to `.env`:

```bash
# Enable/disable optimizer
OPTIMIZER_ENABLED=true

# Mode: "suggest" (manual review) or "auto" (automatic execution)
OPTIMIZER_MODE=suggest

# Run interval (seconds)
OPTIMIZER_INTERVAL_SECONDS=3600  # 1 hour

# ROAS thresholds
OPTIMIZER_SCALE_UP_MIN_ROAS=2.0
OPTIMIZER_SCALE_DOWN_MAX_ROAS=1.5
OPTIMIZER_PAUSE_ROAS=0.8

# Safety limits
OPTIMIZER_MIN_CONFIDENCE=0.65
OPTIMIZER_MAX_DAILY_CHANGE_PCT=0.20  # 20%
OPTIMIZER_EMBARGO_HOURS=48
OPTIMIZER_MIN_SPEND_USD=100.0
OPTIMIZER_MIN_IMPRESSIONS=1000

# Budget reallocation
OPTIMIZER_REALLOCATE_THRESHOLD_DIFF=1.5
OPTIMIZER_REALLOCATE_MIN_ADS=3

# Execution limits
OPTIMIZER_MAX_ACTIONS_PER_CAMPAIGN=5
OPTIMIZER_MAX_ACTIONS_PER_RUN=50
OPTIMIZER_COOLDOWN_HOURS=24
```

---

## 🚀 API Endpoints

### 1. GET /meta/optimization/queue

List pending and suggested actions.

**Auth**: Requires `manager` or `admin` role

**Query Parameters**:
- `campaign_id` (optional): Filter by campaign
- `status` (optional): Filter by status (suggested, pending, etc.)
- `action_type` (optional): Filter by type (scale_up, scale_down, etc.)
- `limit` (optional): Max results (default: 100)

**Response**:
```json
[
  {
    "action_id": "uuid-123",
    "campaign_id": "uuid-campaign",
    "ad_id": "uuid-ad",
    "action_type": "scale_up",
    "target_level": "ad",
    "target_id": "META_AD_456",
    "amount_pct": 0.5,
    "reason": "high_roas_performance",
    "confidence": 0.85,
    "roas_value": 4.2,
    "status": "suggested",
    "created_by": "optimizer",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-17T10:30:00Z"
  }
]
```

### 2. GET /meta/optimization/stats

Get queue statistics.

**Auth**: Requires `manager` or `admin` role

**Response**:
```json
{
  "total_suggested": 15,
  "total_pending": 3,
  "total_executing": 1,
  "total_executed_today": 8,
  "total_failed_today": 0,
  "avg_confidence": 0.78
}
```

### 3. POST /meta/optimization/execute/{action_id}

Execute a specific action.

**Auth**: Requires `manager` or `admin` role

**Request Body**:
```json
{
  "dry_run": false
}
```

**Response**:
```json
{
  "action_id": "uuid-123",
  "status": "executed",
  "details": {
    "message": "Scaled up META_AD_456 by 50.0%",
    "old_budget": 100.0,
    "new_budget": 150.0
  },
  "meta_response": {"success": true}
}
```

### 4. POST /meta/optimization/approve/{action_id}

Approve an action for execution (SUGGESTED → PENDING).

**Auth**: Requires `manager` or `admin` role

**Request Body**:
```json
{
  "notes": "Approved after review"
}
```

**Response**:
```json
{
  "action_id": "uuid-123",
  "status": "pending",
  "approved_by": "user@example.com",
  "approved_at": "2024-01-15T11:00:00Z"
}
```

### 5. DELETE /meta/optimization/cancel/{action_id}

Cancel a pending action.

**Auth**: Requires `manager` or `admin` role

**Response**:
```json
{
  "action_id": "uuid-123",
  "status": "cancelled"
}
```

### 6. POST /meta/optimization/run

Trigger manual optimization run immediately.

**Auth**: Requires `admin` role

**Request Body**:
```json
{
  "campaign_ids": ["META_CAMPAIGN_1", "META_CAMPAIGN_2"],
  "lookback_days": 7
}
```

**Response**:
```json
{
  "started": true,
  "processed_campaigns": 2,
  "actions_suggested": 5,
  "execution_time_seconds": 3.2
}
```

---

## 📊 Database Schema

### optimization_actions Table

```sql
CREATE TABLE optimization_actions (
    id UUID PRIMARY KEY,
    action_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Target
    campaign_id UUID REFERENCES meta_campaigns(id),
    adset_id UUID REFERENCES meta_adsets(id),
    ad_id UUID REFERENCES meta_ads(id),
    
    -- Action details
    action_type VARCHAR(50) NOT NULL,  -- scale_up, scale_down, pause, resume, reallocate
    target_level VARCHAR(20) NOT NULL,  -- campaign, adset, ad
    target_id VARCHAR(100) NOT NULL,
    
    -- Parameters
    amount_pct FLOAT,
    amount_usd FLOAT,
    new_budget_usd FLOAT,
    old_budget_usd FLOAT,
    
    -- Rationale
    reason VARCHAR(255) NOT NULL,
    reason_details TEXT,
    confidence FLOAT NOT NULL,
    
    -- Supporting metrics
    roas_value FLOAT,
    spend_usd FLOAT,
    revenue_usd FLOAT,
    conversions INTEGER,
    impressions INTEGER,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- suggested, pending, executing, executed, failed, cancelled
    created_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    executed_by VARCHAR(100),
    
    -- Timing
    created_at TIMESTAMP NOT NULL,
    approved_at TIMESTAMP,
    executed_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Execution results
    execution_error TEXT,
    execution_result JSON,
    meta_response JSON,
    
    -- Guard rails
    safety_score FLOAT,
    guard_rails_passed INTEGER DEFAULT 1,
    guard_rails_details JSON,
    
    -- Reallocation specific
    reallocation_plan JSON,
    affected_ad_ids JSON,
    
    -- Metadata
    params JSON,
    tags JSON,
    notes TEXT,
    ledger_event_id UUID,
    
    -- Indexes
    INDEX idx_action_id (action_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

---

## 🔄 Workflow

### Suggest Mode (Default)

```
1. Runner executes tick (every N hours)
   ↓
2. Service evaluates active campaigns
   ↓
3. Generate optimization actions based on ROAS
   ↓
4. Apply guard rails
   ↓
5. Enqueue actions (status = SUGGESTED)
   ↓
6. Create ledger event (optimization_suggested)
   ↓
7. [MANUAL] Manager reviews queue via API
   ↓
8. [MANUAL] Manager approves/rejects actions
   ↓
9. [MANUAL] Approved actions executed (status = EXECUTED)
   ↓
10. Create ledger event (optimization_executed)
```

### Auto Mode

```
1. Runner executes tick (every N hours)
   ↓
2. Service evaluates active campaigns
   ↓
3. Generate optimization actions based on ROAS
   ↓
4. Apply guard rails
   ↓
5. Enqueue actions (status = SUGGESTED)
   ↓
6. Check if safe for auto-execution:
   - Confidence ≥ 0.75
   - Budget change ≤ 10%
   - Not a reallocation
   - OR action_type = pause
   ↓
7a. IF SAFE: Execute immediately (status = EXECUTED)
7b. IF NOT SAFE: Keep as SUGGESTED (manual review)
   ↓
8. Create ledger events
```

---

## 🔍 Ledger Events

All optimization actions generate audit trail events:

### optimization_suggested

```json
{
  "event_type": "optimization_suggested",
  "entity_type": "optimization_action",
  "entity_id": "action_uuid",
  "details": {
    "action_type": "scale_up",
    "target": "META_AD_123",
    "amount_pct": 0.5,
    "reason": "high_roas_performance",
    "roas_value": 4.2,
    "confidence": 0.85
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### optimization_executed

```json
{
  "event_type": "optimization_executed",
  "entity_type": "optimization_action",
  "entity_id": "action_uuid",
  "details": {
    "executed_by": "user@example.com",
    "old_budget": 100.0,
    "new_budget": 150.0,
    "meta_response": {"success": true}
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

### optimization_failed

```json
{
  "event_type": "optimization_failed",
  "entity_type": "optimization_action",
  "entity_id": "action_uuid",
  "details": {
    "error": "Meta API error: Invalid budget value",
    "attempted_by": "optimizer_auto"
  },
  "created_at": "2024-01-15T10:35:00Z"
}
```

---

## 🚢 Deployment

### Staged Rollout

#### 1. Staging Environment
```bash
# Suggest mode only
OPTIMIZER_ENABLED=true
OPTIMIZER_MODE=suggest
OPTIMIZER_INTERVAL_SECONDS=7200  # 2 hours

# Conservative thresholds
OPTIMIZER_SCALE_UP_MIN_ROAS=2.5
OPTIMIZER_SCALE_DOWN_MAX_ROAS=1.2
OPTIMIZER_MAX_DAILY_CHANGE_PCT=0.10  # 10%
```

#### 2. Canary (10% of traffic)
```bash
# Suggest mode with tighter loop
OPTIMIZER_ENABLED=true
OPTIMIZER_MODE=suggest
OPTIMIZER_INTERVAL_SECONDS=3600  # 1 hour

# Standard thresholds
OPTIMIZER_SCALE_UP_MIN_ROAS=2.0
OPTIMIZER_SCALE_DOWN_MAX_ROAS=1.5
OPTIMIZER_MAX_DAILY_CHANGE_PCT=0.15  # 15%
```

#### 3. Production (Full Auto)
```bash
# Auto mode with all features
OPTIMIZER_ENABLED=true
OPTIMIZER_MODE=auto
OPTIMIZER_INTERVAL_SECONDS=3600

# Production thresholds
OPTIMIZER_SCALE_UP_MIN_ROAS=2.0
OPTIMIZER_SCALE_DOWN_MAX_ROAS=1.5
OPTIMIZER_MAX_DAILY_CHANGE_PCT=0.20  # 20%
```

---

## 🧪 Testing

Run the test suite:

```bash
cd /workspaces/stakazo/backend
PYTHONPATH=/workspaces/stakazo/backend pytest tests/test_meta_optimization.py -v
```

**Test Coverage**:
1. ✅ Worker creates actions based on ROAS
2. ✅ Scale-down threshold applies correctly
3. ✅ Budget reallocation calculation
4. ✅ Actions enqueued and persisted
5. ✅ Execute action changes status and ledger
6. ✅ Safety limits prevent large changes
7. ✅ Confidence threshold enforced
8. ✅ Embargo period respected
9. ✅ Cooldown prevents duplicate optimizations
10. ✅ Auto mode only executes safe actions

---

## 🔧 Manual Execution

### Python REPL

```python
import asyncio
from app.core.database import async_sessionmaker
from app.meta_optimization.runner import OptimizationRunner
from app.meta_optimization.service import OptimizationService

# Execute one tick manually
async def run_once():
    runner = OptimizationRunner(async_sessionmaker)
    stats = await runner._tick()
    print(f"Processed {stats['campaigns_evaluated']} campaigns")
    print(f"Suggested {stats['actions_suggested']} actions")

asyncio.run(run_once())
```

### curl Examples

```bash
# List queue
curl -X GET "http://localhost:8000/meta/optimization/queue" \
  -H "Authorization: Bearer $TOKEN"

# Get stats
curl -X GET "http://localhost:8000/meta/optimization/stats" \
  -H "Authorization: Bearer $TOKEN"

# Trigger manual run
curl -X POST "http://localhost:8000/meta/optimization/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 7}'

# Approve action
curl -X POST "http://localhost:8000/meta/optimization/approve/action_uuid" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Looks good"}'

# Execute action
curl -X POST "http://localhost:8000/meta/optimization/execute/action_uuid" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# Cancel action
curl -X DELETE "http://localhost:8000/meta/optimization/cancel/action_uuid" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔐 RBAC (Role-Based Access Control)

| Endpoint | Manager | Admin | Notes |
|----------|---------|-------|-------|
| GET /queue | ✅ | ✅ | View actions |
| GET /stats | ✅ | ✅ | View statistics |
| POST /approve/{id} | ✅ | ✅ | Approve for execution |
| POST /execute/{id} | ✅ | ✅ | Execute action |
| DELETE /cancel/{id} | ✅ | ✅ | Cancel action |
| POST /run | ❌ | ✅ | Trigger manual run (admin only) |

---

## 📈 Monitoring

### Key Metrics to Track

1. **Action Generation Rate**
   - Actions suggested per hour
   - Actions executed per day
   - Action failure rate

2. **Performance Impact**
   - Average ROAS before/after optimization
   - Budget utilization improvement
   - Revenue lift from optimizations

3. **Safety Metrics**
   - Actions blocked by guard rails
   - Average confidence score
   - Cooldown violations prevented

4. **System Health**
   - Tick execution time
   - API response times
   - Database queue size

### Example Dashboard Queries

```sql
-- Actions by type (last 24h)
SELECT action_type, COUNT(*) as count
FROM optimization_actions
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY action_type;

-- Success rate
SELECT 
  status,
  COUNT(*) as count,
  AVG(confidence) as avg_confidence
FROM optimization_actions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY status;

-- Top performing campaigns (by actions executed)
SELECT 
  campaign_id,
  COUNT(*) as action_count,
  AVG(roas_value) as avg_roas
FROM optimization_actions
WHERE status = 'executed'
  AND executed_at >= NOW() - INTERVAL '30 days'
GROUP BY campaign_id
ORDER BY action_count DESC
LIMIT 10;
```

---

## ⚠️ Edge Cases & Limitations

### 1. Zero ROAS Data
- **Issue**: Campaign has no ROAS metrics yet
- **Handling**: Skip optimization (embargo period handles this)

### 2. Extreme ROAS Values
- **Issue**: ROAS > 50 or < 0 (outliers)
- **Handling**: Flagged by ROAS Engine, confidence reduced

### 3. API Rate Limits
- **Issue**: Meta Ads API rate limits
- **Handling**: Retry with exponential backoff, respect limits

### 4. Concurrent Modifications
- **Issue**: Multiple systems modifying same campaign
- **Handling**: Database transactions, check current state before execution

### 5. Budget Exhaustion
- **Issue**: Campaign budget fully spent
- **Handling**: Skip scale-up actions, suggest reallocation

---

## 🔗 Integration Points

### PASO 10.5 (ROAS Engine)
- Reads: `MetaROASMetricsModel` for ROAS data
- Uses: `ROASOptimizer` for recommendations
- Depends on: ROAS calculations, confidence scores

### PASO 10.3 (Orchestrator)
- Will consume: Optimization recommendations
- Future: Auto-apply approved actions

### Meta Ads API
- Executes: Budget changes via API
- Monitors: Rate limits, errors

---

## ✅ Completion Status

- ✅ Module structure (config, service, runner, routes)
- ✅ Database model (OptimizationActionModel)
- ✅ Guard rails implementation (6 safety layers)
- ✅ API endpoints (6 endpoints with RBAC)
- ✅ Tests (12+ test cases)
- ✅ Documentation (this file)
- ✅ Integration with ROAS Engine

**PASO 10.6: COMPLETE** ✅

---

## 📞 Support

For questions or issues:
- **Team**: Meta Ads Engineering
- **Slack**: #meta-ads-optimization
- **Docs**: https://docs.internal.com/optimization-loop
- **Code**: `/backend/app/meta_optimization/`
