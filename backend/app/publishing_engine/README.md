# Publishing Engine

## Overview

The Publishing Engine handles automated publication of clips to social media platforms (Instagram, TikTok, YouTube). This is **Step 2** of the implementation, which includes internal logic, simulators, and API endpoints **without real platform integration**.

## Architecture

```
publishing_engine/
├── models.py      # Pydantic request/response models
├── service.py     # Core publication logic
├── simulator.py   # Platform simulators (10% failure rate)
├── router.py      # FastAPI endpoints
└── __init__.py    # Module exports
```

### Database Schema

The engine uses two tables created in migration `005_publishing_engine.py`:

**social_accounts**
- Stores social media account credentials
- Supports main accounts and satellites
- Platform-specific configuration

**publish_logs**
- Tracks all publication attempts
- Links to clips and social accounts
- Stores external post IDs and URLs
- Captures errors for failed publications

## Components

### 1. Models (models.py)

#### PublishRequest
```python
{
  "clip_id": "uuid",
  "platform": "instagram|tiktok|youtube",
  "social_account_id": "uuid (optional)",
  "metadata": {
    "caption": "...",
    "hashtags": ["#tag1", "#tag2"]
  }
}
```

#### PublishResult
```python
{
  "success": true,
  "external_post_id": "ig_abc123",
  "external_url": "https://instagram.com/p/abc123/",
  "error_message": null,
  "platform": "instagram",
  "clip_id": "uuid",
  "social_account_id": "uuid"
}
```

### 2. Simulators (simulator.py)

Simulates real platform APIs for testing without external dependencies.

**Features:**
- **Network delay**: 0.1-0.3 seconds
- **Failure rate**: 10% random failures
- **Realistic responses**: Generates fake post IDs and URLs
- **Platform-specific errors**: Different error messages per platform

**Platforms:**
- `instagram`: Simulates Instagram Graph API
- `tiktok`: Simulates TikTok Content Posting API
- `youtube`: Simulates YouTube Shorts upload

**Example simulator call:**
```python
from app.publishing_engine.simulator import get_simulator

simulator = await get_simulator("instagram")
result = await simulator(publish_request)
```

### 3. Service (service.py)

Core business logic for publication workflow.

#### `publish_clip(db, request) -> PublishResult`

**Workflow:**
1. ✅ **Validate clip exists** - Query clips table
2. ✅ **Validate social account** (if provided) - Verify account exists and platform matches
3. ✅ **Create pending log** - Insert PublishLogModel with status="pending"
4. ✅ **Call simulator** - Execute platform-specific publish simulation
5. ✅ **Update log** - Mark success/failed, save external IDs
6. ✅ **Log to ledger** - Record events: publish_started, publish_successful, publish_failed
7. ✅ **Return result** - PublishResult with success status

**Error handling:**
- Clip not found → ValueError
- Social account not found → ValueError
- Platform mismatch → ValueError
- Unsupported platform → ValueError
- Simulator errors → Captured in PublishLog

#### `get_publish_logs_for_clip(db, clip_id) -> list[PublishLogModel]`

Retrieves all publish attempts for a clip, ordered by most recent first.

### 4. Router (router.py)

FastAPI endpoints for publication API.

#### POST /publishing/publish

Publishes a clip to a social platform.

**Request:**
```bash
curl -X POST http://localhost:8000/publishing/publish \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "instagram",
    "social_account_id": "660e8400-e29b-41d4-a716-446655440001",
    "metadata": {
      "caption": "Check out this amazing clip! #viral",
      "hashtags": ["#trending", "#stakazo"]
    }
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "external_post_id": "ig_abc123def456",
  "external_url": "https://www.instagram.com/p/ig_abc123def456/",
  "error_message": null,
  "platform": "instagram",
  "clip_id": "550e8400-e29b-41d4-a716-446655440000",
  "social_account_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Response (Failure):**
```json
{
  "success": false,
  "external_post_id": null,
  "external_url": null,
  "error_message": "Instagram API rate limit exceeded (simulated)",
  "platform": "instagram",
  "clip_id": "550e8400-e29b-41d4-a716-446655440000",
  "social_account_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### GET /publishing/logs/{clip_id}

Retrieves all publish logs for a specific clip.

**Request:**
```bash
curl http://localhost:8000/publishing/logs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "clip_id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "instagram",
    "social_account_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "success",
    "external_post_id": "ig_abc123",
    "external_url": "https://instagram.com/p/ig_abc123/",
    "error_message": null,
    "requested_at": "2025-11-20T10:30:00Z",
    "published_at": "2025-11-20T10:30:01Z",
    "created_at": "2025-11-20T10:30:00Z",
    "updated_at": "2025-11-20T10:30:01Z"
  }
]
```

## Integration with SocialSyncLedger

The Publishing Engine logs all operations to the SocialSyncLedger for audit trails and analytics.

**Events logged:**

### publish_started
```json
{
  "event_type": "publish_started",
  "entity_type": "clip",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "social_account_id": "660e8400-e29b-41d4-a716-446655440001",
    "publish_log_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

### publish_provider_ready
```json
{
  "event_type": "publish_provider_ready",
  "entity_type": "clip",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "provider": "instagram",
    "publish_log_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

### publish_provider_fallback
```json
{
  "event_type": "publish_provider_fallback",
  "entity_type": "clip",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "reason": "incomplete_config",
    "publish_log_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

### publish_successful
```json
{
  "event_type": "publish_successful",
  "entity_type": "clip",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "external_post_id": "ig_abc123",
    "external_url": "https://instagram.com/p/ig_abc123/",
    "publish_log_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

### publish_failed
```json
{
  "event_type": "publish_failed",
  "entity_type": "clip",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "platform": "instagram",
    "error": "Instagram API rate limit exceeded",
    "publish_log_id": "770e8400-e29b-41d4-a716-446655440002"
  }
}
```

## Provider Client Integration Flow (PASO 5.3)

Starting from PASO 5.3, the Publishing Engine intelligently chooses between **simulators** and **real provider clients** based on whether encrypted credentials exist for a social account.

### Architecture

```
publish_clip() Flow:
┌─────────────────────────────────────┐
│ 1. Validate Clip + Social Account  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Check if credentials exist       │
│    get_account_credentials(db, id)  │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    ✅ Has Creds   ❌ No Creds
         │           │
         ▼           ▼
    ┌─────────┐   ┌──────────┐
    │Provider │   │Simulator │
    │ Client  │   │  (stub)  │
    └─────────┘   └──────────┘
         │           │
         └─────┬─────┘
               ▼
    ┌──────────────────────┐
    │ 3. Execute Publish   │
    │    (stub mode)       │
    └──────────────────────┘
```

### supports_real_api() Method

Each provider client implements `supports_real_api()` to validate if all required credentials are present:

**Instagram:**
```python
def supports_real_api(self) -> bool:
    access_token = self.config.get("access_token")
    instagram_account_id = self.config.get("instagram_account_id")
    return bool(access_token and instagram_account_id)
```

**TikTok:**
```python
def supports_real_api(self) -> bool:
    client_key = self.config.get("client_key")
    client_secret = self.config.get("client_secret")
    access_token = self.config.get("access_token")
    return bool(client_key and client_secret and access_token)
```

**YouTube:**
```python
def supports_real_api(self) -> bool:
    client_id = self.config.get("client_id")
    client_secret = self.config.get("client_secret")
    access_token = self.config.get("access_token")
    return bool(client_id and client_secret and access_token)
```

### Fallback Logic

The engine gracefully falls back to simulators in these scenarios:

1. **No credentials stored** → Use simulator
2. **Incomplete credentials** (e.g., missing access_token) → Use simulator
3. **Credential decryption error** → Use simulator
4. **Unsupported platform** → Use simulator

All fallback events are logged to ledger with event type `publish_provider_fallback`.

### Usage Example

```python
from app.publishing_engine import publish_clip, PublishRequest
from app.services.social_accounts import set_account_credentials

# Step 1: Store encrypted credentials for social account
credentials = {
    "access_token": "IG_TOKEN_12345",
    "instagram_account_id": "123456789",
    "facebook_page_id": "page_123"
}
await set_account_credentials(db, social_account.id, credentials)

# Step 2: Publish clip
request = PublishRequest(
    clip_id=clip_uuid,
    platform="instagram",
    social_account_id=social_account.id,
    metadata={"caption": "Amazing clip! #viral"}
)

# Engine will automatically:
# - Detect credentials exist
# - Get provider client for account
# - Check if supports_real_api() returns True
# - Use provider client (stub mode) instead of simulator
result = await publish_clip(db, request)

# Check ledger for "publish_provider_ready" event
```

### Stub Methods

Provider clients currently use stub methods (not real API calls):

**upload_video_stub(file_path, **kwargs)**
- Simulates video upload
- Returns fake video_id
- Maintains same interface as real `upload_video()`

**publish_post_stub(video_id, **kwargs)**
- Simulates post publishing
- Returns fake post_id and post_url
- Maintains same interface as real `publish_post()`

These stub methods will be replaced with real API calls in future phases (PASO 5.4+).

### Ledger Events

When provider client is used, additional events are logged:

- **`publish_provider_ready`**: Provider client has valid credentials and is ready
- **`publish_provider_fallback`**: Falling back to simulator (with reason)

### Testing

Tests verify the integration logic:

```bash
# Run provider integration tests
pytest backend/tests/test_publishing_provider_integration.py -v
```

**Test Coverage:**
- ✅ Simulator used when no credentials
- ✅ Provider client used when credentials present (stub mode)
- ✅ Fallback to simulator on incomplete credentials
- ✅ Fallback to simulator on credential errors
- ✅ Proper ledger event logging

### Configuration

No additional configuration needed - the integration is automatic:

1. If `SocialAccount` has encrypted credentials → Try provider client
2. If provider client's `supports_real_api()` returns True → Use it (stub mode)
3. Otherwise → Fall back to simulator

This ensures zero breaking changes while preparing the architecture for real API integration.

## Complete Publication Flow

```
1. Client sends POST /publishing/publish
   ↓
2. service.publish_clip() validates clip and account
   ↓
3. Create PublishLog (status="pending")
   ↓
4. Log "publish_started" to ledger
   ↓
5. Call platform simulator (instagram/tiktok/youtube)
   ↓
6. Simulator returns success or failure (10% failure rate)
   ↓
7. Update PublishLog:
   - Success: status="success", external_post_id, external_url, published_at
   - Failure: status="failed", error_message
   ↓
8. Log "publish_successful" or "publish_failed" to ledger
   ↓
9. Return PublishResult to client
```

## Testing

Run tests:
```bash
pytest backend/tests/test_publishing_engine.py -v
```

**Test coverage:**
- ✅ Successful publication
- ✅ Failed publication (simulated)
- ✅ Publication without social account
- ✅ Query publish logs endpoint
- ✅ Validation errors (clip not found, account not found)
- ✅ Platform mismatch validation

## Database Compatibility

**Fully compatible with:**
- ✅ SQLite (in-memory for tests)
- ✅ PostgreSQL (production)

**Key compatibility features:**
- Uses Integer (0/1) instead of Boolean for SQLite
- JSON columns work in both databases
- UUID columns compatible via sqlalchemy.dialects.postgresql.UUID

## Limitations (Step 2)

This implementation uses **simulators only**. Real platform integration will be added in Step 3:

- ❌ No real Instagram Graph API integration
- ❌ No real TikTok Content Posting API
- ❌ No real YouTube Data API v3
- ❌ No OAuth2 authentication flows
- ❌ No rate limiting beyond simulated failures
- ❌ No webhook handling for post status updates

**What works:**
- ✅ Complete internal logic and workflow
- ✅ Database persistence
- ✅ Ledger integration
- ✅ Error handling
- ✅ API endpoints
- ✅ Comprehensive tests

## Future Enhancements (Step 3)

1. **Real Platform Integration**
   - Instagram Graph API for posts and reels
   - TikTok Content Posting API
   - YouTube Data API v3 for Shorts

2. **OAuth2 Authentication**
   - Account linking flow
   - Token refresh logic
   - Secure credential storage

3. **Advanced Features**
   - Scheduled publishing
   - A/B testing captions
   - Automatic hashtag generation
   - Cross-posting to multiple accounts
   - Post performance analytics

4. **Webhooks**
   - Instagram webhook for post insights
   - TikTok webhook for video status
   - YouTube webhook for processing status

## Usage Example

```python
from app.publishing_engine import publish_clip, PublishRequest

# Create request
request = PublishRequest(
    clip_id=clip_uuid,
    platform="instagram",
    social_account_id=account_uuid,
    metadata={
        "caption": "Amazing clip! #viral",
        "hashtags": ["#trending", "#stakazo"]
    }
)

# Publish
result = await publish_clip(db, request)

if result.success:
    print(f"Published to {result.external_url}")
else:
    print(f"Failed: {result.error_message}")
```

## API Integration in main.py

```python
from app.publishing_engine import router as publishing_router

app.include_router(
    publishing_router, 
    prefix="/publishing", 
    tags=["publishing"]
)
```

## Error Codes

| HTTP Status | Description |
|------------|-------------|
| 200 | Successful publication |
| 404 | Clip or social account not found |
| 400 | Validation error (platform mismatch, etc.) |
| 500 | Internal server error |
