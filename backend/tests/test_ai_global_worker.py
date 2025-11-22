"""
Tests for AI Global Worker module (PASO 7.0).

Tests cover:
1. System snapshot collection
2. LLM client stub responses
3. Reasoning engine output structure
4. Runner state management
5. Basic functionality (endpoint tests skipped pending client_with_auth fixture)
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.ai_global_worker.collector import collect_system_snapshot
from app.ai_global_worker.llm_client import LLMClient
from app.ai_global_worker.reasoning import run_full_reasoning
from app.ai_global_worker.runner import (
    start_ai_worker_loop,
    stop_ai_worker_loop,
    get_last_reasoning,
)
from app.ai_global_worker.schemas import (
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan,
    AIReasoningOutput,
)


# ==================== TEST 1: Collector ====================

@pytest.mark.asyncio
async def test_collect_system_snapshot_ok(db_session):
    """
    Test 1: System snapshot collection returns valid SystemSnapshot.
    
    Verifies:
    - Snapshot is SystemSnapshot instance
    - Contains expected fields
    - Timestamp is recent
    """
    snapshot = await collect_system_snapshot(db_session)
    
    assert isinstance(snapshot, SystemSnapshot)
    assert snapshot.timestamp is not None
    assert isinstance(snapshot.queue_pending, int)
    assert isinstance(snapshot.queue_processing, int)
    assert isinstance(snapshot.queue_failed, int)
    assert isinstance(snapshot.queue_success, int)
    assert isinstance(snapshot.scheduler_pending, int)
    assert snapshot.publish_success_rate >= 0.0
    assert snapshot.publish_success_rate <= 100.0
    assert isinstance(snapshot.clips_ready, int)
    assert isinstance(snapshot.jobs_pending, int)
    assert isinstance(snapshot.campaigns_active, int)
    assert isinstance(snapshot.alerts_critical, int)
    assert isinstance(snapshot.alerts_warning, int)
    assert isinstance(snapshot.platform_stats, dict)
    assert isinstance(snapshot.recent_events, list)
    assert isinstance(snapshot.additional_metrics, dict)


# ==================== TEST 2: LLM Client ====================

@pytest.mark.asyncio
async def test_llm_client_generates_stub_data():
    """
    Test 2: LLM client stub generates valid responses.
    
    Verifies:
    - generate_summary returns AISummary
    - generate_recommendations returns list
    - generate_action_plan returns AIActionPlan
    - Health score is in 0-100 range
    """
    # Create mock snapshot
    snapshot = SystemSnapshot(
        timestamp=datetime.utcnow(),
        queue_pending=10,
        queue_processing=2,
        queue_failed=1,
        queue_success=50,
        scheduler_pending=5,
        scheduler_due_soon=2,
        orchestrator_running=True,
        orchestrator_last_run=datetime.utcnow(),
        orchestrator_actions_last_24h=45,
        publish_success_rate=94.2,
        publish_total_24h=45,
        publish_failed_24h=3,
        clips_ready=8,
        clips_pending_analysis=3,
        jobs_pending=2,
        jobs_failed=1,
        campaigns_active=3,
        campaigns_draft=1,
        alerts_critical=0,
        alerts_warning=2,
        platform_stats={},
        best_clips={},
        rule_weights={},
        recent_events=[],
        additional_metrics={},
    )
    
    client = LLMClient()
    
    # Test summary
    summary = await client.generate_summary(snapshot)
    assert isinstance(summary, AISummary)
    assert summary.overall_health in ["excellent", "good", "warning", "critical"]
    assert 0.0 <= summary.health_score <= 100.0
    assert isinstance(summary.key_insights, list)
    assert len(summary.key_insights) >= 1
    assert isinstance(summary.concerns, list)
    assert isinstance(summary.positives, list)
    
    # Test recommendations
    recommendations = await client.generate_recommendations(snapshot)
    assert isinstance(recommendations, list)
    for rec in recommendations:
        assert isinstance(rec, AIRecommendation)
        assert rec.priority in ["critical", "high", "medium", "low"]
        assert rec.effort in ["low", "medium", "high"]
        assert len(rec.title) > 0
        assert len(rec.description) > 0
    
    # Test action plan
    action_plan = await client.generate_action_plan(snapshot)
    assert isinstance(action_plan, AIActionPlan)
    assert len(action_plan.title) > 0
    assert len(action_plan.objective) > 0
    assert isinstance(action_plan.steps, list)
    assert len(action_plan.steps) >= 1
    assert action_plan.risk_level in ["low", "medium", "high"]
    assert isinstance(action_plan.automated, bool)


# ==================== TEST 3: Reasoning Output ====================

@pytest.mark.asyncio
async def test_reasoning_output_structure(db_session):
    """
    Test 3: Reasoning engine returns complete AIReasoningOutput.
    
    Verifies:
    - Output is AIReasoningOutput instance
    - Contains reasoning_id
    - Contains snapshot, summary, recommendations, action_plan
    - Execution time is tracked
    """
    snapshot = await collect_system_snapshot(db_session)
    reasoning_output = await run_full_reasoning(snapshot)
    
    assert isinstance(reasoning_output, AIReasoningOutput)
    assert reasoning_output.reasoning_id is not None
    assert reasoning_output.timestamp is not None
    assert isinstance(reasoning_output.snapshot, SystemSnapshot)
    assert isinstance(reasoning_output.summary, AISummary)
    assert isinstance(reasoning_output.recommendations, list)
    assert isinstance(reasoning_output.action_plan, AIActionPlan)
    assert reasoning_output.execution_time_ms > 0
    
    # Verify recommendations structure
    for rec in reasoning_output.recommendations:
        assert isinstance(rec, AIRecommendation)


# ==================== TEST 4: Runner Initial State ====================

def test_last_run_initially_empty():
    """
    Test 4: Runner has no cached reasoning initially.
    
    Verifies:
    - get_last_reasoning() returns None before any run
    """
    # Stop any existing worker to reset state
    import app.ai_global_worker.runner as runner_module
    runner_module._last_reasoning = None
    
    last_reasoning = get_last_reasoning()
    assert last_reasoning is None


# ==================== TEST 5: Manual Run Creates State ====================

@pytest.mark.asyncio
async def test_manual_run_creates_state(db_session):
    """
    Test 5: Manual reasoning run updates global state.
    
    Verifies:
    - After run_full_reasoning(), state is not None
    - State contains valid AIReasoningOutput
    """
    import app.ai_global_worker.runner as runner_module
    
    # Reset state
    runner_module._last_reasoning = None
    
    # Run reasoning
    snapshot = await collect_system_snapshot(db_session)
    reasoning_output = await run_full_reasoning(snapshot)
    
    # Manually update state (simulating runner loop)
    runner_module._last_reasoning = reasoning_output
    
    # Verify state updated
    last_reasoning = get_last_reasoning()
    assert last_reasoning is not None
    assert isinstance(last_reasoning, AIReasoningOutput)
    assert last_reasoning.reasoning_id == reasoning_output.reasoning_id


# ==================== TEST 6: Action Plan Not Empty ====================

@pytest.mark.asyncio
async def test_action_plan_not_empty(db_session):
    """
    Test 6: Action plan always contains at least one step.
    
    Verifies:
    - AIActionPlan.steps is not empty
    - Each step has required fields
    """
    snapshot = await collect_system_snapshot(db_session)
    reasoning_output = await run_full_reasoning(snapshot)
    
    action_plan = reasoning_output.action_plan
    assert len(action_plan.steps) > 0
    
    for step in action_plan.steps:
        assert "step" in step
        assert "action" in step
        assert "description" in step
        assert isinstance(step["step"], int)
        assert isinstance(step["action"], str)
        assert isinstance(step["description"], str)


# ==================== TEST 7: Recommendations List Not Empty ====================

@pytest.mark.asyncio
async def test_recommendations_list_not_empty(db_session):
    """
    Test 7: Recommendations list contains at least one item.
    
    Verifies:
    - Recommendations list is not empty
    - Each recommendation has required priority and category
    """
    snapshot = await collect_system_snapshot(db_session)
    reasoning_output = await run_full_reasoning(snapshot)
    
    recommendations = reasoning_output.recommendations
    assert len(recommendations) > 0
    
    for rec in recommendations:
        assert rec.priority in ["critical", "high", "medium", "low"]
        assert rec.category in ["performance", "content", "campaigns", "system"]
        assert len(rec.title) > 0


# ==================== TEST 8: Runner Start and Update ====================

@pytest.mark.asyncio
async def test_runner_starts_and_updates_state(db_session):
    """
    Test 8: Runner background loop updates cached state.
    
    Verifies:
    - Worker can be started
    - After short wait, state is populated
    - Worker can be stopped gracefully
    """
    import app.ai_global_worker.runner as runner_module
    
    # Reset state
    runner_module._last_reasoning = None
    runner_module._is_running = False
    
    # Mock db factory
    async def mock_db_factory():
        yield db_session
    
    # Start worker with short interval
    task = await start_ai_worker_loop(mock_db_factory, interval_seconds=1)
    
    try:
        # Wait for at least one cycle (2 seconds to be safe)
        await asyncio.sleep(2.5)
        
        # Check state updated
        last_reasoning = get_last_reasoning()
        assert last_reasoning is not None
        assert isinstance(last_reasoning, AIReasoningOutput)
    
    finally:
        # Stop worker
        await stop_ai_worker_loop()


# ==================== ENDPOINT TESTS (SKIPPED - require client_with_auth fixture) ====================

@pytest.mark.skip(reason="Requires client_with_auth fixture - to be implemented")
@pytest.mark.asyncio
async def test_endpoint_last_run():
    """
    Test 9: GET /ai/global/last_run endpoint.
    
    Verifies:
    - Endpoint requires authentication
    - Returns 404 if no reasoning available
    - Returns 200 with valid data after reasoning
    """
    # TODO: Implement once client_with_auth fixture is available
    pass


@pytest.mark.skip(reason="Requires client_with_auth fixture - to be implemented")
@pytest.mark.asyncio
async def test_endpoint_manual_run():
    """
    Test 10: POST /ai/global/run endpoint.
    
    Verifies:
    - Endpoint requires authentication
    - Returns 200 with AIRunResponse
    - Response contains reasoning_id and execution time
    """
    # TODO: Implement once client_with_auth fixture is available
    pass


@pytest.mark.skip(reason="Requires client_with_auth fixture - to be implemented")
@pytest.mark.asyncio
async def test_endpoint_recommendations():
    """
    Test 11: GET /ai/global/recommendations endpoint.
    
    Verifies:
    - Endpoint requires authentication
    - Returns list of recommendations
    - Each recommendation has required fields
    """
    # TODO: Implement once client_with_auth fixture is available
    pass


@pytest.mark.skip(reason="Requires client_with_auth fixture - to be implemented")
@pytest.mark.asyncio
async def test_endpoint_snapshot():
    """
    Test 12: GET /ai/global/snapshot endpoint.
    
    Verifies:
    - Endpoint requires authentication
    - Returns SystemSnapshot structure
    - Contains expected fields
    """
    # TODO: Implement once client_with_auth fixture is available
    pass


@pytest.mark.skip(reason="Requires client_with_auth fixture - to be implemented")
@pytest.mark.asyncio
async def test_ai_endpoints_require_admin_or_manager():
    """
    Test RBAC: AI endpoints require admin or manager role.
    
    Verifies:
    - User without admin/manager role gets 403
    - Admin gets 200
    """
    # TODO: Implement once client_with_auth fixture is available
    pass
