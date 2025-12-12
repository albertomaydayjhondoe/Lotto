# Publishing Webhooks Module

Simulated webhook handlers for social media platform callbacks during the publishing process.

## Overview

This module simulates the webhook callbacks that real social media platforms (Instagram, TikTok, YouTube) would send when posts are published or when asynchronous tasks complete.

In production, these webhooks would be called by the actual platform APIs. For development and testing, we can manually trigger them or use simulators.

## Architecture

```
POST /publishing/webhooks/instagram
POST /publishing/webhooks/tiktok  
POST /publishing/webhooks/youtube
         ↓
    router.py
         ↓
  instagram.py / tiktok.py / youtube.py
         ↓
  1. Find PublishLog by external_post_id
  2. Update extra_metadata with webhook data
  3. Log event to SocialSyncLedger
  4. Return {"status": "ok"}
```

## Webhook Handlers

### Instagram Webhook

**Endpoint:** `POST /publishing/webhooks/instagram`

**Payload Example:**
```json
{
  "external_post_id": "instagram_post_12345",
  "media_url": "https://www.instagram.com/p/ABC123/",
  "status": "published",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Behavior:**
- Searches for PublishLog with matching `external_post_id`
- Updates `extra_metadata` with:
  - `webhook_received`: true
  - `webhook_timestamp`: current timestamp
  - `webhook_platform`: "instagram"
  - `media_url`: provided URL
  - `webhook_status`: "published"
- Logs `publish_webhook_received` event to ledger

### TikTok Webhook

**Endpoint:** `POST /publishing/webhooks/tiktok`

**Payload Example:**
```json
{
  "external_post_id": "tiktok_video_67890",
  "task_id": "task_abc123",
  "complete": true,
  "video_url": "https://www.tiktok.com/@user/video/123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Behavior:**
- Searches for PublishLog with matching `external_post_id`
- Updates `extra_metadata` with:
  - `webhook_received`: true
  - `webhook_timestamp`: current timestamp
  - `webhook_platform`: "tiktok"
  - `task_id`: task identifier
  - `complete`: completion flag
  - `video_url`: published video URL
- Logs `publish_webhook_received` event to ledger

### YouTube Webhook

**Endpoint:** `POST /publishing/webhooks/youtube`

**Payload Example:**
```json
{
  "external_post_id": "youtube_video_XYZ789",
  "videoId": "dQw4w9WgXcQ",
  "publishAt": "2024-01-15T10:30:00Z",
  "status": "published",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Behavior:**
- Searches for PublishLog with matching `external_post_id`
- Updates `extra_metadata` with:
  - `webhook_received`: true
  - `webhook_timestamp`: current timestamp
  - `webhook_platform`: "youtube"
  - `videoId`: YouTube video ID
  - `publishAt`: publication time
  - `webhook_status`: "published"
- Logs `publish_webhook_received` event to ledger

## Usage

### Simulating a Webhook Call

```bash
# Instagram webhook
curl -X POST http://localhost:8000/publishing/webhooks/instagram \
  -H "Content-Type: application/json" \
  -d '{
    "external_post_id": "instagram_post_12345",
    "media_url": "https://www.instagram.com/p/ABC123/",
    "status": "published"
  }'

# TikTok webhook
curl -X POST http://localhost:8000/publishing/webhooks/tiktok \
  -H "Content-Type: application/json" \
  -d '{
    "external_post_id": "tiktok_video_67890",
    "task_id": "task_abc123",
    "complete": true
  }'

# YouTube webhook
curl -X POST http://localhost:8000/publishing/webhooks/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "external_post_id": "youtube_video_XYZ789",
    "videoId": "dQw4w9WgXcQ",
    "publishAt": "2024-01-15T10:30:00Z"
  }'
```

### Programmatic Usage

```python
from app.publishing_webhooks import handle_instagram_webhook

# Simulate Instagram callback
result = await handle_instagram_webhook(db, {
    "external_post_id": "ig_post_123",
    "media_url": "https://instagram.com/p/ABC/",
    "status": "published"
})
# Returns: {"status": "ok"}
```

## Integration with Reconciliation

The reconciliation module (`publishing_reconciliation`) uses the webhook data stored in `extra_metadata` to determine if publications were successful:

1. Worker publishes clip → receives `external_post_id`
2. Platform sends webhook → updates `extra_metadata["webhook_received"]`
3. Reconciliation checks `webhook_received` flag
4. If present → mark as success
5. If absent after timeout → mark as failed

## Event Logging

All webhooks log a `publish_webhook_received` event to the SocialSyncLedger with:
- `event_type`: "publish_webhook_received"
- `severity`: "info"
- `entity_type`: "publish_log"
- `entity_id`: PublishLog UUID
- `metadata`: platform-specific webhook data

## Error Handling

If a webhook cannot find the corresponding PublishLog:
```json
{
  "status": "error",
  "message": "Log not found"
}
```

This could happen if:
- The `external_post_id` doesn't match any log
- The platform doesn't match
- The log was deleted

## Testing

See `backend/tests/test_publishing_webhooks.py` for comprehensive webhook tests.

## Future Enhancements

1. **Webhook Authentication**: Add signature verification for real platform webhooks
2. **Idempotency**: Track webhook IDs to prevent duplicate processing
3. **Retry Mechanism**: Auto-retry failed webhook processing
4. **Batch Webhooks**: Support for processing multiple events in one call
5. **Webhook Queue**: Queue webhooks for asynchronous processing
6. **Rate Limiting**: Protect endpoints from excessive webhook traffic
