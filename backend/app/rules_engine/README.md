# Rule Engine 2.0

## Overview

The Rule Engine 2.0 is a dynamic, adaptive scoring system that evaluates clips based on multiple features and learns from real-world performance data.

## Architecture

### Core Components

1. **models.py** - Data models
   - `RuleWeight`: Individual feature weight
   - `AdaptiveRuleSet`: Complete weight set for a platform

2. **engine.py** - Main interface
   - `RuleEngine`: High-level API for evaluating and training

3. **evaluator.py** - Clip evaluation
   - Normalizes features (visual_score, duration, position, motion)
   - Applies weighted scoring
   - Logs evaluation events to ledger

4. **trainer.py** - Adaptive learning
   - Reads performance data from ledger
   - Updates weights based on outcomes
   - Uses gradient-like optimization

5. **heuristics.py** - Platform-specific rules
   - TikTok: Prioritizes short duration + motion
   - Instagram: Prioritizes visual quality + 15-30s duration
   - YouTube: Prioritizes longer content + narrative

6. **loader.py** - Database loading
   - Loads rules from `rules_engine_weights` table
   - Falls back to defaults if not found

7. **persistence.py** - Database persistence
   - Saves updated rules to database
   - UPSERT operations for weight updates

## Database Schema

### Table: `rules_engine_weights`

```sql
CREATE TABLE rules_engine_weights (
    platform TEXT PRIMARY KEY,
    weights JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Default Weights

Initial weights for all platforms:

```json
{
  "visual_score": 0.5,
  "duration_ms": 0.2,
  "cut_position": 0.2,
  "motion_intensity": 0.1
}
```

## API Endpoints

### GET /rules/engine/weights
Get current weights for a platform.

**Query Parameters:**
- `platform`: tiktok | instagram | youtube

**Response:**
```json
{
  "platform": "tiktok",
  "weights": {
    "visual_score": 0.45,
    "duration_ms": 0.15,
    "cut_position": 0.2,
    "motion_intensity": 0.2
  },
  "updated_at": "2025-11-20T12:00:00Z"
}
```

### POST /rules/engine/evaluate
Evaluate a clip for a specific platform.

**Request:**
```json
{
  "clip_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "tiktok"
}
```

**Response:**
```json
{
  "clip_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "tiktok",
  "score": 0.87
}
```

### POST /rules/engine/train
Train weights based on performance data.

**Request:**
```json
{
  "platform": "instagram"
}
```

**Response:**
```json
{
  "platform": "instagram",
  "weights": {
    "visual_score": 0.55,
    "duration_ms": 0.18,
    "cut_position": 0.2,
    "motion_intensity": 0.07
  },
  "updated_at": "2025-11-20T12:05:00Z"
}
```

## Usage Example

```python
from app.rules_engine import RuleEngine
from app.core.database import get_db

engine = RuleEngine()

# Get current rules
rules = await engine.get_rules(db, "tiktok")

# Evaluate a clip
score = await engine.evaluate_clip(db, clip_id, "instagram")

# Train from performance data
updated_rules = await engine.train(db, "youtube")
```

## Integration with Cut Analysis

The Rule Engine is integrated with the cut analysis handler:
- After creating each clip, it's automatically evaluated
- Score is stored in the clip's `visual_score` field
- Evaluation event is logged to the ledger

## Adaptive Learning

The trainer analyzes ledger events to identify successful clips:
- High engagement → target = 1.0
- Low engagement → target = 0.0
- Weights are updated using gradient-like optimization
- Learning rate: α = 0.05 (conservative)

## Platform Heuristics

### TikTok
- Optimal duration: ≤ 15s
- Motion intensity weight multiplied by 1.5
- Fast-paced content prioritized

### Instagram
- Optimal duration: 15-30s
- Visual score prioritized (multiplied by 1.3)
- Aesthetic quality emphasized

### YouTube
- Optimal duration: 45-60s
- Narrative flow prioritized
- Longer content not penalized

## Testing

Run the test suite:
```bash
cd backend
pytest tests/test_rule_engine.py -v
```

Test coverage:
- Initial weights validation
- Clip evaluation scoring
- Platform heuristics application
- Adaptive training
- Database persistence
- API endpoints integration
