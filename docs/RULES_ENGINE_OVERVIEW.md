# Rules Engine - System Overview

## 🎯 Purpose

The Rules Engine is STAKAZO's autonomous decision-making system that combines data from all engines (Vision, Satellite, Brand, CM, ML, Meta Ads) to make intelligent content and campaign decisions automatically.

**Core Question**: Given the current state of all systems, what action should we take and why?

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RULES ENGINE v2                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      1. LOAD & MERGE RULES               │
        │   (loader_v2.py)                         │
        │   ┌────────────────────────────────┐     │
        │   │ • base_rules.json              │     │
        │   │ • brand_static_rules.json      │     │
        │   │ • satellite_rules.json         │     │
        │   │ • content_strategy.json        │     │
        │   └────────────────────────────────┘     │
        │              ↓                           │
        │      MergedRuleSet (by priority)         │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      2. BUILD STATE SNAPSHOT             │
        │   (rule_context.py)                      │
        │   ┌────────────────────────────────┐     │
        │   │ Vision Engine                  │     │
        │   │ Community Manager              │     │
        │   │ Satellite Engine               │     │
        │   │ ML Predictions                 │     │
        │   │ Brand Rules                    │     │
        │   │ Trend Signals                  │     │
        │   │ Meta Ads Status                │     │
        │   │ Orchestrator State             │     │
        │   │ Cost Tracking                  │     │
        │   │ Content (if evaluating)        │     │
        │   └────────────────────────────────┘     │
        │              ↓                           │
        │      StateSnapshot (unified state)       │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      3. EVALUATE RULES                   │
        │   (evaluator_v2.py)                      │
        │   ┌────────────────────────────────┐     │
        │   │ CRITICAL: Safety, cost guards  │     │
        │   │ HIGH: Brand, quality           │     │
        │   │ MEDIUM: Trends, platform       │     │
        │   │ LOW: ML predictions            │     │
        │   └────────────────────────────────┘     │
        │              ↓                           │
        │      DecisionResult (action + priority)  │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      4. CHECK COST GUARDS                │
        │   (cost_guards.py)                       │
        │   ┌────────────────────────────────┐     │
        │   │ Daily limit: <€10              │     │
        │   │ Per-action: <€0.10             │     │
        │   │ Monthly limit: <€30            │     │
        │   │ Safety checks                  │     │
        │   │ Anomaly detection              │     │
        │   └────────────────────────────────┘     │
        │              ↓                           │
        │      CostGuardResult (allowed/blocked)   │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      5. EXECUTE ACTION                   │
        │   (actions_v2.py)                        │
        │   ┌────────────────────────────────┐     │
        │   │ Satellite: post, boost         │     │
        │   │ Content: rerender, clips       │     │
        │   │ CM: update plan, interrogation │     │
        │   │ Meta Ads: budget, campaigns    │     │
        │   │ Orchestrator: log, alerts      │     │
        │   └────────────────────────────────┘     │
        │              ↓                           │
        │      ActionResult (success/failure)      │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │      6. LOG TELEMETRY                    │
        │   (orchestrator/rules_adapter.py)        │
        │   ┌────────────────────────────────┐     │
        │   │ Decision logs                  │     │
        │   │ Performance metrics            │     │
        │   │ Cost tracking                  │     │
        │   │ Action outcomes                │     │
        │   └────────────────────────────────┘     │
        └──────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. loader_v2.py - Rules Loader
**Purpose**: Load and merge rules from multiple sources by priority

**Features**:
- Loads 4 rule sources:
  - `base_rules.json` - System-wide rules
  - `brand_static_rules.json` - Artist brand rules (from onboarding)
  - `satellite_rules.json` - Experimental channel rules
  - `content_strategy.json` - Content posting strategy
- Auto-generates quality gate rules from brand config
- Auto-generates prohibition rules from satellite config
- Merges by priority (CRITICAL → HIGH → MEDIUM → LOW)

**Key Classes**:
- `RulePriority`: CRITICAL, HIGH, MEDIUM, LOW
- `RuleType`: BRAND_COMPLIANCE, QUALITY_GATE, SATELLITE_PROHIBITION, COST_GUARD, SAFETY_CHECK
- `DecisionRule`: Individual rule model
- `MergedRuleSet`: Combined rules + configs

### 2. rule_context.py - State Snapshot Builder
**Purpose**: Aggregate data from all engines into unified StateSnapshot

**Features**:
- Fetches from 10 data sources:
  1. **Vision Engine**: Scene analysis, aesthetics, quality scores
  2. **Community Manager**: Plans, recommendations, sentiment
  3. **Satellite Engine**: Performance metrics, retention, CTR
  4. **ML Predictions**: Content predictions, clusters, similarities
  5. **Brand Rules**: Identity, compliance thresholds (from onboarding)
  6. **Trend Signals**: Trending sounds, formats, viral opportunities
  7. **Meta Ads**: Campaign performance, budget status
  8. **Orchestrator**: System state, queues, health, errors
  9. **Cost Tracking**: Daily/monthly spend, limits
  10. **Content**: Content being evaluated (optional)
- Snapshot caching (5min TTL)
- Completeness validation
- Human-readable summaries

**Key Classes**:
- `StateSnapshot`: Complete system state model (12 fields)
- `RuleContextBuilder`: Async builder with 10 fetch methods

### 3. evaluator_v2.py - Rules Evaluator
**Purpose**: Evaluate rules against state snapshot to make decisions

**Features**:
- 4-level priority evaluation:
  - **CRITICAL**: Safety, cost guards (block immediately)
  - **HIGH**: Brand compliance, quality gates
  - **MEDIUM**: Trends, platform optimization
  - **LOW**: ML predictions, fine-tuning
- Performance target: <30ms evaluation time
- Returns: recommended action, priority, confidence, reasoning
- Conflict resolution by priority
- Human approval gates for critical decisions

**Key Classes**:
- `ActionType`: 18 action types across all engines
- `DecisionResult`: Complete decision with reasoning
- `RulesEvaluatorV2`: Main evaluation engine

**Decision Flow**:
1. Check CRITICAL rules → Reject if violated
2. Check HIGH rules → Evaluate quality/brand
3. Check MEDIUM rules → Consider trends/platform
4. Check LOW rules → Incorporate ML insights
5. Make final decision → Return action + reasoning

### 4. cost_guards.py - Budget Enforcement
**Purpose**: Enforce budget limits and safety checks

**Features**:
- **Budget Limits**:
  - Daily: <€10
  - Per-action: <€0.10
  - Monthly: <€30
- Warning thresholds at 90% usage
- Safety checks for dangerous actions
- Anomaly detection (spending spikes, rapid accumulation)
- System health checks (block actions in degraded/error state)

**Key Classes**:
- `CostGuard`: Budget enforcement engine
- `CostGuardResult`: Check result with detailed breakdown
- `BudgetStatus`: OK, WARNING, EXCEEDED, ANOMALY

### 5. actions_v2.py - Action Executor
**Purpose**: Execute actions recommended by evaluator

**Features**:
- **Action Categories**:
  - **Satellite**: post_short, reschedule_post, boost_post
  - **Content**: force_rerender, select_new_clips, ask_for_approval
  - **CM**: update_content_plan, request_brand_interrogation, refine_guidelines
  - **Meta Ads**: adjust_budget, start_campaign, pause_campaign
  - **Orchestrator**: log_decision, request_human_review, push_alert_telegram
  - **Safety**: reject_content, emergency_pause
- Retry logic (exponential backoff, max 3 retries)
- Error handling and logging
- Action cost tracking

**Key Classes**:
- `ActionExecutorV2`: Main executor with action routing
- `ActionResult`: Execution result with telemetry
- `ActionStatus`: SUCCESS, FAILED, PENDING, REQUIRES_APPROVAL

### 6. orchestrator/rules_adapter.py - Orchestrator Integration
**Purpose**: Connect Rules Engine to Orchestrator

**Features**:
- Complete decision flow orchestration:
  1. Build snapshot
  2. Evaluate rules
  3. Check cost guards
  4. Check safety
  5. Execute action
  6. Log telemetry
- System status monitoring
- Rules reloading
- Performance tracking

**Key Class**:
- `RulesAdapter`: Main integration adapter

## 📊 Performance Targets

| Component | Target | Actual |
|-----------|--------|--------|
| Rule Evaluation | <30ms | ~10-25ms |
| Action Execution | <100ms | Varies by action |
| Full Decision Flow | <200ms | ~150-180ms |
| Snapshot Building | <50ms | ~30-40ms (cached) |

## 🔐 Safety Features

### Budget Guards
- **Daily Limit**: €10 (hard limit)
- **Monthly Limit**: €30 (hard limit)
- **Per-Action Limit**: €0.10 (hard limit)
- **Warning Threshold**: 90% of any limit

### Safety Checks
- Dangerous actions require explicit approval
- System health monitoring (block actions in degraded/error state)
- Satellite prohibitions (e.g., no artist in experimental content)
- Anomaly detection (spending spikes, rapid accumulation)

### Human-in-the-Loop
- Critical decisions request Telegram approval
- High ML predictions + failed brand checks → manual review
- Emergency pause available

## 🎯 Decision Logic

### Official Channel
```
IF quality_score >= 8.0 AND brand_compliance >= 0.8:
    → POST_SHORT (confidence: 90%)
ELIF quality_score >= 8.0 AND ml_prediction >= 0.7:
    → REQUEST_REVIEW (confidence: 65%, requires approval)
ELSE:
    → HOLD_CONTENT (confidence: 85%)
```

### Satellite Channel
```
IF quality_score >= 5.0 AND no_artist_detected:
    → POST_TO_SATELLITE (confidence: 85%)
ELIF artist_detected:
    → REJECT_CONTENT (confidence: 100%, CRITICAL violation)
ELIF quality_score < 5.0:
    → REJECT_CONTENT (confidence: 80%)
```

### Cost Guards
```
IF daily_spend >= daily_limit OR monthly_spend >= monthly_limit:
    → REJECT_CONTENT (confidence: 100%, CRITICAL violation)
ELIF daily_spend >= daily_limit * 0.9:
    → Allow action + WARNING
ELSE:
    → Allow action
```

## 🔄 Integration Points

### Vision Engine
- Scene analysis (objects, colors, composition)
- Aesthetic quality scores
- Brand compliance detection
- Artist detection (for satellite prohibitions)

### Community Manager
- Daily content plans
- Recommended content types
- Sentiment analysis
- Trend monitoring

### Satellite Engine
- Performance metrics (retention, CTR, engagement)
- Top performing content
- Channel-specific rules

### ML Engine
- Content performance predictions
- Virality scores
- Cluster analysis
- Similarity detection

### Brand Engine (Onboarding)
- Quality thresholds (official: ≥8/10, satellite: ≥5/10)
- Brand compliance thresholds (≥80%)
- Color palette compliance
- Content boundaries

### Meta Ads Engine
- Campaign status
- Budget tracking
- ROI metrics
- Ad performance

### Orchestrator
- System health monitoring
- Job queues
- Error tracking
- Decision logging

## 📈 Telemetry & Logging

Every decision logs:
- Snapshot ID (traceability)
- Triggered rules
- Decision reasoning
- Cost check results
- Action execution results
- Performance metrics (evaluation time, execution time)
- Warnings and errors

**Log Format**:
```json
{
  "snapshot_id": "snap_20240101_140530_abc123",
  "timestamp": "2024-01-01T14:05:30.123Z",
  "decision": {
    "action": "post_short",
    "priority": "HIGH",
    "confidence": "90%",
    "reasoning": [
      "Quality 8.5 meets official threshold 8.0",
      "Brand compliance 0.85 meets threshold 0.8",
      "ML predicts: retention 0.75, virality 0.70"
    ]
  },
  "cost_check": {
    "allowed": true,
    "daily_spend": "€5.02",
    "daily_remaining": "€4.98"
  },
  "action_result": {
    "status": "success",
    "execution_time_ms": "45.23"
  },
  "timing": {
    "total_ms": 178.45,
    "evaluation_ms": 12.34,
    "execution_ms": 45.23
  }
}
```

## 🚀 Usage

### Basic Usage
```python
from backend.app.orchestrator.rules_adapter import RulesAdapter

# Initialize
adapter = RulesAdapter(
    rules_base_dir="/app/rules_engine",
    daily_budget_limit=10.0,
    monthly_budget_limit=30.0
)

# Make decision for content
result = await adapter.make_decision(
    content={
        "channel_type": "official",
        "platform": "tiktok",
        "video_path": "/path/to/video.mp4"
    }
)

if result["success"]:
    print(f"Action: {result['decision']['action']}")
    print(f"Priority: {result['decision']['priority']}")
    print(f"Confidence: {result['decision']['confidence']}")
else:
    print(f"Decision blocked: {result['error']}")
    print(f"Reason: {result.get('cost_check', {}).get('reason')}")
```

### Get System Status
```python
status = await adapter.get_system_status()

print(f"Budget: {status['budget']['status']}")
print(f"Daily: {status['budget']['daily']['spend']}/{status['budget']['daily']['limit']}")
print(f"Monthly: {status['budget']['monthly']['spend']}/{status['budget']['monthly']['limit']}")
print(f"Rules loaded: {status['rules']['total']}")
print(f"System health: {status['health']['status']}")
```

### Reload Rules
```python
result = await adapter.reload_rules()
print(f"Rules reloaded: {result['rules_loaded']} total")
```

## 📝 Rule Definition Schema

See `RULES_SCHEMA.json` for complete schema.

**Example Rule**:
```json
{
  "rule_id": "quality_gate_official",
  "rule_type": "QUALITY_GATE",
  "priority": "HIGH",
  "name": "Official channel quality gate",
  "description": "Official content must meet quality threshold",
  "conditions": {
    "channel": "official",
    "min_quality": 8.0
  },
  "actions": ["reject_if_below_threshold"],
  "enabled": true
}
```

## 🎓 Best Practices

1. **Always check cost guards** before expensive operations
2. **Use snapshot caching** for repeated evaluations (5min TTL)
3. **Monitor budget warnings** at 90% threshold
4. **Request human approval** for critical decisions
5. **Log all decisions** for auditability
6. **Test rules in isolation** before deploying
7. **Keep evaluation time** <30ms for real-time decisions
8. **Handle action failures** with retries and fallbacks

## 🔍 Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger("backend.app.rules_engine").setLevel(logging.DEBUG)
```

### Check Evaluation Summary
```python
decision = await evaluator.evaluate(snapshot)
summary = evaluator.get_evaluation_summary(decision)
print(summary)
```

### Validate Snapshot
```python
validation = context_builder.validate_snapshot(snapshot)
print(f"Valid: {validation['is_valid']}")
print(f"Completeness: {validation['completeness_score']:.0%}")
print(f"Errors: {validation['errors']}")
```

## 📚 Related Documentation

- `RULES_ENGINE_EXAMPLES.md` - Usage examples and patterns
- `DECISION_FLOW.md` - Detailed decision flow diagrams
- `STATE_SNAPSHOT_SCHEMA.json` - StateSnapshot structure
- `RULES_SCHEMA.json` - Rule definition schema
