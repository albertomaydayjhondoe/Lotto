# E2B Sandbox Simulation Engine

## Overview

The E2B Sandbox Simulation Engine provides a complete simulation of video analysis workflows without requiring external services or GPU-intensive processing. It generates realistic fake data for YOLO object detection, video embeddings, trend analysis, and intelligent video cuts.

## Purpose

This module serves multiple purposes:

1. **Development**: Test the full video processing pipeline without external dependencies
2. **CI/CD**: Run tests that validate workflow logic without actual AI models
3. **Prototyping**: Demonstrate the system's capabilities before implementing real ML models
4. **Cost Control**: Avoid expensive API calls during development and testing

## Architecture

```
app/e2b/
├── models.py       # Pydantic data models for requests/responses
├── runner.py       # Core simulation logic
├── dispatcher.py   # Job routing and execution
├── callbacks.py    # Result processing and validation
├── api.py          # REST API endpoints
└── __init__.py     # Module exports
```

## Core Components

### 1. Simulation Runner (runner.py)

**Function**: `run_e2b_simulation(job, db)`

Generates complete fake video analysis:
- **YOLO Detections**: 10-30 random object detections (person, car, dog, etc.)
- **Embeddings**: 512-dimensional vectors every 1000ms
- **Trend Features**: Hashtag, audio, and visual trend scores
- **Video Cuts**: 3-12 intelligent clips with calculated scores

**Score Formula**:
```
cut_score = 0.6 × visual_score + 0.2 × motion_intensity + 0.2 × trend_score
```

**Output**:
- Creates `Clip` records in database (status=READY)
- Logs events to SocialSyncLedger
- Returns `E2BSandboxResult` with all generated data

### 2. Job Dispatcher (dispatcher.py)

**Function**: `dispatch_e2b_job(job, db)`

Routes jobs with `job_type="cut_analysis_e2b"` to the simulation engine:
1. Updates job status to PROCESSING
2. Executes `run_e2b_simulation()`
3. Updates job with results
4. Handles errors and logs events

**Function**: `should_use_e2b_dispatcher(job)`

Determines if a job should use E2B simulation (returns True for "cut_analysis_e2b").

### 3. Callbacks (callbacks.py)

**Function**: `process_e2b_callback(job_id, result, db)`

Processes callbacks from simulated "external" E2B sandbox:
- Updates job status (COMPLETED/FAILED)
- Stores results in job.result
- Logs callback receipt to ledger

**Function**: `validate_e2b_callback(result)`

Validates E2BSandboxResult structure:
- Checks status is "completed" or "failed"
- Verifies cuts exist for completed jobs
- Validates all scores are in [0, 1] range

### 4. Data Models (models.py)

**FakeYoloDetection**:
```python
{
  "class_name": "person",
  "confidence": 0.95,
  "bbox": [100, 50, 200, 300],
  "timestamp_ms": 5000
}
```

**FakeTrendFeatures**:
```python
{
  "hashtag_relevance": 0.8,
  "audio_trend_score": 0.75,
  "visual_trend_score": 0.85,
  "overall_trend_score": 0.80
}
```

**FakeEmbedding**:
```python
{
  "vector": [0.1, -0.5, ..., 0.3],  # 512 floats
  "model_name": "fake-clip-vit",
  "timestamp_ms": 3000
}
```

**FakeCut**:
```python
{
  "start_ms": 0,
  "end_ms": 10000,
  "duration_ms": 10000,
  "visual_score": 0.85,
  "motion_intensity": 0.70,
  "trend_score": 0.65,
  "confidence": 0.80
}
```

**E2BSandboxResult**:
Complete simulation output with all generated data plus metadata.

## API Endpoints

### POST /e2b/jobs/launch

Launch E2B simulation for a video asset.

**Request**:
```json
{
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",  // optional
  "job_type": "cut_analysis_e2b",
  "params": {}
}
```

**Response**:
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "num_cuts_created": 7,
  "processing_time_ms": 245
}
```

### POST /e2b/jobs/{job_id}/callback

Receive callback from E2B sandbox (simulates external service).

**Request**:
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "cuts": [...],
  "yolo_detections": [...],
  "embeddings": [...],
  "trend_features": {...},
  "processing_time_ms": 245
}
```

**Response**:
```json
{
  "status": "callback_received",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_status": "completed",
  "num_cuts": 7
}
```

### GET /e2b/jobs/{job_id}/status

Get status of E2B job.

**Response**:
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_type": "cut_analysis_e2b",
  "status": "completed",
  "video_asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "status": "completed",
    "num_cuts": 7,
    "num_detections": 23,
    "num_embeddings": 31,
    "processing_time_ms": 245
  }
}
```

## Integration with Job Runner

The E2B dispatcher is integrated into the main job processing flow:

```python
# In app/worker/dispatcher.py
DISPATCH_TABLE = {
    "cut_analysis": run_cut_analysis,      # Real analysis
    "cut_analysis_e2b": dispatch_e2b_job,  # E2B simulation
}
```

Jobs with `job_type="cut_analysis_e2b"` are automatically routed to the E2B simulation engine.

## Usage Examples

### Launch E2B Job Programmatically

```python
from app.e2b import dispatch_e2b_job
from app.models.database import Job, JobStatus

job = Job(
    id=uuid4(),
    job_type="cut_analysis_e2b",
    status=JobStatus.PENDING,
    video_asset_id=my_video_id,
    params={}
)
db.add(job)
await db.commit()

# Dispatch to E2B
result = await dispatch_e2b_job(job=job, db=db)

print(f"Created {len(result.cuts)} clips")
```

### Launch via API

```bash
curl -X POST http://localhost:8000/e2b/jobs/launch \
  -H "Content-Type: application/json" \
  -d '{
    "video_asset_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Check Job Status

```bash
curl http://localhost:8000/e2b/jobs/{job_id}/status
```

## Ledger Events

The E2B engine logs the following events:

**e2b_simulation_completed**:
```json
{
  "event_type": "e2b_simulation_completed",
  "entity_type": "job",
  "entity_id": "job-uuid",
  "metadata": {
    "video_asset_id": "video-uuid",
    "num_detections": 23,
    "num_embeddings": 31,
    "num_cuts": 7,
    "processing_time_ms": 245
  }
}
```

**e2b_callback_received**:
```json
{
  "event_type": "e2b_callback_received",
  "entity_type": "job",
  "entity_id": "job-uuid",
  "metadata": {
    "result_status": "completed",
    "num_cuts": 7,
    "processing_time_ms": 245,
    "has_error": false
  }
}
```

## Testing

Comprehensive test suite in `tests/test_e2b_simulation.py`:

- `test_e2b_job_creation`: Job creation and persistence
- `test_e2b_simulation_creates_clips`: Clip generation and DB insertion
- `test_e2b_scores_are_calculated`: Score validation and formula
- `test_e2b_callback_updates_job`: Callback processing
- `test_e2b_integration_with_job_runner`: Full dispatcher integration
- `test_e2b_callback_validation`: Input validation
- `test_e2b_generates_detections_and_embeddings`: Data generation

Run tests:
```bash
pytest tests/test_e2b_simulation.py -v
```

## Configuration

No special configuration needed. The E2B engine uses:
- Video duration from `VideoAsset.duration_ms` (defaults to 30s if not set)
- Random number generation for realistic variability
- Fixed parameters for consistency:
  - 10-30 YOLO detections
  - 512-dimensional embeddings
  - 3-12 video cuts
  - Cuts between 5-15 seconds

## Comparison: E2B vs Real Analysis

| Feature | E2B Simulation | Real Analysis |
|---------|----------------|---------------|
| Speed | ~200ms | 30-120s |
| Cost | $0 | ~$0.10-0.50 per video |
| Accuracy | Random (0.5-0.95) | Model-dependent |
| GPU Required | No | Yes |
| Use Case | Dev/Testing | Production |
| Job Type | cut_analysis_e2b | cut_analysis |

## Migration Path

To switch from E2B to real analysis:

1. Change job type from `"cut_analysis_e2b"` to `"cut_analysis"`
2. Ensure real analysis handler is properly configured
3. Update any hardcoded job type references
4. Test with small batch before full migration

## Future Enhancements

1. **Configurable Variability**: Allow tuning randomness levels
2. **Preset Scenarios**: Pre-defined result patterns for specific test cases
3. **Performance Simulation**: Add configurable delays to simulate real processing time
4. **Dataset Generation**: Create synthetic training data for ML models
5. **Error Simulation**: Inject failures to test error handling

## Dependencies

- **SQLAlchemy**: Database operations
- **Pydantic**: Data validation
- **Python random**: Data generation
- **SocialSyncLedger**: Event logging

## Troubleshooting

**No clips created:**
- Check video_asset exists and has valid duration_ms
- Verify job.video_asset_id is correct
- Check database permissions

**Invalid scores:**
- E2B generates scores in [0.5, 0.95] range
- Scores are randomly generated but validated
- Check FakeCut validation in models.py

**Job stuck in PROCESSING:**
- Check for uncaught exceptions in runner.py
- Verify database commit is called
- Check ledger for error events

## License

Part of the Stakazo platform. Internal use only.
