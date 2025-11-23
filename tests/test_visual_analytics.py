"""
Tests for Visual Analytics Layer (PASO 8.3).

All tests work with empty database (stub data) to ensure no dependencies.
These tests focus on API structure and response validation, not authentication.
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from tests.test_db import get_test_db, init_test_db


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
async def test_db():
    """
    Create test database with schema.
    """
    await init_test_db()
    async for session in get_test_db():
        yield session


@pytest.fixture
def bypass_auth():
    """
    Bypass authentication for testing.
    Mock the RBAC permission checker to always allow access.
    """
    async def mock_permission(*args, **kwargs):
        """Mock permission checker that always returns success."""
        return None
    
    return patch('app.auth.permissions.require_permission', return_value=mock_permission)


# =====================================================================
# TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_visual_overview_returns_ok(bypass_auth, test_db):
    """
    Test 1: GET /visual/analytics/overview returns valid structure.
    
    Verifies:
    - Endpoint returns 200
    - Response contains all required fields
    - Data types are correct
    - Works with empty database
    """
    with bypass_auth:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/visual/analytics/overview?days_back=30")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "total_clips" in data
    assert "total_jobs" in data
    assert "total_publications" in data
    assert "total_campaigns" in data
    assert "clips_per_day" in data
    assert "clips_per_week" in data
    assert "clips_per_month" in data
    assert "avg_job_duration_ms" in data
    assert "avg_clip_score" in data
    assert "publication_success_rate" in data
    assert "trends" in data
    assert "correlations" in data
    assert "top_videos_by_score" in data
    assert "rule_engine_metrics" in data
    assert "generated_at" in data
    assert "date_range" in data
    
    # Check data types
    assert isinstance(data["total_clips"], int)
    assert isinstance(data["total_jobs"], int)
    assert isinstance(data["clips_per_day"], (int, float))
    assert isinstance(data["avg_clip_score"], (int, float))
    assert isinstance(data["trends"], list)
    assert isinstance(data["correlations"], list)
    assert isinstance(data["top_videos_by_score"], list)
    assert isinstance(data["rule_engine_metrics"], dict)
    
    # Empty database should return zeros
    assert data["total_clips"] >= 0
    assert data["total_jobs"] >= 0
    assert data["avg_clip_score"] >= 0.0


@pytest.mark.asyncio
async def test_heatmap_structure(auth_headers, test_db):
    """
    Test 2: GET /visual/analytics/heatmap returns valid heatmap structure.
    
    Verifies:
    - Endpoint returns 200
    - Heatmap has correct structure
    - Labels are present
    - Cells format is correct
    - Works with empty database
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/visual/analytics/heatmap?metric=clips&days_back=30",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "title" in data
    assert "x_labels" in data
    assert "y_labels" in data
    assert "cells" in data
    assert "color_scale" in data
    
    # Check data types
    assert isinstance(data["title"], str)
    assert isinstance(data["x_labels"], list)
    assert isinstance(data["y_labels"], list)
    assert isinstance(data["cells"], list)
    assert isinstance(data["color_scale"], str)
    
    # Check labels
    assert len(data["x_labels"]) == 24  # 24 hours
    assert len(data["y_labels"]) == 7   # 7 days of week
    
    # Check cells structure (if any)
    if data["cells"]:
        cell = data["cells"][0]
        assert "x" in cell
        assert "y" in cell
        assert "value" in cell
        assert isinstance(cell["value"], (int, float))


@pytest.mark.asyncio
async def test_timeline_valid(auth_headers, test_db):
    """
    Test 3: GET /visual/analytics/timeline returns valid timeline data.
    
    Verifies:
    - Endpoint returns 200
    - Timeline has all required series
    - Timeseries structure is correct
    - Works with empty database
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/visual/analytics/timeline?days_back=7",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "jobs_timeline" in data
    assert "publications_timeline" in data
    assert "clips_timeline" in data
    assert "orchestrator_events" in data
    assert "date_range" in data
    
    # Check data types
    assert isinstance(data["jobs_timeline"], list)
    assert isinstance(data["publications_timeline"], list)
    assert isinstance(data["clips_timeline"], list)
    assert isinstance(data["orchestrator_events"], list)
    assert isinstance(data["date_range"], dict)
    
    # Check date range
    assert "start" in data["date_range"]
    assert "end" in data["date_range"]
    
    # Check timeseries structure (if any data)
    if data["jobs_timeline"]:
        series = data["jobs_timeline"][0]
        assert "series_name" in series
        assert "data" in series
        assert isinstance(series["data"], list)
        
        if series["data"]:
            point = series["data"][0]
            assert "timestamp" in point
            assert "value" in point


@pytest.mark.asyncio
async def test_platform_stats(auth_headers, test_db):
    """
    Test 4: GET /visual/analytics/platforms returns valid platform stats.
    
    Verifies:
    - Endpoint returns 200
    - Platform stats structure is correct
    - Metrics are present
    - Works with empty database
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/visual/analytics/platforms?days_back=30",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "platforms" in data
    assert "total_clips" in data
    assert "total_publications" in data
    assert "best_platform" in data
    
    # Check data types
    assert isinstance(data["platforms"], list)
    assert isinstance(data["total_clips"], int)
    assert isinstance(data["total_publications"], int)
    
    # Check platform structure (if any)
    if data["platforms"]:
        platform = data["platforms"][0]
        assert "platform" in platform
        assert "clips_count" in platform
        assert "publications_count" in platform
        assert "avg_score" in platform
        assert "success_rate" in platform
        assert "total_views" in platform
        
        assert isinstance(platform["clips_count"], int)
        assert isinstance(platform["avg_score"], (int, float))
        assert isinstance(platform["success_rate"], (int, float))
    
    # Empty database should return valid structure
    assert data["total_clips"] >= 0
    assert data["total_publications"] >= 0


@pytest.mark.asyncio
async def test_clips_distribution(auth_headers, test_db):
    """
    Test 5: GET /visual/analytics/clips returns valid distributions.
    
    Verifies:
    - Endpoint returns 200
    - Distribution structure is correct
    - Histograms are present
    - Top clips list is valid
    - Works with empty database
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/visual/analytics/clips?days_back=30",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "by_duration" in data
    assert "by_score" in data
    assert "top_clips" in data
    assert "total_clips" in data
    assert "avg_score" in data
    assert "avg_duration" in data
    
    # Check data types
    assert isinstance(data["by_duration"], dict)
    assert isinstance(data["by_score"], dict)
    assert isinstance(data["top_clips"], list)
    assert isinstance(data["total_clips"], int)
    assert isinstance(data["avg_score"], (int, float))
    assert isinstance(data["avg_duration"], (int, float))
    
    # Check distribution structure
    assert "bins" in data["by_duration"]
    assert "counts" in data["by_duration"]
    assert isinstance(data["by_duration"]["bins"], list)
    assert isinstance(data["by_duration"]["counts"], list)
    
    # Check top clips structure (if any)
    if data["top_clips"]:
        clip = data["top_clips"][0]
        assert "clip_id" in clip
        assert "video_id" in clip
        assert "title" in clip
        assert "score" in clip
        assert isinstance(clip["score"], (int, float))
    
    # Empty database should return valid structure
    assert data["total_clips"] >= 0
    assert data["avg_score"] >= 0.0


@pytest.mark.asyncio
async def test_campaign_breakdown(auth_headers, test_db):
    """
    Test 6: GET /visual/analytics/campaigns returns valid campaign breakdown.
    
    Verifies:
    - Endpoint returns 200
    - Campaign breakdown structure is correct
    - Metrics are present
    - Works with empty database
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/visual/analytics/campaigns?days_back=30",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "campaigns" in data
    assert "total_campaigns" in data
    assert "active_campaigns" in data
    assert "avg_clips_per_campaign" in data
    
    # Check data types
    assert isinstance(data["campaigns"], list)
    assert isinstance(data["total_campaigns"], int)
    assert isinstance(data["active_campaigns"], int)
    assert isinstance(data["avg_clips_per_campaign"], (int, float))
    
    # Check campaign structure (if any)
    if data["campaigns"]:
        campaign = data["campaigns"][0]
        assert "campaign_id" in campaign
        assert "name" in campaign
        assert "status" in campaign
        assert "clips_count" in campaign
        assert "publications_count" in campaign
        assert "avg_clip_score" in campaign
        assert "created_at" in campaign
        
        assert isinstance(campaign["clips_count"], int)
        assert isinstance(campaign["publications_count"], int)
    
    # Empty database should return valid structure
    assert data["total_campaigns"] >= 0
    assert data["active_campaigns"] >= 0
    assert data["avg_clips_per_campaign"] >= 0.0


# =====================================================================
# PERMISSION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_analytics_requires_permission(test_db):
    """
    Test that analytics endpoints require analytics:read permission.
    
    Verifies:
    - Endpoints return 403 without proper permission
    - Auth is working correctly
    """
    # Try without auth
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/visual/analytics/overview")
    
    # Should be 401 (unauthorized) or 403 (forbidden)
    assert response.status_code in [401, 403]


# =====================================================================
# QUERY PARAMETER VALIDATION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_days_back_validation(auth_headers, test_db):
    """
    Test that days_back parameter is validated correctly.
    
    Verifies:
    - Invalid days_back values are rejected
    - Valid values are accepted
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test valid value
        response = await client.get(
            "/visual/analytics/overview?days_back=30",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test invalid value (too large)
        response = await client.get(
            "/visual/analytics/overview?days_back=1000",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_heatmap_metric_validation(auth_headers, test_db):
    """
    Test that heatmap metric parameter is validated.
    
    Verifies:
    - Valid metrics are accepted
    - Invalid metrics are rejected
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test valid metrics
        for metric in ["clips", "jobs", "publications"]:
            response = await client.get(
                f"/visual/analytics/heatmap?metric={metric}",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test invalid metric
        response = await client.get(
            "/visual/analytics/heatmap?metric=invalid",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
