# Campaigns Engine - Clip Selection & Pre-Orchestrator

## Overview

The Campaigns Engine module provides intelligent clip selection and automated campaign creation capabilities. It integrates with the Rule Engine 2.0 to evaluate clips and select the best candidate for each platform, then creates internal draft campaigns ready for Meta Ads integration.

## Architecture

```
campaigns_engine/
├── schemas.py      # Pydantic models for requests/responses
├── selector.py     # Best clip selection logic using Rule Engine
├── services.py     # Campaign creation and orchestration services
└── __init__.py     # High-level orchestration functions
```

## Core Components

### 1. Clip Selection (selector.py)

**Purpose**: Select the best clip for each platform based on Rule Engine scores.

**Key Functions**:
- `select_best_clip_for_platform()`: Evaluates all clips for a video asset on a specific platform
- `select_best_clips_for_platforms()`: Batch selection across multiple platforms

**Selection Algorithm**:
1. Load all READY clips for the video asset
2. For each clip, get platform-specific Rule Engine weights
3. Evaluate clip with `RuleEngine.evaluate_clip()`
4. Select clip with highest score
5. UPSERT decision to `best_clip_decisions` table
6. Log to SocialSyncLedger with event_type="best_clip_selected"

**Database Persistence**:
- Stores decisions in `best_clip_decisions` table
- UNIQUE constraint on (video_asset_id, platform) prevents duplicates
- Subsequent calls overwrite previous decisions for same video+platform

### 2. Campaign Services (services.py)

**Purpose**: Create internal campaigns from clip selection decisions.

**Key Functions**:
- `create_internal_campaigns_for_decisions()`: Creates draft campaigns for each decision

**Campaign Creation**:
1. For each BestClipDecision, create a Campaign record:
   - `clip_id`: The winning clip
   - `status`: "draft"
   - `name`: Auto-generated (e.g., "INSTAGRAM auto-campaign for <video_asset_id>")
   - `budget_cents`: 0 (symbolic, updated later)
   - `optimization_meta`: JSON with source, score, platform
2. Log to SocialSyncLedger with event_type="campaign_created_auto"
3. Return list of campaign IDs

### 3. High-Level Orchestration (__init__.py)

**Purpose**: Unified interface for end-to-end orchestration.

**Key Functions**:
- `orchestrate_campaigns_for_video()`: Complete workflow from video asset to campaigns

**Workflow**:
1. Call selector for each requested platform
2. Create internal campaigns for all decisions
3. Return OrchestrateCampaignResponse with decisions and campaign IDs

## API Endpoints

### POST /campaigns/orchestrate

Orchestrate campaigns for a video asset across specified platforms.

**Request**:
```json
{
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "platforms": ["tiktok", "instagram", "youtube"]
}
```

**Response**:
```json
{
  "decisions": [
    {
      "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "instagram",
      "clip_id": "660e8400-e29b-41d4-a716-446655440001",
      "score": 0.87,
      "decided_at": "2025-11-20T10:30:00Z"
    }
  ],
  "campaigns_created": [
    "770e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Status Codes**:
- 200: Success
- 404: Video asset not found
- 422: Validation error

### GET /campaigns/best_clip

Retrieve the best clip decision for a video asset and platform.

**Query Parameters**:
- `video_asset_id`: UUID (required)
- `platform`: tiktok|instagram|youtube (required)

**Response**:
```json
{
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "instagram",
  "clip_id": "660e8400-e29b-41d4-a716-446655440001",
  "score": 0.87,
  "decided_at": "2025-11-20T10:30:00Z"
}
```

**Status Codes**:
- 200: Decision found
- 404: No decision exists for this video_asset_id + platform

**Note**: This endpoint only reads from the database. It does NOT trigger clip evaluation. Use POST /campaigns/orchestrate to create new decisions.

## Database Schema

### best_clip_decisions Table

```sql
CREATE TABLE best_clip_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_asset_id UUID NOT NULL REFERENCES video_assets(id),
    platform TEXT NOT NULL,
    clip_id UUID NOT NULL REFERENCES clips(id),
    score DOUBLE PRECISION NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (video_asset_id, platform)
);

CREATE INDEX idx_best_clip_decisions_video_platform 
    ON best_clip_decisions(video_asset_id, platform);
CREATE INDEX idx_best_clip_decisions_clip 
    ON best_clip_decisions(clip_id);
```

### campaigns Table Extensions

No schema changes needed. Uses existing `campaigns` table with:
- `optimization_meta` JSON field stores orchestrator metadata
- Identifies auto-created campaigns via `{"source": "auto_orchestrator"}`

## Integration with Rule Engine

The Campaigns Engine is a **consumer** of Rule Engine 2.0:

1. **Evaluation**: Uses `RuleEngine.evaluate_clip()` to score clips
2. **Platform Heuristics**: Automatically applies platform-specific weights
3. **Adaptive Learning**: Benefits from Rule Engine training without modification

**Example Integration**:
```python
from app.rules_engine import RuleEngine
from app.campaigns_engine.selector import select_best_clip_for_platform

# Rule Engine evaluates clips
engine = RuleEngine()
decision = await select_best_clip_for_platform(
    db, 
    video_asset_id=uuid,
    platform="instagram"
)
# decision.clip_id contains the clip with highest Rule Engine score
```

## Ledger Events

### best_clip_selected

Logged when a clip is selected as winner for a platform.

```json
{
  "event_type": "best_clip_selected",
  "entity_type": "video_asset",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "clip_id": "660e8400-e29b-41d4-a716-446655440001",
    "score": 0.87,
    "num_candidates": 5
  }
}
```

### campaign_created_auto

Logged when an internal campaign is created by the orchestrator.

```json
{
  "event_type": "campaign_created_auto",
  "entity_type": "campaign",
  "entity_id": "770e8400-e29b-41d4-a716-446655440002",
  "metadata": {
    "platform": "instagram",
    "clip_id": "660e8400-e29b-41d4-a716-446655440001",
    "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
    "score": 0.87
  }
}
```

## Usage Examples

### Orchestrate Campaigns for a Video

```python
from app.campaigns_engine import orchestrate_campaigns_for_video

response = await orchestrate_campaigns_for_video(
    db=db_session,
    video_asset_id=my_video_uuid,
    platforms=["tiktok", "instagram", "youtube"]
)

print(f"Created {len(response.campaigns_created)} campaigns")
for decision in response.decisions:
    print(f"{decision.platform}: clip {decision.clip_id} (score: {decision.score:.2f})")
```

### Check Previously Selected Clip

```python
from app.campaigns_engine.selector import get_best_clip_decision

decision = await get_best_clip_decision(
    db=db_session,
    video_asset_id=my_video_uuid,
    platform="instagram"
)

if decision:
    print(f"Instagram best clip: {decision.clip_id} (score: {decision.score:.2f})")
else:
    print("No decision found - orchestrate first")
```

## Testing

Comprehensive test coverage in `tests/test_campaigns_engine.py`:

- `test_select_best_clip_for_platform_simple`: Basic selection logic
- `test_select_best_clips_for_multiple_platforms`: Multi-platform batch selection
- `test_create_internal_campaigns_for_decisions`: Campaign creation
- `test_orchestrate_campaigns_for_video_endpoint`: Full API integration
- `test_get_best_clip_endpoint`: Read endpoint functionality
- `test_best_clip_uses_rule_engine_scores`: Validates Rule Engine integration

Run tests:
```bash
pytest tests/test_campaigns_engine.py -v
```

## Future Enhancements

1. **Meta Ads Integration**: Connect draft campaigns to real Meta Business Manager
2. **Budget Optimization**: Use historical performance to set smart budgets
3. **A/B Testing**: Create multiple campaigns per platform to test variants
4. **Scheduling**: Auto-schedule campaigns based on optimal posting times
5. **Performance Feedback**: Feed campaign results back to Rule Engine for training
6. **Multi-Clip Campaigns**: Support multiple clips per campaign for carousel ads

## Dependencies

- **Rule Engine 2.0**: Provides clip evaluation and scoring
- **SocialSyncLedger**: Event logging and audit trail
- **SQLAlchemy**: Database persistence
- **FastAPI**: API endpoints
- **Pydantic**: Data validation and serialization
