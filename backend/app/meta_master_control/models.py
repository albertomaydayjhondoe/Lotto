"""SQLAlchemy models for Meta Master Control Tower (PASO 10.18)"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.core.database import Base

class MetaControlTowerRunModel(Base):
    """Control tower execution runs (PASO 10.18)"""
    __tablename__ = "meta_control_tower_runs"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Run details
    run_type = Column(String(50), nullable=False, index=True)  # health_check, command, recovery
    command_type = Column(String(50), nullable=True, index=True)  # CommandType enum
    
    # System status
    system_status = Column(String(20), nullable=False, index=True)  # SystemStatus enum
    total_modules_checked = Column(Integer, default=17, nullable=False)
    online_modules = Column(Integer, nullable=False)
    degraded_modules = Column(Integer, nullable=False)
    offline_modules = Column(Integer, nullable=False)
    
    # Module details
    module_health_details = Column(JSONB, nullable=False)  # Dict[module_name, ModuleHealthStatus]
    
    # Actions taken
    actions_executed = Column(JSONB, nullable=True)  # List[str]
    errors_encountered = Column(JSONB, nullable=True)  # List[str]
    recoveries_performed = Column(JSONB, nullable=True)  # List[RecoveryResult]
    
    # Metrics
    total_api_calls_24h = Column(Integer, default=0, nullable=False)
    total_errors_24h = Column(Integer, default=0, nullable=False)
    total_campaigns_active = Column(Integer, default=0, nullable=False)
    total_daily_budget_usd = Column(Float, default=0.0, nullable=False)
    
    # Database health
    db_connection_pool_size = Column(Integer, nullable=True)
    db_active_connections = Column(Integer, nullable=True)
    db_query_avg_ms = Column(Float, nullable=True)
    
    # Execution
    execution_time_ms = Column(Integer, nullable=False)
    executed_by = Column(String(100), nullable=True)  # scheduler, api, admin
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Recommendations
    recommendations = Column(JSONB, nullable=True)  # List[str]
    alerts = Column(JSONB, nullable=True)  # List[str]
    
    # Mode
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_control_runs_status_executed', 'system_status', 'executed_at'),
        Index('ix_control_runs_type_status', 'run_type', 'system_status'),
        Index('ix_control_runs_command_executed', 'command_type', 'executed_at'),
    )

class MetaSystemHealthLogModel(Base):
    """System health log entries (PASO 10.18)"""
    __tablename__ = "meta_system_health_logs"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Module identification
    module_name = Column(String(50), nullable=False, index=True)  # e.g., "10.5", "10.16"
    module_full_name = Column(String(200), nullable=False)
    
    # Health status
    health_status = Column(String(20), nullable=False, index=True)  # ModuleHealth enum
    
    # Metrics
    success_rate = Column(Float, nullable=False)  # 0-1
    avg_execution_time_ms = Column(Integer, nullable=False)
    error_count_24h = Column(Integer, default=0, nullable=False)
    api_calls_24h = Column(Integer, default=0, nullable=False)
    
    # Component health
    is_scheduler_running = Column(Boolean, nullable=False, index=True)
    is_db_healthy = Column(Boolean, nullable=False, index=True)
    is_api_healthy = Column(Boolean, nullable=False, index=True)
    
    # Last execution
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    # Error details
    last_error = Column(Text, nullable=True)
    last_error_time = Column(DateTime, nullable=True, index=True)
    
    # Recovery
    recovery_attempts = Column(Integer, default=0, nullable=False)
    last_recovery_action = Column(String(50), nullable=True)  # RecoveryAction enum
    last_recovery_time = Column(DateTime, nullable=True)
    recovery_successful = Column(Boolean, nullable=True)
    
    # Resources
    db_connections = Column(Integer, default=0, nullable=False)
    memory_usage_mb = Column(Integer, nullable=True)
    cpu_usage_pct = Column(Float, nullable=True)
    
    # Metadata
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_health_logs_module_status', 'module_name', 'health_status'),
        Index('ix_health_logs_module_checked', 'module_name', 'checked_at'),
        Index('ix_health_logs_scheduler_db', 'is_scheduler_running', 'is_db_healthy'),
        Index('ix_health_logs_errors', 'error_count_24h', 'checked_at'),
    )
