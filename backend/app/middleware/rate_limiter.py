"""
Rate Limiting Middleware (STUB Mode)

Phase 1: In-memory rate limiting simulation
Phase 2: Redis-backed distributed rate limiting
"""
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging
from pathlib import Path

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration loader"""
    
    @staticmethod
    def load() -> Dict:
        """Load rate limits from config/options.json"""
        config_path = Path(__file__).parent.parent.parent / "config" / "options.json"
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {
                "rate_limits": {
                    "/upload": {"requests_per_minute": 10, "per": "user"},
                    "/jobs": {"requests_per_minute": 20, "per": "user"},
                    "/campaigns": {"requests_per_minute": 5, "per": "account"},
                }
            }
        
        with open(config_path, 'r') as f:
            return json.load(f)


class RateLimiter:
    """
    Rate limiter with sliding window algorithm (STUB mode)
    
    Phase 1: In-memory storage
    Phase 2: Redis-backed for distributed systems
    """
    
    def __init__(self, mode: str = "STUB"):
        self.mode = mode
        self.config = RateLimitConfig.load()
        
        # STUB: In-memory request tracking
        # Structure: {endpoint: {identifier: deque([timestamp, ...])}}
        self.requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        logger.info(f"RateLimiter initialized in {mode} mode")
    
    def _get_endpoint_config(self, path: str) -> Optional[Dict]:
        """Get rate limit config for endpoint"""
        rate_limits = self.config.get("rate_limits", {})
        
        # Exact match first
        if path in rate_limits:
            return rate_limits[path]
        
        # Pattern matching (e.g., /api/meta/*)
        for pattern, config in rate_limits.items():
            if "*" in pattern:
                prefix = pattern.replace("*", "")
                if path.startswith(prefix):
                    return config
        
        return None
    
    def _get_identifier(self, request: Request, scope: str) -> str:
        """
        Get identifier for rate limiting based on scope
        
        Args:
            request: FastAPI request object
            scope: "user", "account", "token", "ip"
        
        Returns:
            Identifier string
        """
        if scope == "user":
            # STUB: Use X-User-ID header or IP
            user_id = request.headers.get("X-User-ID")
            if user_id:
                return f"user:{user_id}"
            return f"ip:{request.client.host}"
        
        elif scope == "account":
            # STUB: Use X-Account-ID header or IP
            account_id = request.headers.get("X-Account-ID")
            if account_id:
                return f"account:{account_id}"
            return f"ip:{request.client.host}"
        
        elif scope == "token":
            # STUB: Use Authorization header or IP
            auth = request.headers.get("Authorization")
            if auth:
                return f"token:{auth[:20]}"
            return f"ip:{request.client.host}"
        
        else:  # Default to IP
            return f"ip:{request.client.host}"
    
    def _cleanup_old_requests(self, request_queue: deque, window_seconds: int):
        """Remove requests older than window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        while request_queue and request_queue[0] < cutoff:
            request_queue.popleft()
    
    def check_rate_limit(
        self,
        request: Request,
        endpoint: str,
        limit: int,
        window_seconds: int,
        scope: str,
        burst: Optional[int] = None
    ) -> tuple[bool, Dict]:
        """
        Check if request is within rate limit
        
        Args:
            request: FastAPI request
            endpoint: Endpoint path
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            scope: Rate limit scope (user, account, token, ip)
            burst: Optional burst limit (allows temporary spikes)
        
        Returns:
            Tuple of (allowed: bool, metadata: dict)
        """
        identifier = self._get_identifier(request, scope)
        request_queue = self.requests[endpoint][identifier]
        
        # Cleanup old requests
        self._cleanup_old_requests(request_queue, window_seconds)
        
        # Check limits
        current_count = len(request_queue)
        effective_limit = burst if burst and current_count < burst else limit
        
        allowed = current_count < effective_limit
        
        if allowed:
            # Add current request
            request_queue.append(datetime.utcnow())
        
        # Calculate reset time
        if request_queue:
            oldest_request = request_queue[0]
            reset_at = oldest_request + timedelta(seconds=window_seconds)
            remaining = max(0, effective_limit - current_count - (0 if allowed else 1))
        else:
            reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)
            remaining = effective_limit - 1
        
        metadata = {
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at.isoformat(),
            "reset_in_seconds": (reset_at - datetime.utcnow()).total_seconds(),
            "window_seconds": window_seconds,
            "identifier": identifier,
            "current_count": current_count,
            "burst_limit": burst,
        }
        
        return allowed, metadata
    
    async def __call__(self, request: Request, call_next: Callable):
        """Middleware function for FastAPI"""
        
        # Get endpoint config
        endpoint_config = self._get_endpoint_config(request.url.path)
        
        # Skip if no rate limit configured or disabled
        if not endpoint_config or not endpoint_config.get("enabled", True):
            return await call_next(request)
        
        # Extract config
        limit = endpoint_config.get("requests_per_minute", 60)
        scope = endpoint_config.get("per", "ip")
        burst = endpoint_config.get("burst")
        window_seconds = 60  # 1 minute window
        
        # Check rate limit
        allowed, metadata = self.check_rate_limit(
            request,
            request.url.path,
            limit,
            window_seconds,
            scope,
            burst
        )
        
        # Add rate limit headers to response
        headers = {
            "X-RateLimit-Limit": str(metadata["limit"]),
            "X-RateLimit-Remaining": str(metadata["remaining"]),
            "X-RateLimit-Reset": str(int(metadata["reset_in_seconds"])),
        }
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"[RATE_LIMIT] Blocked request from {metadata['identifier']} "
                f"to {request.url.path} (limit: {limit}/min)"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again in {int(metadata['reset_in_seconds'])} seconds.",
                    "limit": metadata["limit"],
                    "remaining": metadata["remaining"],
                    "reset_in_seconds": int(metadata["reset_in_seconds"]),
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Global instance
rate_limiter = RateLimiter(mode="STUB")
