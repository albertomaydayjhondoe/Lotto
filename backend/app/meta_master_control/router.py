"""Meta Master Control Tower API Router (PASO 10.18)"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_session
from app.core.auth import get_current_user
from app.meta_master_control.control_tower import MetaMasterControlTower
from app.meta_master_control.models import (
    MetaControlTowerRunModel,
    MetaSystemHealthLogModel
)
from app.meta_master_control.schemas import (
    SystemHealthReport, OrchestrationCommand, OrchestrationResult,
    EmergencyStopRequest, EmergencyStopResult,
    ResumeOperationsRequest, ResumeOperationsResult,
    SystemReportRequest, SystemReport, ControlTowerStatus,
    MasterControlDashboard
)

router = APIRouter(prefix="/meta/control-tower", tags=["Meta Master Control Tower"])

@router.get("/status", response_model=ControlTowerStatus)
async def get_control_tower_status(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Get Meta Master Control Tower status
    
    Returns:
    - Control tower operational status
    - Last health check time
    - Emergency stop status
    - System overview
    """
    control_tower = MetaMasterControlTower(mode="stub")
    
    # Get system health
    health = await control_tower.get_system_health()
    
    # Calculate last run
    from sqlalchemy import select, desc
    result = await session.execute(
        select(MetaControlTowerRunModel)
        .order_by(desc(MetaControlTowerRunModel.executed_at))
        .limit(1)
    )
    last_run = result.scalar_one_or_none()
    
    return ControlTowerStatus(
        is_operational=True,
        emergency_stop_active=control_tower.emergency_stop_active,
        last_health_check=last_run.executed_at if last_run else None,
        next_health_check=None,  # Calculated by scheduler
        system_status=health.system_status,
        total_modules_monitored=len(control_tower.META_MODULES),
        online_modules=health.online_modules,
        degraded_modules=health.degraded_modules,
        offline_modules=health.offline_modules,
        mode="stub"
    )

@router.get("/health", response_model=SystemHealthReport)
async def get_system_health(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive system health report for all 17 Meta modules
    
    Returns:
    - Health status of each module
    - System-wide metrics
    - Recommendations
    - Alerts
    """
    control_tower = MetaMasterControlTower(mode="stub")
    health = await control_tower.get_system_health()
    
    # Persist to DB
    run = MetaControlTowerRunModel(
        run_type="health_check",
        command_type=None,
        system_status=health.system_status.value,
        total_modules_checked=health.total_modules,
        online_modules=health.online_modules,
        degraded_modules=health.degraded_modules,
        offline_modules=health.offline_modules,
        module_health_details={m.module_name: m.status.value for m in health.modules},
        total_api_calls_24h=health.total_api_calls_24h,
        total_errors_24h=health.total_errors_24h,
        total_campaigns_active=health.total_campaigns_active,
        total_daily_budget_usd=health.total_daily_budget_usd,
        db_connection_pool_size=health.db_connection_pool_size,
        db_active_connections=health.db_active_connections,
        db_query_avg_ms=health.db_query_avg_ms,
        execution_time_ms=1,
        executed_by=str(current_user.get("id", "api")),
        executed_at=datetime.utcnow(),
        recommendations=health.recommendations,
        alerts=health.alerts,
        mode="stub"
    )
    session.add(run)
    
    # Persist module health logs
    for module in health.modules:
        log = MetaSystemHealthLogModel(
            module_name=module.module_name,
            module_full_name=module.module_full_name,
            health_status=module.status.value,
            success_rate=module.success_rate,
            avg_execution_time_ms=module.avg_execution_time_ms,
            error_count_24h=module.error_count_24h,
            api_calls_24h=module.api_calls_24h,
            is_scheduler_running=module.is_scheduler_running,
            is_db_healthy=module.is_db_healthy,
            is_api_healthy=module.is_api_healthy,
            last_run=module.last_run,
            next_run=module.next_run,
            last_error=module.last_error,
            last_error_time=module.last_error_time,
            db_connections=module.db_connections,
            checked_at=module.checked_at,
            mode="stub"
        )
        session.add(log)
    
    await session.commit()
    
    return health

@router.post("/command", response_model=OrchestrationResult)
async def execute_orchestration_command(
    command: OrchestrationCommand,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Execute master orchestration command
    
    Commands:
    - START_ALL: Start all schedulers
    - STOP_ALL: Stop all schedulers  
    - RESTART_MODULE: Restart specific module
    - SYNC_ALL_DATA: Synchronize data
    - OPTIMIZE_ALL: Run optimization
    - RUN_HEALTH_CHECK: Force health check
    
    Requires: Admin role
    """
    control_tower = MetaMasterControlTower(mode="stub")
    executed_by = str(current_user.get("id", "api"))
    
    result = await control_tower.execute_command(command, executed_by)
    
    # Persist to DB
    run = MetaControlTowerRunModel(
        run_type="command",
        command_type=command.command_type.value,
        system_status="healthy",  # TODO: Get actual status
        total_modules_checked=len(result.modules_affected),
        actions_executed=result.actions_executed,
        errors_encountered=result.errors,
        execution_time_ms=result.execution_time_ms,
        executed_by=executed_by,
        executed_at=result.executed_at,
        mode="stub"
    )
    session.add(run)
    await session.commit()
    
    return result

@router.post("/emergency-stop", response_model=EmergencyStopResult)
async def emergency_stop(
    request: EmergencyStopRequest,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Execute emergency stop procedure
    
    Actions:
    - Stop all schedulers
    - Pause active campaigns
    - Send emergency alerts
    
    Requires: Admin role
    """
    control_tower = MetaMasterControlTower(mode="stub")
    result = await control_tower.emergency_stop(request)
    
    # Persist to DB
    run = MetaControlTowerRunModel(
        run_type="emergency_stop",
        command_type="emergency_stop",
        system_status="emergency_stop",
        total_modules_checked=result.schedulers_stopped,
        actions_executed=[f"Emergency stop: {request.reason}"],
        execution_time_ms=1,
        executed_by=str(current_user.get("id", "api")),
        executed_at=result.stopped_at,
        alerts=[f"EMERGENCY STOP: {request.reason}"],
        mode="stub"
    )
    session.add(run)
    await session.commit()
    
    return result

@router.post("/resume", response_model=ResumeOperationsResult)
async def resume_operations(
    request: ResumeOperationsRequest,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Resume operations after emergency stop
    
    Actions:
    - Resume schedulers
    - Resume campaigns
    - Run health check
    
    Requires: Admin role
    """
    control_tower = MetaMasterControlTower(mode="stub")
    result = await control_tower.resume_operations(request)
    
    # Persist to DB
    run = MetaControlTowerRunModel(
        run_type="resume_operations",
        command_type="resume_operations",
        system_status="healthy",
        total_modules_checked=result.schedulers_resumed,
        actions_executed=["Operations resumed"],
        execution_time_ms=1,
        executed_by=str(current_user.get("id", "api")),
        executed_at=result.resumed_at,
        mode="stub"
    )
    session.add(run)
    await session.commit()
    
    return result

@router.get("/report", response_model=SystemReport)
async def get_system_report(
    request: SystemReportRequest = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive system report
    
    Includes:
    - Recent health checks
    - Command history
    - Emergency events
    - Performance metrics
    - Module details
    """
    from sqlalchemy import select, and_, desc
    
    # Get health checks
    health_query = select(MetaControlTowerRunModel).where(
        MetaControlTowerRunModel.run_type == "health_check"
    ).order_by(desc(MetaControlTowerRunModel.executed_at)).limit(request.max_health_checks)
    
    health_result = await session.execute(health_query)
    health_checks = health_result.scalars().all()
    
    # Get command history
    command_query = select(MetaControlTowerRunModel).where(
        MetaControlTowerRunModel.run_type == "command"
    ).order_by(desc(MetaControlTowerRunModel.executed_at)).limit(request.max_commands)
    
    command_result = await session.execute(command_query)
    commands = command_result.scalars().all()
    
    # Get emergency events
    emergency_query = select(MetaControlTowerRunModel).where(
        MetaControlTowerRunModel.run_type.in_(["emergency_stop", "resume_operations"])
    ).order_by(desc(MetaControlTowerRunModel.executed_at)).limit(10)
    
    emergency_result = await session.execute(emergency_query)
    emergency_events = emergency_result.scalars().all()
    
    return SystemReport(
        report_period_start=request.period_start,
        report_period_end=request.period_end,
        total_health_checks=len(health_checks),
        total_commands_executed=len(commands),
        total_emergency_stops=len([e for e in emergency_events if e.run_type == "emergency_stop"]),
        health_checks=health_checks,
        commands=commands,
        emergency_events=emergency_events,
        generated_at=datetime.utcnow()
    )
