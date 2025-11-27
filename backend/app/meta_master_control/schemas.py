"""Pydantic schemas for Meta Master Control Tower (PASO 10.18)"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# ==================== ENUMS ====================

class SystemStatus(str, Enum):
    """Overall system status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY_STOP = "emergency_stop"

class ModuleHealth(str, Enum):
    """Health status of individual module"""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class CommandType(str, Enum):
    """Master orchestration command types"""
    START_ALL = "start_all"
    STOP_ALL = "stop_all"
    RESTART_MODULE = "restart_module"
    EMERGENCY_STOP = "emergency_stop"
    RESUME_OPERATIONS = "resume_operations"
    RUN_HEALTH_CHECK = "run_health_check"
    SYNC_ALL_DATA = "sync_all_data"
    OPTIMIZE_ALL = "optimize_all"

class RecoveryAction(str, Enum):
    """Auto-recovery actions"""
    RESTART_SCHEDULER = "restart_scheduler"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DB = "reconnect_db"
    RESET_MODULE = "reset_module"
    ALERT_ADMIN = "alert_admin"

# ==================== MODULE HEALTH ====================

class ModuleHealthStatus(BaseModel):
    """Health status of a single Meta module"""
    module_name: str = Field(..., description="Module identifier (10.1-10.17)")
    module_full_name: str
    status: ModuleHealth
    
    # Metrics
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    success_rate: float = Field(..., ge=0, le=1)
    avg_execution_time_ms: int
    
    # Errors
    error_count_24h: int = Field(default=0, ge=0)
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    # Resources
    db_connections: int = Field(default=0, ge=0)
    api_calls_24h: int = Field(default=0, ge=0)
    
    # Status
    is_scheduler_running: bool = True
    is_db_healthy: bool = True
    is_api_healthy: bool = True
    
    checked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SystemHealthReport(BaseModel):
    """Complete system health report"""
    system_status: SystemStatus
    total_modules: int = Field(17, ge=1)
    
    # Module counts
    online_modules: int
    degraded_modules: int
    offline_modules: int
    unknown_modules: int
    
    # Module details
    modules: List[ModuleHealthStatus]
    
    # System-wide metrics
    total_campaigns_active: int
    total_daily_budget_usd: float
    total_api_calls_24h: int
    total_errors_24h: int
    
    # Database health
    db_connection_pool_size: int
    db_active_connections: int
    db_query_avg_ms: float
    
    # Recommendations
    recommendations: List[str]
    alerts: List[str]
    
    report_timestamp: datetime
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)

# ==================== ORCHESTRATION COMMANDS ====================

class OrchestrationCommand(BaseModel):
    """Master orchestration command"""
    command_type: CommandType
    target_modules: Optional[List[str]] = None  # Specific modules or None for all
    parameters: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    force: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class OrchestrationResult(BaseModel):
    """Result of orchestration command"""
    command_id: UUID
    command_type: CommandType
    success: bool
    
    # Execution details
    modules_affected: List[str]
    actions_executed: List[str]
    errors: List[str]
    
    execution_time_ms: int
    executed_at: datetime
    executed_by: str
    
    message: str
    
    model_config = ConfigDict(from_attributes=True)

# ==================== EMERGENCY PROCEDURES ====================

class EmergencyStopRequest(BaseModel):
    """Emergency stop request"""
    reason: str = Field(..., min_length=10, max_length=500)
    stop_schedulers: bool = True
    pause_campaigns: bool = True
    send_alerts: bool = True
    
    model_config = ConfigDict(from_attributes=True)

class EmergencyStopResult(BaseModel):
    """Result of emergency stop"""
    success: bool
    schedulers_stopped: int
    campaigns_paused: int
    alerts_sent: int
    errors: List[str]
    
    stopped_at: datetime
    message: str
    
    model_config = ConfigDict(from_attributes=True)

class ResumeOperationsRequest(BaseModel):
    """Resume operations request"""
    resume_schedulers: bool = True
    resume_campaigns: bool = True
    run_health_check: bool = True
    
    model_config = ConfigDict(from_attributes=True)

class ResumeOperationsResult(BaseModel):
    """Result of resume operations"""
    success: bool
    schedulers_resumed: int
    campaigns_resumed: int
    health_check_passed: bool
    errors: List[str]
    
    resumed_at: datetime
    message: str
    
    model_config = ConfigDict(from_attributes=True)

# ==================== AUTO-RECOVERY ====================

class RecoveryProcedure(BaseModel):
    """Auto-recovery procedure"""
    module_name: str
    issue_detected: str
    recommended_action: RecoveryAction
    confidence: float = Field(..., ge=0, le=1)
    auto_execute: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class RecoveryResult(BaseModel):
    """Result of recovery procedure"""
    module_name: str
    action_taken: RecoveryAction
    success: bool
    recovery_time_ms: int
    
    # Status after recovery
    module_status_before: ModuleHealth
    module_status_after: ModuleHealth
    
    executed_at: datetime
    message: str
    
    model_config = ConfigDict(from_attributes=True)

# ==================== API SCHEMAS ====================

class ControlTowerStatus(BaseModel):
    """Status of control tower itself"""
    status: SystemStatus
    is_monitoring_active: bool
    monitoring_interval_seconds: int
    last_health_check: Optional[datetime] = None
    next_health_check: Optional[datetime] = None
    
    # Stats
    total_commands_executed: int
    total_recoveries_performed: int
    uptime_hours: float
    
    mode: str
    
    model_config = ConfigDict(from_attributes=True)

class MasterControlDashboard(BaseModel):
    """Master control dashboard data"""
    control_tower_status: ControlTowerStatus
    system_health: SystemHealthReport
    recent_commands: List[Dict[str, Any]]
    recent_recoveries: List[Dict[str, Any]]
    active_alerts: List[str]
    
    model_config = ConfigDict(from_attributes=True)

class SystemReportRequest(BaseModel):
    """Request for system report"""
    include_module_details: bool = True
    include_metrics: bool = True
    include_recommendations: bool = True
    time_range_hours: int = Field(24, ge=1, le=168)
    
    model_config = ConfigDict(from_attributes=True)

class SystemReport(BaseModel):
    """Comprehensive system report"""
    report_id: UUID
    report_period_start: datetime
    report_period_end: datetime
    
    # Summary
    system_status: SystemStatus
    total_uptime_pct: float
    
    # Module performance
    module_performance: List[Dict[str, Any]]
    
    # System metrics
    total_campaigns_run: int
    total_budget_spent_usd: float
    total_api_calls: int
    total_errors: int
    avg_error_rate: float
    
    # Top issues
    top_errors: List[Dict[str, int]]
    modules_needing_attention: List[str]
    
    # Recommendations
    optimization_suggestions: List[str]
    
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
