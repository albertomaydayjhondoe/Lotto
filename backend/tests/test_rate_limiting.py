"""
Tests for Rate Limiting Middleware

Phase 1: STUB mode tests
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.middleware.rate_limiter import (
    RateLimiter,
    RateLimitConfig
)


@pytest.fixture
def rate_limiter():
    """Create rate limiter instance with manual config"""
    limiter = RateLimiter(mode="STUB")
    # Override config after initialization (since file might not exist in test environment)
    limiter.config["rate_limits"] = {
        "/upload": {"requests_per_minute": 10, "per": "user", "burst": 15},
        "/jobs": {"requests_per_minute": 20, "per": "user", "burst": 30},
        "/campaigns": {"requests_per_minute": 5, "per": "account", "burst": 10},
        "/api/meta/*": {"requests_per_minute": 100, "per": "token", "burst": 150}
    }
    return limiter


@pytest.fixture
def mock_request():
    """Create mock FastAPI request"""
    request = Mock()
    request.url.path = "/upload"
    request.client.host = "127.0.0.1"
    request.headers.get = Mock(return_value=None)
    return request


def test_rate_limiter_initialization(rate_limiter):
    """Test rate limiter initializes correctly"""
    assert rate_limiter.mode == "STUB"
    assert rate_limiter.config is not None


def test_get_endpoint_config(rate_limiter):
    """Test getting endpoint config"""
    # Exact match
    config = rate_limiter._get_endpoint_config("/upload")
    assert config is not None
    assert "requests_per_minute" in config
    
    # Pattern match
    config = rate_limiter._get_endpoint_config("/api/meta/campaigns")
    assert config is not None
    
    # No match
    config = rate_limiter._get_endpoint_config("/nonexistent")
    assert config is None


def test_get_identifier_by_scope(rate_limiter, mock_request):
    """Test identifier extraction by scope"""
    # User scope with header
    mock_request.headers.get = Mock(side_effect=lambda x: "user123" if x == "X-User-ID" else None)
    identifier = rate_limiter._get_identifier(mock_request, "user")
    assert identifier == "user:user123"
    
    # User scope without header (falls back to IP)
    mock_request.headers.get = Mock(return_value=None)
    identifier = rate_limiter._get_identifier(mock_request, "user")
    assert identifier == "ip:127.0.0.1"
    
    # Account scope
    mock_request.headers.get = Mock(side_effect=lambda x: "acc456" if x == "X-Account-ID" else None)
    identifier = rate_limiter._get_identifier(mock_request, "account")
    assert identifier == "account:acc456"
    
    # Token scope
    mock_request.headers.get = Mock(side_effect=lambda x: "Bearer token123" if x == "Authorization" else None)
    identifier = rate_limiter._get_identifier(mock_request, "token")
    assert identifier.startswith("token:")


def test_check_rate_limit_within_limit(rate_limiter, mock_request):
    """Test rate limit check within limits"""
    allowed, metadata = rate_limiter.check_rate_limit(
        request=mock_request,
        endpoint="/test",
        limit=10,
        window_seconds=60,
        scope="ip"
    )
    
    assert allowed is True
    assert metadata["limit"] == 10
    assert metadata["remaining"] >= 0
    assert "reset_at" in metadata


def test_check_rate_limit_exceeded(rate_limiter, mock_request):
    """Test rate limit exceeded"""
    # Make requests up to limit
    for i in range(10):
        allowed, metadata = rate_limiter.check_rate_limit(
            request=mock_request,
            endpoint="/test",
            limit=10,
            window_seconds=60,
            scope="ip"
        )
        if i < 10:
            assert allowed is True
    
    # Next request should be blocked
    allowed, metadata = rate_limiter.check_rate_limit(
        request=mock_request,
        endpoint="/test",
        limit=10,
        window_seconds=60,
        scope="ip"
    )
    
    assert allowed is False
    assert metadata["remaining"] == 0


def test_rate_limit_with_burst(rate_limiter, mock_request):
    """Test rate limiting with burst allowance"""
    # Regular limit is 5, burst is 10
    # Should allow up to 10 requests
    for i in range(10):
        allowed, metadata = rate_limiter.check_rate_limit(
            request=mock_request,
            endpoint="/burst_test",
            limit=5,
            window_seconds=60,
            scope="ip",
            burst=10
        )
        assert allowed is True
    
    # 11th request should be blocked
    allowed, metadata = rate_limiter.check_rate_limit(
        request=mock_request,
        endpoint="/burst_test",
        limit=5,
        window_seconds=60,
        scope="ip",
        burst=10
    )
    
    assert allowed is False


def test_cleanup_old_requests(rate_limiter):
    """Test cleanup of old requests"""
    from collections import deque
    from datetime import timedelta
    
    request_queue = deque()
    
    # Add old requests
    old_time = datetime.utcnow() - timedelta(seconds=120)
    request_queue.append(old_time)
    request_queue.append(old_time)
    
    # Add recent request
    recent_time = datetime.utcnow()
    request_queue.append(recent_time)
    
    # Cleanup (60 second window)
    rate_limiter._cleanup_old_requests(request_queue, 60)
    
    # Only recent request should remain
    assert len(request_queue) == 1
    assert request_queue[0] == recent_time


@pytest.mark.asyncio
async def test_middleware_allowed_request(rate_limiter, mock_request):
    """Test middleware allows request within limits"""
    # Mock call_next
    mock_response = Mock()
    mock_response.headers = {}
    call_next = AsyncMock(return_value=mock_response)
    
    # Process request
    response = await rate_limiter(mock_request, call_next)
    
    # Should call next middleware
    call_next.assert_called_once()
    
    # Should have rate limit headers
    assert "X-RateLimit-Limit" in response.headers


@pytest.mark.asyncio
async def test_middleware_blocked_request(rate_limiter, mock_request):
    """Test middleware blocks request exceeding limits"""
    # Exhaust rate limit
    for _ in range(15):  # More than upload limit (10)
        call_next = AsyncMock(return_value=Mock(headers={}))
        await rate_limiter(mock_request, call_next)
    
    # Next request should be blocked
    call_next = AsyncMock()
    response = await rate_limiter(mock_request, call_next)
    
    # Should NOT call next middleware
    call_next.assert_not_called()
    
    # Should return 429 error
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_middleware_skips_unconfigured_endpoint(rate_limiter):
    """Test middleware skips endpoints without rate limit config"""
    mock_request = Mock()
    mock_request.url.path = "/unconfigured"
    mock_request.client.host = "127.0.0.1"
    mock_request.headers.get = Mock(return_value=None)
    
    mock_response = Mock()
    call_next = AsyncMock(return_value=mock_response)
    
    response = await rate_limiter(mock_request, call_next)
    
    # Should call next middleware (no rate limiting)
    call_next.assert_called_once()
    assert response == mock_response


def test_rate_limit_config_load():
    """Test loading rate limit config from file"""
    config = RateLimitConfig.load()
    
    assert "rate_limits" in config or "MODE" in config
    # Config should either load from file or use defaults
