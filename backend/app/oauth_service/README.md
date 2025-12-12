```markdown
# OAuth Service Module

OAuth token management infrastructure for social media platform integrations.

## Overview

This module provides the foundation for OAuth 2.0 token management in the Stakazo publishing system. It handles:

- **Token Information Retrieval**: Get OAuth tokens from social accounts
- **Expiration Checking**: Detect when tokens are expired or close to expiration
- **Automatic Token Refresh**: Refresh access tokens using refresh tokens
- **Integration with Publishing**: Ensure valid tokens before API calls

## Status: Infrastructure Only (PASO 5.4)

⚠️ **IMPORTANT**: This is infrastructure-only implementation. Real OAuth flows and API calls are NOT yet implemented.

**What works:**
- ✅ Database schema for OAuth tokens
- ✅ Token retrieval and expiration logic
- ✅ Simulated token refresh (for testing)
- ✅ Integration with account binding
- ✅ Comprehensive test coverage

**What's NOT implemented (yet):**
- ❌ Real OAuth authorization flows
- ❌ Browser-based login redirects
- ❌ Real API calls to Instagram/TikTok/YouTube OAuth endpoints
- ❌ OAuth callback handling
- ❌ User consent screens

## Architecture

```
SocialAccountModel
├── oauth_provider (string)      # "instagram", "tiktok", "youtube"
├── oauth_access_token (text)    # Current access token
├── oauth_refresh_token (text)   # Refresh token for renewal
├── oauth_expires_at (datetime)  # Token expiration time (UTC)
└── oauth_scopes (json)          # Granted scopes list
```

### Token Lifecycle

```
1. User authorizes app (future implementation)
   ↓
2. Store access_token + refresh_token in SocialAccountModel
   ↓
3. Publishing engine calls get_provider_client_for_account()
   ↓
4. account_binding calls ensure_valid_access_token()
   ↓
5. Check if token is expired or close to expiration
   ├─ No  → Use existing token
   └─ Yes → refresh_oauth_token()
           ├─ Call platform OAuth refresh endpoint (TODO)
           ├─ Update oauth_access_token
           ├─ Update oauth_expires_at
           └─ Return new token
   ↓
6. Construct provider client with valid token
   ↓
7. Make API calls
```

## Modules

### models.py

Pydantic models for OAuth data structures.

**OAuthTokenInfo**
- Represents OAuth token data from a social account
- Fields: access_token, refresh_token, expires_at, scopes, provider

**OAuthRefreshResult**
- Result of a token refresh operation
- Fields: success, provider, reason, new_access_token, new_expires_at

### service.py

Core OAuth token management functions.

**get_account_oauth_info(db, social_account_id)**
- Retrieve OAuth token info for an account
- Returns OAuthTokenInfo or None

**is_token_expired_or_close(info, threshold_seconds=300)**
- Check if token is expired or within threshold of expiration
- Returns True if refresh is needed

**refresh_oauth_token(db, account)**
- Refresh OAuth access token using refresh token
- Currently simulated - TODO: Implement real API calls
- Returns OAuthRefreshResult

**ensure_valid_access_token(db, account)**
- Ensure account has valid (non-expired) access token
- Automatically refreshes if needed
- Returns (account, refresh_result)

## Usage

### Checking Token Expiration

```python
from app.oauth_service import get_account_oauth_info, is_token_expired_or_close

# Get token info
token_info = await get_account_oauth_info(db, account.id)

if token_info:
    # Check if token needs refresh (within 5 minutes of expiration)
    if is_token_expired_or_close(token_info, threshold_seconds=300):
        print("Token needs refresh")
```

### Refreshing Tokens

```python
from app.oauth_service import refresh_oauth_token

result = await refresh_oauth_token(db, account)

if result.success:
    print(f"Token refreshed! New expiration: {result.new_expires_at}")
else:
    print(f"Refresh failed: {result.reason}")
```

### Automatic Token Refresh (Recommended)

```python
from app.oauth_service import ensure_valid_access_token

# This automatically refreshes if needed
account, refresh_result = await ensure_valid_access_token(db, account)

if refresh_result and not refresh_result.success:
    logger.warning(f"Token refresh failed: {refresh_result.reason}")

# Use account.oauth_access_token for API calls
# Token is guaranteed to be valid (or refresh was attempted)
```

### Integration with Account Binding

The OAuth service is automatically integrated with `get_provider_client_for_account()`:

```python
from app.publishing_integrations.account_binding import get_provider_client_for_account

# This internally calls ensure_valid_access_token()
client = await get_provider_client_for_account(db, account)

# Token was already refreshed if needed - safe to use client
await client.authenticate()
result = await client.upload_video("/path/to/video.mp4")
```

## Database Migration

Migration `008_oauth_tokens.py` adds OAuth fields to `social_accounts` table.

**To apply:**
```bash
cd backend
alembic upgrade head
```

**To rollback:**
```bash
alembic downgrade -1
```

⚠️ **Warning**: Downgrading will permanently delete all stored OAuth tokens.

## Testing

Comprehensive test suite in `backend/tests/test_oauth_service.py`.

**Run tests:**
```bash
# Run OAuth tests only
pytest backend/tests/test_oauth_service.py -v

# Run with coverage
pytest backend/tests/test_oauth_service.py --cov=app.oauth_service -v
```

**Test Coverage:**
- ✅ Token info retrieval (with/without tokens)
- ✅ Expiration checking (various scenarios)
- ✅ Simulated token refresh
- ✅ Automatic refresh before expiration
- ✅ Integration with account binding
- ✅ Error handling (no refresh token, etc.)

## Platform-Specific Details

### Instagram

**Required Scopes:**
- `instagram_basic` - Basic profile info
- `instagram_content_publish` - Post content
- `pages_read_engagement` - Read engagement metrics

**Token Lifetime:**
- Access tokens: 60 days (long-lived)
- Refresh: Exchange short-lived for long-lived

**Refresh Endpoint (TODO):**
```
POST https://graph.instagram.com/refresh_access_token
Params:
  - grant_type: ig_refresh_token
  - access_token: <current_token>
```

### TikTok

**Required Scopes:**
- `user.info.basic` - User profile
- `video.upload` - Upload videos
- `video.publish` - Publish posts

**Token Lifetime:**
- Access tokens: 24 hours
- Refresh tokens: Can be used once

**Refresh Endpoint (TODO):**
```
POST https://open-api.tiktok.com/oauth/refresh_token/
JSON:
  - client_key: <app_key>
  - grant_type: refresh_token
  - refresh_token: <token>
```

### YouTube

**Required Scopes:**
- `https://www.googleapis.com/auth/youtube.upload` - Upload videos
- `https://www.googleapis.com/auth/youtube` - Manage channel

**Token Lifetime:**
- Access tokens: 1 hour
- Refresh tokens: Never expire (unless revoked)

**Refresh Endpoint (TODO):**
```
POST https://oauth2.googleapis.com/token
Data:
  - client_id: <id>
  - client_secret: <secret>
  - refresh_token: <token>
  - grant_type: refresh_token
```

## Future Implementation (PASO 5.5+)

### OAuth Authorization Flow

1. **Initiate Authorization**
   - Redirect user to platform OAuth page
   - Request required scopes
   - Include callback URL

2. **Handle Callback**
   - Receive authorization code
   - Exchange code for access + refresh tokens
   - Store tokens in SocialAccountModel

3. **Token Management**
   - Replace simulated refresh with real API calls
   - Add retry logic with exponential backoff
   - Handle rate limiting
   - Log refresh attempts to ledger

### Implementation Checklist

- [ ] Add OAuth redirect endpoints to FastAPI router
- [ ] Implement authorization initiation
- [ ] Implement callback handler
- [ ] Add real Instagram token refresh
- [ ] Add real TikTok token refresh
- [ ] Add real YouTube token refresh
- [ ] Add token revocation handling
- [ ] Add OAuth error handling
- [ ] Add rate limiting
- [ ] Add ledger integration for OAuth events
- [ ] Add user-facing OAuth status UI

## Configuration

Add to `.env` or environment variables:

```bash
# Instagram (Meta)
INSTAGRAM_CLIENT_ID=your_client_id
INSTAGRAM_CLIENT_SECRET=your_client_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/oauth/instagram/callback

# TikTok
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_REDIRECT_URI=https://yourdomain.com/oauth/tiktok/callback

# YouTube (Google)
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=https://yourdomain.com/oauth/youtube/callback
```

## Security Considerations

1. **Token Storage**
   - OAuth tokens stored in plaintext in `oauth_access_token` field
   - Alternative: Use `encrypted_credentials` field with Fernet encryption
   - Recommendation: Migrate to encrypted storage in production

2. **Refresh Token Security**
   - Refresh tokens are sensitive - protect database access
   - Consider encrypting refresh tokens
   - Rotate tokens regularly

3. **HTTPS Required**
   - OAuth callbacks MUST use HTTPS in production
   - Platform providers reject HTTP callbacks

4. **Token Expiration**
   - Always check expiration before API calls
   - Use `ensure_valid_access_token()` wrapper

## Troubleshooting

### Token Refresh Fails with "no_refresh_token"

**Cause**: Account has `oauth_access_token` but no `oauth_refresh_token`

**Solution**: User needs to re-authorize the app to get a new refresh token

### Token Expires Too Quickly

**Cause**: Different platforms have different token lifetimes

**Solution**: 
- Instagram: Use long-lived tokens (60 days)
- TikTok: Refresh every 24 hours
- YouTube: Refresh every hour

### Integration Test Fails

**Cause**: Database migration not applied

**Solution**:
```bash
cd backend
alembic upgrade head
pytest tests/test_oauth_service.py -v
```

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review TODO comments in `service.py`
3. Consult platform OAuth documentation:
   - [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/overview)
   - [TikTok for Developers](https://developers.tiktok.com/)
   - [YouTube Data API](https://developers.google.com/youtube/v3)

## License

Part of Stakazo publishing system.
```
