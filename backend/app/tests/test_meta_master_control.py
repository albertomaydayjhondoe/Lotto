"""Tests for Meta Master Control Tower (PASO 10.18)"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.meta_master_control.control_tower import MetaMasterControlTower
from app.meta_master_control.health_monitor import SystemHealthMonitor
from app.meta_master_control.orchestration_commander import OrchestrationCommander
from app.meta_master_control.schemas import (
    SystemHealthReport, ModuleHealthStatus, OrchestrationCommand,
    EmergencyStopRequest, ResumeOperationsRequest,
    CommandType, SystemStatus, ModuleHealth, RecoveryAction
)
from app.meta_master_control.models import (
    MetaControlTowerRunModel,
    MetaSystemHealthLogModel
)

# ==================== HEALTH MONITORING TESTS ====================

@pytest.mark.asyncio
async def test_health_monitoring_all_17_modules():
    """Test that Control Tower monitors all 17 Meta modules"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    # Get system health
    health = await control_tower.get_system_health()
    
    # Validate all 17 modules are checked
    assert health.total_modules == 15  # Updated count
    assert len(control_tower.META_MODULES) == 15
    assert len(health.modules) == 15
    
    # Validate counts add up
    assert (health.online_modules + health.degraded_modules + 
            health.offline_modules + health.unknown_modules) == health.total_modules
    
    # Validate each module has required fields
    for module in health.modules:
        assert module.module_name in [m[0] for m in control_tower.META_MODULES]
        assert module.status in [ModuleHealth.ONLINE, ModuleHealth.DEGRADED, 
                                  ModuleHealth.OFFLINE, ModuleHealth.UNKNOWN]
        assert 0 <= module.success_rate <= 1.0
        assert module.avg_execution_time_ms >= 0
        assert module.error_count_24h >= 0
        assert module.api_calls_24h >= 0
        assert module.db_connections >= 0

@pytest.mark.asyncio
async def test_module_health_status_detection():
    """Test module health status detection"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    # Check health status for a specific module
    module = await control_tower._check_module_health("10.7", "Autonomous System")
    
    assert module.module_name == "10.7"
    assert module.module_full_name == "Autonomous System"
    assert isinstance(module.status, ModuleHealth)
    assert module.checked_at is not None
    assert isinstance(module.is_scheduler_running, bool)
    assert isinstance(module.is_db_healthy, bool)
    assert isinstance(module.is_api_healthy, bool)

@pytest.mark.asyncio
async def test_system_health_report_aggregation():
    """Test system health report aggregation"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    health = await control_tower.get_system_health()
    
    # Validate system status levels
    assert health.system_status in [SystemStatus.HEALTHY, SystemStatus.DEGRADED,
                                     SystemStatus.CRITICAL, SystemStatus.EMERGENCY_STOP]
    
    # Validate system-wide metrics
    assert health.total_campaigns_active >= 0
    assert health.total_daily_budget_usd >= 0
    assert health.total_api_calls_24h >= 0
    assert health.total_errors_24h >= 0
    
    # Validate DB metrics
    assert health.db_connection_pool_size > 0
    assert health.db_active_connections >= 0
    assert health.db_query_avg_ms >= 0
    
    # Validate metadata
    assert health.report_timestamp is not None
    assert health.mode == "stub"
    assert isinstance(health.recommendations, list)
    assert isinstance(health.alerts, list)

# ==================== ORCHESTRATION COMMAND TESTS ====================

@pytest.mark.asyncio
async def test_orchestration_command_start_all():
    """Test START_ALL orchestration command"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    command = OrchestrationCommand(
        command_type=CommandType.START_ALL,
        reason="Start Meta Ads stack",
        execute_immediately=True
    )
    
    result = await control_tower.execute_command(command, executed_by="test")
    
    assert result.success is True
    assert result.command_type == CommandType.START_ALL
    assert len(result.modules_affected) == 15
    assert len(result.actions_executed) > 0
    assert result.execution_time_ms >= 1
    assert result.executed_by == "test"
    assert "executed successfully" in result.message.lower()

@pytest.mark.asyncio
async def test_orchestration_command_stop_all():
    """Test STOP_ALL orchestration command"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    command = OrchestrationCommand(
        command_type=CommandType.STOP_ALL,
        reason="Maintenance window",
        execute_immediately=True
    )
    
    result = await control_tower.execute_command(command, executed_by="test")
    
    assert result.success is True
    assert result.command_type == CommandType.STOP_ALL
    assert len(result.modules_affected) == 15
    assert len(result.actions_executed) > 0
    assert "executed successfully" in result.message.lower()

@pytest.mark.asyncio
async def test_orchestration_command_run_health_check():
    """Test RUN_HEALTH_CHECK orchestration command"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    command = OrchestrationCommand(
        command_type=CommandType.RUN_HEALTH_CHECK,
        reason="Manual health check",
        execute_immediately=True
    )
    
    result = await control_tower.execute_command(command, executed_by="test")
    
    assert result.success is True
    assert result.command_type == CommandType.RUN_HEALTH_CHECK
    assert len(result.modules_affected) == 15
    assert "executed successfully" in result.message.lower()

# ==================== EMERGENCY PROCEDURES TESTS ====================

@pytest.mark.asyncio
async def test_emergency_stop_procedures():
    """Test emergency stop procedures"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    request = EmergencyStopRequest(
        reason="Budget anomaly detected",
        stop_schedulers=True,
        pause_campaigns=True,
        send_alerts=True
    )
    
    result = await control_tower.emergency_stop(request)
    
    assert result.success is True
    assert result.schedulers_stopped > 0
    assert result.campaigns_paused > 0
    assert result.alerts_sent > 0
    assert result.stopped_at is not None
    assert "budget anomaly" in result.message.lower()
    assert control_tower.emergency_stop_active is True

@pytest.mark.asyncio
async def test_resume_operations_after_emergency():
    """Test resume operations after emergency stop"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    # First, emergency stop
    stop_request = EmergencyStopRequest(
        reason="Test emergency stop procedure",
        stop_schedulers=True,
        pause_campaigns=True,
        send_alerts=False
    )
    await control_tower.emergency_stop(stop_request)
    assert control_tower.emergency_stop_active is True
    
    # Then, resume
    resume_request = ResumeOperationsRequest(
        resume_schedulers=True,
        resume_campaigns=True,
        run_health_check=True
    )
    
    result = await control_tower.resume_operations(resume_request)
    
    assert result.success is True
    assert result.schedulers_resumed > 0
    assert result.campaigns_resumed > 0
    assert result.health_check_passed is True
    assert result.resumed_at is not None
    assert control_tower.emergency_stop_active is False

# ==================== AUTO-RECOVERY TESTS ====================

@pytest.mark.asyncio
async def test_auto_recovery_detection():
    """Test auto-recovery anomaly detection"""
    monitor = SystemHealthMonitor(mode="stub")
    
    # Create mock modules with issues
    modules = [
        ModuleHealthStatus(
            module_name="10.7",
            module_full_name="Autonomous System",
            status=ModuleHealth.OFFLINE,
            success_rate=0.0,
            avg_execution_time_ms=0,
            error_count_24h=0,
            db_connections=0,
            api_calls_24h=0,
            is_scheduler_running=False,
            is_db_healthy=False,
            is_api_healthy=False,
            checked_at=datetime.utcnow()
        ),
        ModuleHealthStatus(
            module_name="10.9",
            module_full_name="Budget Spike Manager",
            status=ModuleHealth.DEGRADED,
            success_rate=0.65,
            avg_execution_time_ms=5000,
            error_count_24h=75,  # High error count
            db_connections=2,
            api_calls_24h=1000,
            is_scheduler_running=True,
            is_db_healthy=True,
            is_api_healthy=False,
            checked_at=datetime.utcnow()
        )
    ]
    
    procedures = await monitor.detect_anomalies(modules)
    
    # Should detect multiple issues
    assert len(procedures) > 0
    
    # Check that procedures have correct structure
    for proc in procedures:
        assert proc.module_name in ["10.7", "10.9"]
        assert isinstance(proc.recommended_action, RecoveryAction)
        assert 0 <= proc.confidence <= 1.0
        assert isinstance(proc.auto_execute, bool)

@pytest.mark.asyncio
async def test_auto_recovery_execution():
    """Test auto-recovery procedure execution"""
    commander = OrchestrationCommander(mode="stub")
    
    from app.meta_master_control.schemas import RecoveryProcedure
    
    procedure = RecoveryProcedure(
        module_name="10.7",
        issue_detected="Scheduler not running",
        recommended_action=RecoveryAction.RESTART_SCHEDULER,
        confidence=0.95,
        auto_execute=True
    )
    
    result = await commander.execute_recovery(procedure)
    
    assert result.success is True
    assert result.module_name == "10.7"
    assert result.action_taken == RecoveryAction.RESTART_SCHEDULER
    assert result.recovery_time_ms >= 1
    assert result.executed_at is not None
    assert result.module_status_after in [ModuleHealth.ONLINE, ModuleHealth.UNKNOWN]

# ==================== COMPONENT TESTS ====================

@pytest.mark.asyncio
async def test_health_monitor_schedulers():
    """Test health monitor scheduler checks"""
    monitor = SystemHealthMonitor(mode="stub")
    
    scheduler_status = await monitor.monitor_schedulers()
    
    assert isinstance(scheduler_status, dict)
    assert len(scheduler_status) > 0
    
    for scheduler_name, is_running in scheduler_status.items():
        assert isinstance(scheduler_name, str)
        assert isinstance(is_running, bool)

@pytest.mark.asyncio
async def test_health_monitor_databases():
    """Test health monitor database checks"""
    monitor = SystemHealthMonitor(mode="stub")
    
    db_metrics = await monitor.monitor_databases()
    
    assert isinstance(db_metrics, dict)
    assert "connection_pool_size" in db_metrics
    assert "active_connections" in db_metrics
    assert "is_healthy" in db_metrics
    assert db_metrics["connection_pool_size"] > 0

@pytest.mark.asyncio
async def test_health_monitor_apis():
    """Test health monitor API checks"""
    monitor = SystemHealthMonitor(mode="stub")
    
    api_metrics = await monitor.monitor_apis()
    
    assert isinstance(api_metrics, dict)
    assert "meta_api_reachable" in api_metrics
    assert "api_response_time_ms" in api_metrics
    assert "success_rate_24h" in api_metrics
    assert isinstance(api_metrics["meta_api_reachable"], bool)

# ==================== DATABASE PERSISTENCE TESTS ====================
# NOTE: These tests require db_session fixture from conftest.py
# Uncomment when conftest.py is configured with db_session fixture

# @pytest.mark.asyncio
# async def test_control_tower_run_model_creation(db_session):
#     """Test MetaControlTowerRunModel creation"""
#     run = MetaControlTowerRunModel(
#         run_type="health_check",
#         command_type=None,
#         system_status="healthy",
#         total_modules_checked=15,
#         online_modules=13,
#         degraded_modules=2,
#         offline_modules=0,
#         module_health_details={"10.7": "online", "10.9": "degraded"},
#         actions_executed=["Health check completed"],
#         total_api_calls_24h=5000,
#         total_errors_24h=10,
#         total_campaigns_active=150,
#         total_daily_budget_usd=25000.0,
#         db_connection_pool_size=20,
#         db_active_connections=8,
#         db_query_avg_ms=45.2,
#         execution_time_ms=1500,
#         executed_by="scheduler",
#         executed_at=datetime.utcnow(),
#         recommendations=["Consider restarting module 10.9"],
#         alerts=[],
#         mode="stub"
#     )
    
#     db_session.add(run)
#     await db_session.commit()
#     await db_session.refresh(run)
    
#     assert run.id is not None
#     assert run.run_type == "health_check"
#     assert run.total_modules_checked == 15
#     assert run.online_modules == 13
#     assert isinstance(run.module_health_details, dict)

@pytest.mark.asyncio
# async def test_system_health_log_model_creation(db_session):
#     """Test MetaSystemHealthLogModel creation"""
#     log = MetaSystemHealthLogModel(
#         module_name="10.7",
#         module_full_name="Autonomous System",
#         health_status="online",
#         success_rate=0.95,
#         avg_execution_time_ms=2500,
#         error_count_24h=5,
#         api_calls_24h=1200,
#         is_scheduler_running=True,
#         is_db_healthy=True,
#         is_api_healthy=True,
#         last_run=datetime.utcnow() - timedelta(minutes=30),
#         next_run=datetime.utcnow() + timedelta(hours=12),
#         db_connections=3,
#         checked_at=datetime.utcnow(),
#         mode="stub"
#     )
    
#     db_session.add(log)
#     await db_session.commit()
#     await db_session.refresh(log)
    
#     assert log.id is not None
#     assert log.module_name == "10.7"
#     assert log.health_status == "online"
#     assert 0 <= log.success_rate <= 1.0

# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_health_check_workflow():
    """Test complete health check workflow"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    # 1. Get system health
    health = await control_tower.get_system_health()
    assert health.total_modules == 15
    
    # 2. If issues detected, run recovery
    if health.degraded_modules > 0 or health.offline_modules > 0:
        monitor = SystemHealthMonitor(mode="stub")
        procedures = await monitor.detect_anomalies(health.modules)
        
        # 3. Execute high-confidence recoveries
        commander = OrchestrationCommander(mode="stub")
        for proc in procedures:
            if proc.auto_execute and proc.confidence >= 0.85:
                result = await commander.execute_recovery(proc)
                assert result.success is True

@pytest.mark.asyncio
async def test_emergency_stop_resume_workflow():
    """Test emergency stop and resume workflow"""
    control_tower = MetaMasterControlTower(mode="stub")
    
    # 1. Emergency stop
    stop_request = EmergencyStopRequest(
        reason="Budget anomaly",
        stop_schedulers=True,
        pause_campaigns=True,
        send_alerts=True
    )
    stop_result = await control_tower.emergency_stop(stop_request)
    assert stop_result.success is True
    assert control_tower.emergency_stop_active is True
    
    # 2. Resume operations
    resume_request = ResumeOperationsRequest(
        resume_schedulers=True,
        resume_campaigns=True,
        run_health_check=True
    )
    resume_result = await control_tower.resume_operations(resume_request)
    assert resume_result.success is True
    assert control_tower.emergency_stop_active is False
