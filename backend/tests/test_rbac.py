"""
Tests for RBAC (Role-Based Access Control) protection on API endpoints.

Tests verify that:
- Admin can access all endpoints
- Manager can publish and manage campaigns/rules
- Operator can manage jobs/clips but NOT publish
- Viewer can only read dashboard data
- Webhooks are NOT protected (use signature validation instead)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt import create_access_token
from app.auth.permissions import get_scopes_for_role


@pytest.fixture
def admin_token():
    """Create access token for admin user."""
    return create_access_token(
        user_id="admin-test-id",
        email="admin@test.com",
        role="admin",
        scopes=get_scopes_for_role("admin")
    )


@pytest.fixture
def manager_token():
    """Create access token for manager user."""
    return create_access_token(
        user_id="manager-test-id",
        email="manager@test.com",
        role="manager",
        scopes=get_scopes_for_role("manager")
    )


@pytest.fixture
def operator_token():
    """Create access token for operator user."""
    return create_access_token(
        user_id="operator-test-id",
        email="operator@test.com",
        role="operator",
        scopes=get_scopes_for_role("operator")
    )


@pytest.fixture
def viewer_token():
    """Create access token for viewer user."""
    return create_access_token(
        user_id="viewer-test-id",
        email="viewer@test.com",
        role="viewer",
        scopes=get_scopes_for_role("viewer")
    )


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_admin_access_all(client, admin_token):
    """
    Test that admin can access all protected endpoints.
    
    Admin should have access to:
    - Debug endpoints
    - Dashboard endpoints
    - Publishing endpoints
    - Orchestrator endpoints
    - All CRUD operations
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Debug endpoints (admin only)
    response = client.get("/jobs/summary", headers=headers)
    assert response.status_code != 403, "Admin should access /jobs/summary"
    
    response = client.get("/clips/summary", headers=headers)
    assert response.status_code != 403, "Admin should access /clips/summary"
    
    response = client.get("/health", headers=headers)
    assert response.status_code != 403, "Admin should access /health"
    
    # Dashboard endpoints (all roles)
    response = client.get("/dashboard/stats/overview", headers=headers)
    assert response.status_code != 403, "Admin should access /dashboard/stats/overview"
    
    # Orchestrator endpoints (admin/manager)
    response = client.get("/orchestrator/status", headers=headers)
    assert response.status_code != 403, "Admin should access /orchestrator/status"
    
    # Jobs endpoints (operator/manager/admin)
    response = client.get("/jobs", headers=headers)
    assert response.status_code != 403, "Admin should access /jobs"
    
    # Campaigns endpoints (manager/admin)
    response = client.get("/campaigns", headers=headers)
    assert response.status_code != 403, "Admin should access /campaigns"
    
    # Rules endpoints (manager/admin)
    response = client.get("/rules", headers=headers)
    assert response.status_code != 403, "Admin should access /rules"


def test_viewer_forbidden_write(client, viewer_token):
    """
    Test that viewer CANNOT perform write operations.
    
    Viewer should:
    - Be able to read dashboard data
    - NOT be able to create/update/delete resources
    - NOT access jobs, clips, campaigns, or publishing endpoints
    """
    headers = {"Authorization": f"Bearer {viewer_token}"}
    
    # Dashboard read should work
    response = client.get("/dashboard/stats/overview", headers=headers)
    assert response.status_code != 403, "Viewer should read dashboard"
    
    # Jobs should be forbidden
    response = client.get("/jobs", headers=headers)
    assert response.status_code == 403, "Viewer should NOT access /jobs"
    
    # Clips should be forbidden
    response = client.get("/clips", headers=headers)
    assert response.status_code == 403, "Viewer should NOT access /clips"
    
    # Campaigns should be forbidden
    response = client.get("/campaigns", headers=headers)
    assert response.status_code == 403, "Viewer should NOT access /campaigns"
    
    # Publishing should be forbidden
    response = client.post("/publishing/publish", headers=headers, json={
        "clip_id": "test-clip-id",
        "platform": "instagram"
    })
    assert response.status_code == 403, "Viewer should NOT publish"
    
    # Upload should be forbidden
    response = client.post("/upload", headers=headers)
    assert response.status_code == 403, "Viewer should NOT upload"


def test_operator_can_edit_clips(client, operator_token):
    """
    Test that operator CAN manage jobs and clips.
    
    Operator should:
    - Access and modify jobs
    - Access and modify clips
    - Read publishing logs
    - Read dashboard data
    - NOT publish or schedule
    - NOT manage campaigns or rules
    """
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Jobs should work
    response = client.get("/jobs", headers=headers)
    assert response.status_code != 403, "Operator should access /jobs"
    
    # Clips should work
    response = client.get("/clips", headers=headers)
    assert response.status_code != 403, "Operator should access /clips"
    
    # Dashboard should work
    response = client.get("/dashboard/stats/overview", headers=headers)
    assert response.status_code != 403, "Operator should read dashboard"
    
    # Publishing logs should work (read-only)
    # Note: Will fail with 404/422 if clip doesn't exist, but NOT 403
    response = client.get("/publishing/logs/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code != 403, "Operator should read publishing logs"
    
    # Publishing should be FORBIDDEN
    response = client.post("/publishing/publish", headers=headers, json={
        "clip_id": "test-clip-id",
        "platform": "instagram"
    })
    assert response.status_code == 403, "Operator should NOT publish"
    
    # Campaigns should be FORBIDDEN
    response = client.get("/campaigns", headers=headers)
    assert response.status_code == 403, "Operator should NOT access campaigns"
    
    # Rules should be FORBIDDEN
    response = client.get("/rules", headers=headers)
    assert response.status_code == 403, "Operator should NOT access rules"


def test_manager_can_publish(client, manager_token):
    """
    Test that manager CAN publish and manage campaigns.
    
    Manager should:
    - Publish clips
    - Schedule publications
    - Manage campaigns
    - Manage rules
    - Access jobs and clips
    - Upload videos
    - NOT access debug endpoints
    - NOT access system-critical endpoints (like train rules engine)
    """
    headers = {"Authorization": f"Bearer {manager_token}"}
    
    # Publishing should work
    response = client.post("/publishing/publish", headers=headers, json={
        "clip_id": "00000000-0000-0000-0000-000000000000",
        "platform": "instagram"
    })
    # Will fail with 404 (clip not found) but NOT 403 (forbidden)
    assert response.status_code != 403, "Manager should be able to publish"
    
    # Campaigns should work
    response = client.get("/campaigns", headers=headers)
    assert response.status_code != 403, "Manager should access campaigns"
    
    # Rules should work
    response = client.get("/rules", headers=headers)
    assert response.status_code != 403, "Manager should access rules"
    
    # Jobs should work
    response = client.get("/jobs", headers=headers)
    assert response.status_code != 403, "Manager should access jobs"
    
    # Clips should work
    response = client.get("/clips", headers=headers)
    assert response.status_code != 403, "Manager should access clips"
    
    # Dashboard should work
    response = client.get("/dashboard/stats/overview", headers=headers)
    assert response.status_code != 403, "Manager should read dashboard"
    
    # Debug endpoints should be FORBIDDEN
    response = client.get("/jobs/summary", headers=headers)
    assert response.status_code == 403, "Manager should NOT access debug endpoints"
    
    # Train rule engine should be FORBIDDEN (admin only)
    response = client.post("/rules/engine/train", headers=headers, json={
        "platform": "instagram"
    })
    assert response.status_code == 403, "Manager should NOT train rules"


def test_webhooks_not_protected(client):
    """
    Test that webhooks are NOT protected by authentication.
    
    Webhooks should:
    - NOT require JWT authentication
    - Use signature validation instead (not tested here)
    - Accept requests without Authorization header
    """
    # Instagram webhook (no auth header)
    response = client.post("/webhook/instagram", json={
        "object": "instagram",
        "entry": []
    })
    # Will return 200 or 422 (validation error) but NOT 401/403
    assert response.status_code not in [401, 403], "Instagram webhook should NOT require auth"
    
    # Publishing webhooks (different prefix)
    response = client.post("/publishing/webhooks/instagram", json={
        "object": "instagram",
        "entry": []
    })
    assert response.status_code not in [401, 403], "Publishing webhook should NOT require auth"
    
    response = client.post("/publishing/webhooks/tiktok", json={
        "event": "video.publish",
        "data": {}
    })
    assert response.status_code not in [401, 403], "TikTok webhook should NOT require auth"
    
    response = client.post("/publishing/webhooks/youtube", json={
        "topic": "https://www.youtube.com/xml/feeds/videos.xml",
        "feed": {}
    })
    assert response.status_code not in [401, 403], "YouTube webhook should NOT require auth"


def test_no_token_forbidden(client):
    """
    Test that protected endpoints reject requests without auth token.
    """
    # No Authorization header
    response = client.get("/jobs")
    assert response.status_code == 401, "Should return 401 Unauthorized without token"
    
    response = client.get("/campaigns")
    assert response.status_code == 401, "Should return 401 Unauthorized without token"
    
    response = client.post("/publishing/publish", json={
        "clip_id": "test-id",
        "platform": "instagram"
    })
    assert response.status_code == 401, "Should return 401 Unauthorized without token"


def test_invalid_token_forbidden(client):
    """
    Test that invalid tokens are rejected.
    """
    headers = {"Authorization": "Bearer invalid-token-here"}
    
    response = client.get("/jobs", headers=headers)
    assert response.status_code == 401, "Should return 401 with invalid token"
    
    response = client.get("/campaigns", headers=headers)
    assert response.status_code == 401, "Should return 401 with invalid token"
