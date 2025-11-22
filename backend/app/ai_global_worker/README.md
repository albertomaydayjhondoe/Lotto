# AI Global Worker

**Autonomous AI system analyzer and recommendation engine.**

## Overview

The AI Global Worker is an autonomous background service that:
- **Collects** comprehensive system state from all modules
- **Analyzes** metrics using LLM-powered reasoning
- **Generates** intelligent summaries and health assessments
- **Recommends** prioritized actions based on current conditions
- **Proposes** executable action plans
- **Runs continuously** in the background at configurable intervals

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI GLOBAL WORKER                         │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  COLLECTOR   │───▶│  REASONING   │───▶│   RUNNER     │  │
│  │              │    │   ENGINE     │    │ (Background) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                               │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │   DATABASE   │    │  LLM CLIENT  │                       │
│  │ (All Modules)│    │   (Stub)     │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
                   ┌──────────┐
                   │   API    │
                   │ ROUTER   │
                   └──────────┘
                         │
                    ┌────┴────┐
                    │  6 REST │
                    │ Endpoints│
                    └─────────┘
```

---

## Components

### 1. Collector (`collector.py`)

Collects comprehensive system snapshot:

```python
async def collect_system_snapshot(db) -> SystemSnapshot
```

**Data Sources:**
- Queue statistics (pending, processing, failed, success)
- Scheduler status (pending, due soon)
- Orchestrator metrics (running, last run, actions)
- Publishing history (success rate, totals, failures)
- Content metrics (clips, jobs, campaigns)
- Alert metrics (critical, warning)
- Platform-specific stats
- Best clips per platform
- Rule engine weights
- Recent ledger events (last 50)
- Worker load
- Telemetry data

### 2. LLM Client (`llm_client.py`)

**Current Implementation:** Stub/Mock responses

Generates:
- **System Summary**: Health assessment with score (0-100)
- **Recommendations**: Prioritized list of actionable items
- **Action Plan**: Ordered steps to improve system health

```python
class LLMClient:
    async def generate_summary(snapshot) -> AISummary
    async def generate_recommendations(snapshot) -> List[AIRecommendation]
    async def generate_action_plan(snapshot) -> AIActionPlan
```

**TODO (PASO 7.2): OpenAI Integration**

Replace stub implementation with actual LLM calls:

```python
# TODO: Initialize OpenAI client
from openai import AsyncOpenAI

self.client = AsyncOpenAI(api_key=api_key)

# TODO: Implement actual LLM call
async def generate_summary(self, snapshot):
    prompt = self._build_summary_prompt(snapshot)
    
    response = await self.client.chat.completions.create(
        model="gpt-4-turbo",  # or "gpt-4o" or "gpt-5"
        messages=[
            {
                "role": "system",
                "content": """You are an expert system analyst for a social 
                              media content automation platform. Analyze the 
                              provided metrics and generate a comprehensive 
                              health summary."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    return self._parse_summary_response(response)
```

**Prompt Engineering Tips (for PASO 7.2):**
- Include all snapshot metrics in structured format (JSON)
- Request specific output format matching Pydantic schemas
- Use system role to define AI personality and expertise
- Include examples of good vs bad recommendations
- Set temperature based on creativity needs (0.3-0.7 recommended)

### 3. Reasoning Engine (`reasoning.py`)

Orchestrates LLM client to generate complete output:

```python
async def run_full_reasoning(snapshot) -> AIReasoningOutput
```

Returns:
- Summary
- Recommendations
- Action plan
- Execution time
- Unique reasoning ID
- Timestamp

### 4. Runner (`runner.py`)

Autonomous background loop:

```python
async def ai_worker_loop(db_factory, interval_seconds=30)
```

**Behavior:**
- Runs continuously in background
- Executes every `AI_WORKER_INTERVAL_SECONDS` (default: 30s)
- Stores last reasoning in global state
- Handles errors gracefully (logs and continues)
- Can be started/stopped via `start_ai_worker_loop()` / `stop_ai_worker_loop()`

**Configuration:**
```python
# app/core/config.py
AI_WORKER_ENABLED = True          # Enable/disable worker
AI_WORKER_INTERVAL_SECONDS = 30   # Cycle interval
```

### 5. API Router (`router.py`)

**6 REST Endpoints:**

#### `GET /ai/global/last_run`
Returns most recent AI reasoning output from background worker.

**Response:** `AIReasoningOutput`

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/last_run
```

```json
{
  "reasoning_id": "uuid",
  "timestamp": "2025-11-22T10:30:00Z",
  "snapshot": { ... },
  "summary": {
    "overall_health": "good",
    "health_score": 82.5,
    "key_insights": [
      "System processing 45 publications in last 24h",
      "Queue is healthy with 12 pending items"
    ],
    "concerns": [
      "Low clip inventory: only 8 clips ready"
    ],
    "positives": [
      "Excellent publish success rate: 94.2%",
      "3 active campaigns running"
    ]
  },
  "recommendations": [...],
  "action_plan": {...}
}
```

#### `POST /ai/global/run`
Manually trigger immediate AI reasoning cycle.

**Response:** `AIRunResponse`

**Example:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/run
```

```json
{
  "success": true,
  "reasoning_id": "uuid",
  "message": "AI reasoning completed successfully. Health: good",
  "execution_time_ms": 245
}
```

#### `GET /ai/global/snapshot`
Get current system snapshot without AI reasoning.

**Response:** `SystemSnapshot`

#### `GET /ai/global/recommendations`
Get only recommendations from last reasoning.

**Response:** `List[AIRecommendation]`

**Example Response:**
```json
[
  {
    "id": "uuid",
    "priority": "high",
    "category": "content",
    "title": "Increase Clip Production",
    "description": "Only 8 clips ready. Upload more videos or process existing ones.",
    "impact": "Maintain consistent publishing schedule",
    "effort": "low",
    "action_type": "process_pending_jobs",
    "action_payload": {}
  }
]
```

#### `GET /ai/global/summary`
Get only system summary from last reasoning.

**Response:** `AISummary`

#### `GET /ai/global/action-plan`
Get only action plan from last reasoning.

**Response:** `AIActionPlan`

**Example Response:**
```json
{
  "plan_id": "uuid",
  "title": "System Optimization Plan",
  "objective": "Improve system health and performance",
  "steps": [
    {
      "step": 1,
      "action": "process_queue",
      "description": "Process pending queue items",
      "automated": true,
      "estimated_duration": "30 minutes"
    },
    {
      "step": 2,
      "action": "retry_failed_jobs",
      "description": "Retry failed jobs with exponential backoff",
      "automated": true,
      "estimated_duration": "15 minutes"
    }
  ],
  "estimated_duration": "45 minutes",
  "risk_level": "low",
  "automated": true
}
```

---

## Data Models

### SystemSnapshot
Complete system state at a point in time:
- `timestamp`: When snapshot was taken
- `queue_pending`, `queue_processing`, `queue_failed`, `queue_success`: Queue metrics
- `scheduler_pending`, `scheduler_due_soon`: Scheduler status
- `orchestrator_running`, `orchestrator_last_run`, `orchestrator_actions_last_24h`: Orchestrator metrics
- `publish_success_rate`, `publish_total_24h`, `publish_failed_24h`: Publishing metrics
- `clips_ready`, `clips_pending_analysis`: Content metrics
- `jobs_pending`, `jobs_failed`: Job metrics
- `campaigns_active`, `campaigns_draft`: Campaign metrics
- `alerts_critical`, `alerts_warning`: Alert counts
- `platform_stats`: Per-platform metrics
- `best_clips`: Best clip per platform
- `rule_weights`: Current rule engine weights
- `recent_events`: Last 50 ledger events
- `additional_metrics`: Extra context

### AISummary
AI-generated system health summary:
- `overall_health`: "excellent" | "good" | "warning" | "critical"
- `health_score`: 0-100
- `key_insights`: 3-5 key insights
- `concerns`: Issues requiring attention
- `positives`: Things going well
- `generated_at`: Timestamp

### AIRecommendation
Single recommendation:
- `id`: Unique ID
- `priority`: "critical" | "high" | "medium" | "low"
- `category`: "performance" | "content" | "campaigns" | "system"
- `title`: Short title
- `description`: Detailed explanation
- `impact`: Expected impact if implemented
- `effort`: "low" | "medium" | "high"
- `action_type`: Action type if executable (optional)
- `action_payload`: Parameters for action (optional)

### AIActionPlan
Proposed action plan:
- `plan_id`: Unique ID
- `title`: Plan title
- `objective`: What this aims to achieve
- `steps`: Ordered list of steps
- `estimated_duration`: Time to complete
- `risk_level`: "low" | "medium" | "high"
- `automated`: Can this be automated?

### AIReasoningOutput
Complete reasoning output:
- `reasoning_id`: Unique ID
- `timestamp`: When generated
- `snapshot`: System snapshot used
- `summary`: AI summary
- `recommendations`: List of recommendations
- `action_plan`: Proposed plan
- `execution_time_ms`: Generation time

---

## RBAC Protection

All endpoints protected with admin/manager roles:
```python
_auth: dict = Depends(require_role("admin", "manager"))
```

Only administrators and managers can access AI insights.

---

## Usage

### Start Worker Automatically

Worker starts automatically on app startup if `AI_WORKER_ENABLED=True`:

```python
# In app/main.py lifespan
if settings.AI_WORKER_ENABLED:
    ai_worker_task = await start_ai_worker_loop(
        db_factory=get_db,
        interval_seconds=settings.AI_WORKER_INTERVAL_SECONDS
    )
```

### Query Last Reasoning

```bash
# Get complete reasoning
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/last_run

# Get only recommendations
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/recommendations

# Get only summary
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/summary
```

### Trigger Manual Reasoning

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/run
```

### Get Raw Snapshot

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/snapshot
```

---

## Frontend Integration

### API Client (`dashboard/lib/ai_global/api.ts`)

```typescript
export const aiGlobalApi = {
  getLastRun: async (token: string) => {
    const response = await fetch('/ai/global/last_run', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  triggerRun: async (token: string) => {
    const response = await fetch('/ai/global/run', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },
  
  // ... other methods
};
```

### React Hook (`dashboard/lib/ai_global/hooks.ts`)

```typescript
export const useAIGlobal = () => {
  const [reasoning, setReasoning] = useState<AIReasoningOutput | null>(null);
  const [loading, setLoading] = useState(false);
  
  const fetchLastRun = async () => {
    setLoading(true);
    try {
      const data = await aiGlobalApi.getLastRun(token);
      setReasoning(data);
    } finally {
      setLoading(false);
    }
  };
  
  return { reasoning, loading, fetchLastRun, triggerRun: ... };
};
```

---

## Extending the System

### Adding New Data Sources

1. Edit `collector.py`:
```python
# In collect_system_snapshot()
try:
    # Add your new metric collection
    new_metric = await db.execute(...)
    snapshot_data["additional_metrics"]["my_metric"] = new_metric
except Exception as e:
    snapshot_data["additional_metrics"]["metric_error"] = str(e)
```

2. Update `SystemSnapshot` schema if needed

### Adding New Recommendation Types

1. Edit `llm_client.py`:
```python
# In generate_recommendations()
if my_custom_condition:
    recommendations.append(AIRecommendation(
        id=str(uuid.uuid4()),
        priority="high",
        category="my_category",
        title="My Custom Recommendation",
        description="...",
        impact="...",
        effort="medium",
        action_type="my_action",
        action_payload={"param": "value"}
    ))
```

### Customizing Health Scoring

Edit `_calculate_stub_health_score()` in `llm_client.py`:

```python
def _calculate_stub_health_score(self, snapshot: SystemSnapshot) -> float:
    score = 100.0
    
    # Add your custom scoring logic
    if my_condition:
        score -= 20
    
    return max(0.0, min(100.0, score))
```

---

## Future Enhancements (PASO 7.2)

### OpenAI GPT-4.1 / GPT-5 Integration

**Setup:**
```bash
pip install openai
```

**Implementation Steps:**

1. **Initialize Client:**
```python
from openai import AsyncOpenAI

class LLMClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo"  # or "gpt-4o" or "gpt-5"
```

2. **Build Prompts:**
```python
def _build_summary_prompt(self, snapshot: SystemSnapshot) -> str:
    return f"""
    Analyze this social media automation system:
    
    METRICS:
    - Queue: {snapshot.queue_pending} pending, {snapshot.queue_failed} failed
    - Success Rate: {snapshot.publish_success_rate:.1%}
    - Clips Ready: {snapshot.clips_ready}
    - Campaigns Active: {snapshot.campaigns_active}
    - Alerts: {snapshot.alerts_critical} critical, {snapshot.alerts_warning} warning
    
    Generate a JSON response with:
    - overall_health (excellent|good|warning|critical)
    - health_score (0-100)
    - key_insights (array of 3-5 strings)
    - concerns (array of strings)
    - positives (array of strings)
    """
```

3. **Call LLM:**
```python
async def generate_summary(self, snapshot: SystemSnapshot) -> AISummary:
    prompt = self._build_summary_prompt(snapshot)
    
    response = await self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": "You are a system analyst..."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1000
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    
    return AISummary(
        overall_health=data["overall_health"],
        health_score=data["health_score"],
        key_insights=data["key_insights"],
        concerns=data["concerns"],
        positives=data["positives"],
        generated_at=datetime.utcnow()
    )
```

4. **Add Error Handling:**
```python
try:
    response = await self.client.chat.completions.create(...)
except openai.RateLimitError:
    # Handle rate limits
    await asyncio.sleep(60)
    return self.generate_summary(snapshot)  # Retry
except openai.APIError as e:
    # Handle API errors
    logger.error(f"OpenAI API error: {e}")
    return self._generate_fallback_summary(snapshot)
```

5. **Implement Caching:**
```python
from functools import lru_cache
import hashlib

def _snapshot_hash(self, snapshot: SystemSnapshot) -> str:
    key_metrics = f"{snapshot.queue_pending}-{snapshot.publish_success_rate}"
    return hashlib.md5(key_metrics.encode()).hexdigest()

@lru_cache(maxsize=100)
async def generate_summary_cached(self, snapshot_hash: str, snapshot: SystemSnapshot):
    return await self.generate_summary(snapshot)
```

6. **Cost Tracking:**
```python
class LLMClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.total_tokens = 0
        self.total_cost = 0.0
    
    async def generate_summary(self, snapshot: SystemSnapshot):
        response = await self.client.chat.completions.create(...)
        
        # Track usage
        usage = response.usage
        self.total_tokens += usage.total_tokens
        
        # Estimate cost (GPT-4 Turbo: $0.01/1K prompt, $0.03/1K completion)
        prompt_cost = (usage.prompt_tokens / 1000) * 0.01
        completion_cost = (usage.completion_tokens / 1000) * 0.03
        self.total_cost += prompt_cost + completion_cost
        
        return summary
```

---

## Testing

Run tests:
```bash
pytest backend/tests/test_ai_global_worker.py -v
```

Tests cover:
1. System snapshot collection
2. LLM client stub responses
3. Reasoning output structure
4. Runner state management
5. All API endpoints
6. Error handling
7. RBAC protection

---

## Troubleshooting

### Worker Not Running

Check configuration:
```python
# backend/app/core/config.py
AI_WORKER_ENABLED = True
AI_WORKER_INTERVAL_SECONDS = 30
```

Check logs:
```bash
grep "AI Worker" logs/app.log
```

### No Reasoning Available

Wait for first cycle (30 seconds default) or trigger manually:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/ai/global/run
```

### High Memory Usage

Reduce interval or disable worker:
```python
AI_WORKER_ENABLED = False
```

### Slow Reasoning

Check execution time in response:
```json
{
  "execution_time_ms": 2450  // Should be < 1000ms for stub
}
```

If using real LLM (PASO 7.2), optimize prompts or use faster model.

---

## Performance Considerations

- **Interval**: Default 30s is conservative. Can increase to 60-120s in production.
- **Snapshot Collection**: Optimized with indexed queries. ~50-100ms overhead.
- **LLM Stub**: Very fast (~10ms). Real LLM will be 1-3s per call.
- **Memory**: Stores only last reasoning (~50KB). No memory leak concerns.
- **Database Load**: Minimal. All queries use indexes. No heavy joins.

---

## Security

- All endpoints require JWT authentication
- RBAC enforces admin/manager access only
- Reasoning output does not expose sensitive credentials
- Snapshot sanitizes error messages
- No user-generated content in LLM prompts (PASO 7.2)

---

## Changelog

### PASO 7.0 (2025-11-22)
- Initial implementation with stub LLM client
- Background worker with configurable intervals
- 6 REST API endpoints
- Comprehensive system snapshot collection
- Health scoring and recommendations engine
- Action plan generation
- Full RBAC integration
- Test suite (12 tests)

### PASO 7.2 (Planned)
- OpenAI GPT-4.1 / GPT-5 integration
- Advanced prompt engineering
- Cost tracking and optimization
- Response caching
- Multi-model support

---

## License

Internal use only. Not for public distribution.

---

## Support

For questions or issues, contact the development team or file an issue in the repository.
