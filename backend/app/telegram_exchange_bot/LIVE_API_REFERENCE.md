# LIVE API REFERENCE
**Sprint 7C — YouTube, Instagram, TikTok Live APIs**

---

## 📖 TABLE OF CONTENTS

1. [YouTube Live API](#youtube-live-api)
2. [Instagram Live API](#instagram-live-api)
3. [TikTok Live API](#tiktok-live-api)
4. [Common Patterns](#common-patterns)
5. [Error Handling](#error-handling)
6. [Security Requirements](#security-requirements)

---

## 🎬 YOUTUBE LIVE API

### Module: `platforms/youtube_live.py`

### Features
- ✅ yt-dlp metadata extraction
- ✅ URL validation (multiple formats)
- ✅ Like/Comment/Subscribe execution
- ✅ Interaction verification
- ✅ Safe delays (15-60s)

### YouTubeVideoMetadata

```python
@dataclass
class YouTubeVideoMetadata:
    video_id: str
    title: str
    channel: str
    views: int
    likes: int
    comments: int
    duration: int  # seconds
    tags: List[str]
    upload_date: str
```

### YouTubeLiveAPI

#### Constructor

```python
api = YouTubeLiveAPI()
```

No parameters required. yt-dlp configuration is automatic.

#### extract_video_id()

```python
video_id = api.extract_video_id(url: str) -> Optional[str]
```

**Supported URL formats**:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`

**Example**:
```python
video_id = api.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
# Returns: "dQw4w9WgXcQ"
```

#### get_video_metadata()

```python
metadata = await api.get_video_metadata(
    video_url: str,
    security_context: SecurityContext
) -> Optional[YouTubeVideoMetadata]
```

**Parameters**:
- `video_url`: YouTube video URL
- `security_context`: SecurityContext with VPN+Proxy+Fingerprint

**Returns**: YouTubeVideoMetadata or None on error

**Example**:
```python
metadata = await api.get_video_metadata(
    "https://youtube.com/watch?v=test123",
    security_context
)

print(f"Title: {metadata.title}")
print(f"Views: {metadata.views:,}")
print(f"Duration: {metadata.duration}s")
```

#### execute_like()

```python
result = await api.execute_like(
    video_url: str,
    username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 15-45 seconds

**Returns**:
```python
{
    "success": True,
    "interaction_type": "youtube_like",
    "video_id": "test123",
    "mode": "simulation",  # or "live" when selenium implemented
    "timestamp": "2024-01-01T12:00:00"
}
```

**Example**:
```python
result = await api.execute_like(
    video_url="https://youtube.com/watch?v=test",
    username="user123",
    security_context=security_context
)

if result["success"]:
    print(f"Like executed: {result['video_id']}")
```

#### execute_comment()

```python
result = await api.execute_comment(
    video_url: str,
    comment_text: str,
    username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 25-60 seconds

**Example**:
```python
result = await api.execute_comment(
    video_url="https://youtube.com/watch?v=test",
    comment_text="Great video!",
    username="user123",
    security_context=security_context
)
```

#### execute_subscribe()

```python
result = await api.execute_subscribe(
    video_url: str,
    username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 20-50 seconds

#### verify_interaction_received()

```python
verified = await api.verify_interaction_received(
    video_url: str,
    interaction_type: str,  # "like" | "comment" | "subscribe"
    expected_change: int = 1,
    security_context: SecurityContext
) -> bool
```

**Wait Time**: 5 seconds before re-checking

**Example**:
```python
# Execute like
await api.execute_like(video_url, username, security_context)

# Verify
verified = await api.verify_interaction_received(
    video_url,
    interaction_type="like",
    security_context=security_context
)

if verified:
    print("Like confirmed!")
```

#### get_stats()

```python
stats = api.get_stats()
```

**Returns**:
```python
{
    "metadata_fetched": 10,
    "likes_executed": 5,
    "comments_executed": 3,
    "subscribes_executed": 2,
    "errors": 0
}
```

---

## 📸 INSTAGRAM LIVE API

### Module: `platforms/instagram_live.py`

### Features
- ✅ instagrapi integration
- ✅ Session management per account
- ✅ Challenge handling
- ✅ Like/Save/Comment/Follow execution
- ✅ Safe delays (15-70s)

### InstagramPostMetadata

```python
@dataclass
class InstagramPostMetadata:
    post_id: str
    shortcode: str
    caption: str
    likes: int
    comments: int
    user: str
    media_type: str  # "Photo" | "Video" | "Carousel"
```

### InstagramLiveAPI

#### Constructor

```python
api = InstagramLiveAPI()
```

Internal session dictionary initialized: `{}`

#### login()

```python
success = await api.login(
    account_id: str,
    username: str,
    password: str,
    security_context: SecurityContext
) -> bool
```

**Challenge Handling**:
- `ChallengeRequired`: Auto-resolves challenge
- `SelectContactPointRecoveryForm`: Requires manual intervention
- `RecaptchaChallengeForm`: Requires manual CAPTCHA solving

**Example**:
```python
success = await api.login(
    account_id="acc_001",
    username="my_username",
    password="my_password",
    security_context=security_context
)

if success:
    print("Login successful!")
else:
    print("Login failed (check credentials or challenges)")
```

#### get_post_metadata()

```python
metadata = await api.get_post_metadata(
    post_url: str,
    account_id: str
) -> Optional[InstagramPostMetadata]
```

**Requires**: Active session (call `login()` first)

**Example**:
```python
await api.login(account_id, username, password, security_context)

metadata = await api.get_post_metadata(
    post_url="https://instagram.com/p/test123",
    account_id=account_id
)

print(f"Caption: {metadata.caption}")
print(f"Likes: {metadata.likes:,}")
```

#### execute_like()

```python
result = await api.execute_like(
    post_url: str,
    account_id: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 20-50 seconds

**Requires**: Active session

**Example**:
```python
result = await api.execute_like(
    post_url="https://instagram.com/p/test",
    account_id="acc_001",
    security_context=security_context
)
```

#### execute_save()

```python
result = await api.execute_save(
    post_url: str,
    account_id: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 15-40 seconds

#### execute_comment()

```python
result = await api.execute_comment(
    post_url: str,
    comment_text: str,
    account_id: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 30-70 seconds

**Example**:
```python
result = await api.execute_comment(
    post_url="https://instagram.com/p/test",
    comment_text="Amazing shot! 📸",
    account_id="acc_001",
    security_context=security_context
)
```

#### execute_follow()

```python
result = await api.execute_follow(
    username: str,
    account_id: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 25-60 seconds

#### logout()

```python
await api.logout(account_id: str)
```

**Example**:
```python
# After work is done
await api.logout("acc_001")
```

#### get_stats()

```python
stats = api.get_stats()
```

**Returns**:
```python
{
    "sessions_created": 5,
    "likes_executed": 20,
    "saves_executed": 10,
    "comments_executed": 8,
    "follows_executed": 3,
    "challenges_handled": 2,
    "errors": 1
}
```

---

## 🎵 TIKTOK LIVE API

### Module: `platforms/tiktok_live.py`

### Features
- ✅ Unofficial API + webdriver fallback
- ✅ Circuit breaker pattern
- ✅ Shadowban detection
- ✅ IP rotation per action
- ✅ Safe delays (25-70s)

### TikTokVideoMetadata

```python
@dataclass
class TikTokVideoMetadata:
    video_id: str
    description: str
    author: str
    views: int
    likes: int
    comments: int
    shares: int
    duration: int
    music: str
```

### TikTokLiveAPI

#### Constructor

```python
api = TikTokLiveAPI()
```

**Circuit Breaker**: Initialized with shadowban_signals:
```python
{
    "rate_limit": 0,
    "failed_requests": 0,
    "captcha_count": 0
}
```

#### extract_video_id()

```python
video_id = api.extract_video_id(url: str) -> Optional[str]
```

**Supported URL formats**:
- `https://www.tiktok.com/@username/video/VIDEO_ID`
- `https://vm.tiktok.com/SHORT_CODE` (follows redirect)

**Example**:
```python
video_id = api.extract_video_id(
    "https://tiktok.com/@user123/video/7234567890123456789"
)
# Returns: "7234567890123456789"
```

#### get_video_metadata()

```python
metadata = await api.get_video_metadata(
    video_url: str,
    security_context: SecurityContext
) -> Optional[TikTokVideoMetadata]
```

**Example**:
```python
metadata = await api.get_video_metadata(
    "https://tiktok.com/@user/video/123456",
    security_context
)

print(f"Description: {metadata.description}")
print(f"Views: {metadata.views:,}")
print(f"Music: {metadata.music}")
```

#### execute_like()

```python
result = await api.execute_like(
    video_url: str,
    username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 25-50 seconds

**Circuit Breaker Check**: Returns error if shadowbanned

**Example**:
```python
if not api._is_shadowbanned():
    result = await api.execute_like(
        video_url="https://tiktok.com/@user/video/123",
        username="user123",
        security_context=security_context
    )
else:
    print("Circuit breaker active (shadowban detected)")
```

#### execute_comment()

```python
result = await api.execute_comment(
    video_url: str,
    comment_text: str,
    username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 35-70 seconds (longest for TikTok sensitivity)

#### execute_follow()

```python
result = await api.execute_follow(
    username: str,
    follower_username: str,
    security_context: SecurityContext
) -> Dict[str, any]
```

**Safe Delay**: 30-60 seconds

#### verify_interaction_received()

```python
verified = await api.verify_interaction_received(
    video_url: str,
    interaction_type: str,
    expected_change: int = 1,
    security_context: SecurityContext
) -> bool
```

**Wait Time**: 8 seconds (TikTok servers need more time)

#### _is_shadowbanned()

```python
is_banned = api._is_shadowbanned() -> bool
```

**Triggers**:
- `failed_requests >= 5`
- `captcha_count >= 3`
- `rate_limit > 0`

**Example**:
```python
if api._is_shadowbanned():
    print("Account is shadowbanned!")
    print(f"Signals: {api.shadowban_signals}")
```

#### reset_circuit_breaker()

```python
api.reset_circuit_breaker()
```

**Use**: Manual reset after fixing shadowban (change IP, wait, etc.)

**Example**:
```python
# After waiting 24h and changing proxy
api.reset_circuit_breaker()
print("Circuit breaker reset, account active again")
```

#### get_stats()

```python
stats = api.get_stats()
```

**Returns**:
```python
{
    "metadata_fetched": 15,
    "likes_executed": 8,
    "comments_executed": 4,
    "follows_executed": 3,
    "shadowban_detected": 0,
    "errors": 1
}
```

---

## 🔄 COMMON PATTERNS

### Pattern 1: Safe Execution with Delays

```python
# All platforms use randomized delays
import random

delay = random.uniform(min_seconds, max_seconds)
await asyncio.sleep(delay)
```

**Why**: Prevents pattern detection by platform algorithms

### Pattern 2: Security Context Validation

```python
# All execute_*() methods validate security
if not security_context.vpn_active:
    return {"success": False, "error": "VPN required"}

if not security_context.rate_limit_respected:
    return {"success": False, "error": "Rate limit exceeded"}
```

### Pattern 3: Stats Tracking

```python
# All platforms track stats
self.stats["likes_executed"] += 1
```

**Use**: Dashboard integration, performance monitoring

### Pattern 4: Graceful Degradation

```python
# Instagram: fallback if instagrapi unavailable
if not INSTAGRAPI_AVAILABLE:
    return {"success": False, "error": "instagrapi not installed"}
```

---

## ⚠️ ERROR HANDLING

### Common Errors

#### Network Errors
```python
try:
    metadata = await api.get_video_metadata(url, security_context)
except Exception as e:
    if "timeout" in str(e).lower():
        # Retry with longer timeout
    elif "connection" in str(e).lower():
        # Check proxy/VPN
```

#### Authentication Errors
```python
# Instagram login
success = await api.login(account_id, username, password, security_context)
if not success:
    # Check credentials, handle challenge, or use different account
```

#### Rate Limit Errors
```python
# TikTok circuit breaker
if api._is_shadowbanned():
    # Wait 24h, change IP, reset circuit breaker
    await asyncio.sleep(86400)
    api.reset_circuit_breaker()
```

#### Circuit Breaker Triggered
```python
# TikTok
result = await api.execute_like(url, username, security_context)
if not result["success"] and "circuit breaker" in result["error"]:
    # Account is shadowbanned
    # Apply cooldown from accounts_pool
```

---

## 🔒 SECURITY REQUIREMENTS

### Mandatory for All Platforms

1. **VPN Active**: `security_context.vpn_active = True`
2. **Proxy Valid**: `security_context.proxy` must be functional
3. **Fingerprint Unique**: `security_context.fingerprint` per account
4. **Rate Limits Respected**: `security_context.rate_limit_respected = True`

### IP Rotation

```python
# TikTok: Check IP rotation before execution
if security_context.proxy.host != last_proxy_host:
    # IP rotated, safe to proceed
else:
    # Rotate proxy first
    security_context = await security_layer.prepare_security_context(
        account_id=account_id,
        target_url=video_url,
        interaction_type="tiktok_like"
    )
```

### Delay Ranges by Platform

| Platform  | Like     | Comment  | Follow   | Subscribe |
|-----------|----------|----------|----------|-----------|
| YouTube   | 15-45s   | 25-60s   | -        | 20-50s    |
| Instagram | 20-50s   | 30-70s   | 25-60s   | -         |
| TikTok    | 25-50s   | 35-70s   | 30-60s   | -         |

**TikTok**: Longest delays due to high sensitivity

---

## 📊 INTEGRATION WITH SPRINT 7B

### Executor Integration

```python
# executor.py
from app.telegram_exchange_bot.platforms import (
    YouTubeLiveAPI,
    InstagramLiveAPI,
    TikTokLiveAPI
)

class InteractionExecutor:
    def __init__(self):
        self.yt_api = YouTubeLiveAPI()
        self.ig_api = InstagramLiveAPI()
        self.tt_api = TikTokLiveAPI()
    
    async def execute_interaction(self, interaction: Interaction):
        if interaction.platform == Platform.YOUTUBE:
            result = await self.yt_api.execute_like(
                video_url=interaction.target_url,
                username=interaction.account.username,
                security_context=interaction.security_context
            )
        # ... similar for Instagram/TikTok
```

### Metrics Integration

```python
# metrics.py
from app.telegram_exchange_bot.platforms import YouTubeLiveAPI

yt_api = YouTubeLiveAPI()
stats = yt_api.get_stats()

# Feed to MetricsCollector
metrics_collector.record_platform_stats(
    platform=Platform.YOUTUBE,
    stats=stats
)
```

---

## 🚀 QUICK START

### YouTube Example

```python
from app.telegram_exchange_bot.platforms import YouTubeLiveAPI
from app.telegram_exchange_bot.security import TelegramBotSecurityLayer

# Initialize
api = YouTubeLiveAPI()
security_layer = TelegramBotSecurityLayer(db)

# Prepare security
security_context = await security_layer.prepare_security_context(
    account_id="acc_001",
    target_url="https://youtube.com/watch?v=test",
    interaction_type="youtube_like"
)

# Get metadata
metadata = await api.get_video_metadata(
    "https://youtube.com/watch?v=test",
    security_context
)

# Execute like
result = await api.execute_like(
    "https://youtube.com/watch?v=test",
    username="user123",
    security_context=security_context
)

# Check stats
print(api.get_stats())
```

### Instagram Example

```python
from app.telegram_exchange_bot.platforms import InstagramLiveAPI

# Initialize
api = InstagramLiveAPI()

# Login
await api.login(
    account_id="acc_001",
    username="my_username",
    password="my_password",
    security_context=security_context
)

# Execute like
result = await api.execute_like(
    post_url="https://instagram.com/p/test",
    account_id="acc_001",
    security_context=security_context
)

# Logout
await api.logout("acc_001")
```

### TikTok Example

```python
from app.telegram_exchange_bot.platforms import TikTokLiveAPI

# Initialize
api = TikTokLiveAPI()

# Check circuit breaker
if api._is_shadowbanned():
    print("Account is shadowbanned, cannot execute")
else:
    # Execute like
    result = await api.execute_like(
        video_url="https://tiktok.com/@user/video/123",
        username="user123",
        security_context=security_context
    )
```

---

## 📚 NEXT STEPS

1. **Implement Selenium**: For YouTube/TikTok real execution (currently simulated)
2. **Cookie Injection**: For authenticated actions
3. **Headless Browser**: For production deployments
4. **Proxy Pool**: Rotate IPs automatically
5. **CAPTCHA Solver**: For Instagram challenges

---

**Document Version**: 1.0  
**Last Updated**: 2024 (Sprint 7C)  
**Maintainer**: Telegram Exchange Bot Team
