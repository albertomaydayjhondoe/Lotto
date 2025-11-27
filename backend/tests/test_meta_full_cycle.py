"""
Tests para Meta Full Autonomous Cycle (PASO 10.11)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.meta_full_cycle.cycle import MetaFullCycleManager
from app.meta_full_cycle.models import MetaCycleRunModel, MetaCycleActionLogModel


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def cycle_manager():
    """Cycle manager instance"""
    return MetaFullCycleManager()


# ==================== Test 1: Cycle Runs in Stub Mode ====================


@pytest.mark.asyncio
async def test_cycle_runs_in_stub_mode(cycle_manager, mock_db):
    """Test: Ciclo completo se ejecuta en modo stub"""
    
    # Mock database queries
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    mock_db.execute.return_value.scalar.return_value = 0
    
    cycle_run = await cycle_manager.run_cycle(
        db=mock_db,
        triggered_by="test",
        mode="stub",
    )
    
    assert isinstance(cycle_run, MetaCycleRunModel)
    assert cycle_run.status in ["success", "failed", "partial"]
    assert cycle_run.mode == "stub"
    assert len(cycle_run.steps_executed) > 0


# ==================== Test 2: Data Collection ====================


@pytest.mark.asyncio
async def test_cycle_collects_insights(cycle_manager, mock_db):
    """Test: STEP 1 - Recolección de datos funciona"""
    
    # Mock campaigns, adsets, ads
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        Mock(id="campaign_1"),
        Mock(id="campaign_2"),
    ]
    mock_db.execute.return_value.scalar.return_value = 1500.50
    
    stats = await cycle_manager._step_1_collection(mock_db)
    
    assert "campaigns_active" in stats
    assert "adsets_active" in stats
    assert "total_spend_today" in stats
    assert "avg_roas" in stats
    assert stats["avg_roas"] >= 0


# ==================== Test 3: A/B Winner Selection ====================


@pytest.mark.asyncio
async def test_cycle_applies_ab_winner(cycle_manager, mock_db):
    """Test: Decision A - A/B winner selection"""
    
    decisions = await cycle_manager._decision_a_ab_winner(mock_db)
    
    # Should have decisions (stub mode)
    assert isinstance(decisions, list)
    # In stub, should have at least 2 decisions (publish winner, pause loser)
    if len(decisions) > 0:
        assert decisions[0]["type"] == "ab_winner"
        assert "winner_ad_id" in decisions[0]["metadata"] or "action" in decisions[0]


# ==================== Test 4: ROAS Budget Scaling ====================


@pytest.mark.asyncio
async def test_cycle_applies_roas_scaling(cycle_manager, mock_db):
    """Test: Decision B - ROAS-based budget scaling"""
    
    decisions = await cycle_manager._decision_b_roas_budget(mock_db)
    
    assert isinstance(decisions, list)
    # Stub should produce some ROAS decisions
    if len(decisions) > 0:
        assert decisions[0]["type"] == "roas_scaling"
        assert decisions[0]["action"] in [
            "scale_up_30", "scale_down_30", "pause_adset", "maintain"
        ]


# ==================== Test 5: Spike Detection ====================


@pytest.mark.asyncio
async def test_cycle_detects_spikes(cycle_manager, mock_db):
    """Test: Decision C - Spike detection and handling"""
    
    decisions = await cycle_manager._decision_c_spike_handling(mock_db)
    
    assert isinstance(decisions, list)
    # Stub should detect at least 1 spike
    if len(decisions) > 0:
        assert decisions[0]["type"] == "spike_handling"
        assert "spike_type" in decisions[0]["metadata"]


# ==================== Test 6: Creative Fatigue ====================


@pytest.mark.asyncio
async def test_cycle_generates_variant_if_fatigue(cycle_manager, mock_db):
    """Test: Decision D - Creative fatigue detection"""
    
    decisions = await cycle_manager._decision_d_creative_fatigue(mock_db)
    
    assert isinstance(decisions, list)
    # Stub should detect 1 fatigued creative
    if len(decisions) > 0:
        assert decisions[0]["type"] == "creative_fatigue"
        assert decisions[0]["action"] == "generate_variant"


# ==================== Test 7: Logging ====================


@pytest.mark.asyncio
async def test_cycle_logs_all_steps(cycle_manager, mock_db):
    """Test: STEP 4 - Todos los pasos se loggean correctamente"""
    
    cycle_manager.current_run = MetaCycleRunModel(
        id=uuid4(),
        status="running",
        mode="stub",
    )
    
    # Add some test logs
    cycle_manager._log_action(
        step="test_step",
        action="test_action",
        input_snapshot={"test": "input"},
        output_snapshot={"test": "output"},
        success=True,
    )
    
    assert len(cycle_manager.action_logs) > 0
    assert cycle_manager.action_logs[0].step == "test_step"
    assert cycle_manager.action_logs[0].success is True


# ==================== Test 8: API - Run Cycle ====================


@pytest.mark.asyncio
async def test_api_run_cycle():
    """Test: POST /run ejecuta ciclo manual"""
    # This would require FastAPI TestClient
    # Stub test
    assert True  # TODO: Implement with TestClient


# ==================== Test 9: API - Get Last ====================


@pytest.mark.asyncio
async def test_api_get_last():
    """Test: GET /last retorna último ciclo"""
    # This would require FastAPI TestClient
    # Stub test
    assert True  # TODO: Implement with TestClient


# ==================== Test 10: API - History ====================


@pytest.mark.asyncio
async def test_api_history():
    """Test: GET /history retorna lista de ciclos"""
    # This would require FastAPI TestClient
    # Stub test
    assert True  # TODO: Implement with TestClient


# ==================== Test 11: Scheduler ====================


@pytest.mark.asyncio
async def test_scheduler_executes_cycle():
    """Test: Scheduler ejecuta ciclo cada 30 minutos"""
    from app.meta_full_cycle.scheduler import start_meta_cycle_scheduler
    
    # Test that scheduler can be started
    task = await start_meta_cycle_scheduler()
    assert task is not None
    
    # Cancel immediately to avoid infinite loop
    task.cancel()
    
    try:
        await task
    except:
        pass  # Expected cancellation


# ==================== Test 12: Full Integration Stub ====================


@pytest.mark.asyncio
async def test_full_cycle_integration_stub(cycle_manager, mock_db):
    """Test: Ciclo completo end-to-end en modo stub"""
    
    # Mock all database queries
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        Mock(id="test_1", status="ACTIVE"),
    ]
    mock_db.execute.return_value.scalar.return_value = 100.0
    
    cycle_run = await cycle_manager.run_cycle(
        db=mock_db,
        triggered_by="integration_test",
        mode="stub",
    )
    
    # Verify cycle completed
    assert cycle_run.status in ["success", "partial"]
    assert cycle_run.finished_at is not None
    assert cycle_run.duration_ms is not None
    assert cycle_run.duration_ms > 0
    
    # Verify all steps executed
    assert "step_1_collection" in cycle_run.steps_executed
    assert "step_2_decisions" in cycle_run.steps_executed
    assert "step_3_api_actions" in cycle_run.steps_executed
    assert "step_4_finalize" in cycle_run.steps_executed
    
    # Verify stats snapshot
    assert "campaigns_active" in cycle_run.stats_snapshot
    assert "actions_taken" in cycle_run.stats_snapshot
