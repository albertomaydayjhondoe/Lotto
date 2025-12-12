"""Meta Master Control Tower Background Scheduler (PASO 10.18)"""
import asyncio
from datetime import datetime, timedelta
import logging

from app.core.database import async_session_maker
from app.meta_master_control.control_tower import MetaMasterControlTower
from app.meta_master_control.health_monitor import SystemHealthMonitor
from app.meta_master_control.orchestration_commander import OrchestrationCommander
from app.meta_master_control.models import (
    MetaControlTowerRunModel,
    MetaSystemHealthLogModel
)

logger = logging.getLogger(__name__)

async def master_control_background_task():
    """
    Meta Master Control Tower background task
    
    Frequency: Every 1 hour
    
    Actions:
    1. Run health check on all 17 Meta modules
    2. Detect degraded/offline modules
    3. Execute auto-recovery if needed
    4. Log results to DB
    5. Generate alerts if critical
    """
    logger.info("🏢 Meta Master Control Tower Scheduler Started - 1h cycle")
    
    while True:
        try:
            logger.info("🏢 [PASO 10.18] Starting Master Control Tower health check...")
            
            async with async_session_maker() as session:
                # Initialize components
                control_tower = MetaMasterControlTower(mode="stub")
                health_monitor = SystemHealthMonitor(mode="stub")
                commander = OrchestrationCommander(mode="stub")
                
                # 1. Run comprehensive health check
                health = await control_tower.get_system_health()
                
                logger.info(
                    f"🏢 System Health: {health.system_status.value} | "
                    f"Online: {health.online_modules}/{health.total_modules} | "
                    f"Degraded: {health.degraded_modules} | "
                    f"Offline: {health.offline_modules}"
                )
                
                # 2. Detect anomalies and recommend recovery
                recovery_procedures = await health_monitor.detect_anomalies(health.modules)
                
                if recovery_procedures:
                    logger.warning(
                        f"⚠️ Detected {len(recovery_procedures)} issues requiring attention"
                    )
                
                # 3. Execute auto-recovery for high-confidence procedures
                recoveries_performed = []
                for procedure in recovery_procedures:
                    if procedure.auto_execute and procedure.confidence >= 0.85:
                        logger.info(
                            f"🔧 Auto-recovery: {procedure.module_name} - "
                            f"{procedure.recommended_action.value}"
                        )
                        result = await commander.execute_recovery(procedure)
                        recoveries_performed.append({
                            "module": result.module_name,
                            "action": result.action_taken.value,
                            "success": result.success
                        })
                
                # 4. Persist to database
                run = MetaControlTowerRunModel(
                    run_type="scheduled_health_check",
                    command_type=None,
                    system_status=health.system_status.value,
                    total_modules_checked=health.total_modules,
                    online_modules=health.online_modules,
                    degraded_modules=health.degraded_modules,
                    offline_modules=health.offline_modules,
                    module_health_details={m.module_name: m.status.value for m in health.modules},
                    actions_executed=[f"Health check completed"],
                    recoveries_performed=recoveries_performed,
                    total_api_calls_24h=health.total_api_calls_24h,
                    total_errors_24h=health.total_errors_24h,
                    total_campaigns_active=health.total_campaigns_active,
                    total_daily_budget_usd=health.total_daily_budget_usd,
                    db_connection_pool_size=health.db_connection_pool_size,
                    db_active_connections=health.db_active_connections,
                    db_query_avg_ms=health.db_query_avg_ms,
                    execution_time_ms=1,
                    executed_by="scheduler",
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
                
                # 5. Generate alerts if critical
                if health.alerts:
                    for alert in health.alerts:
                        logger.error(f"🚨 ALERT: {alert}")
                
                logger.info("✅ Master Control Tower health check completed")
                
        except Exception as e:
            logger.error(f"❌ Master Control Tower error: {str(e)}", exc_info=True)
        
        # Wait 1 hour (faster monitoring than other modules)
        logger.info("⏰ Next Master Control Tower health check in 1 hour...")
        await asyncio.sleep(3600)  # 1 hour
