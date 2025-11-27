"""Meta Master Control Tower Migration (PASO 10.18)

Revision ID: 018
Revises: 017
Create Date: 2025-01-15

Creates:
- meta_control_tower_runs: Control tower execution tracking
- meta_system_health_logs: Per-module health logs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None

def upgrade():
    """Create Meta Master Control Tower tables"""
    
    # 1. Create meta_control_tower_runs table
    op.create_table(
        'meta_control_tower_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_type', sa.String(50), nullable=False, comment='health_check, command, emergency_stop, resume'),
        sa.Column('command_type', sa.String(50), nullable=True, comment='Type of command if run_type=command'),
        sa.Column('system_status', sa.String(50), nullable=False, comment='healthy, degraded, critical, emergency_stop'),
        sa.Column('total_modules_checked', sa.Integer, nullable=False, server_default='0'),
        sa.Column('online_modules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('degraded_modules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('offline_modules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('module_health_details', JSONB, nullable=True, comment='Dict of module_name -> status'),
        sa.Column('actions_executed', JSONB, nullable=True, comment='List of actions taken'),
        sa.Column('errors_encountered', JSONB, nullable=True, comment='List of errors'),
        sa.Column('recoveries_performed', JSONB, nullable=True, comment='List of recovery procedures'),
        sa.Column('total_api_calls_24h', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_errors_24h', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_campaigns_active', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_daily_budget_usd', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('db_connection_pool_size', sa.Integer, nullable=False, server_default='0'),
        sa.Column('db_active_connections', sa.Integer, nullable=False, server_default='0'),
        sa.Column('db_query_avg_ms', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('execution_time_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('executed_by', sa.String(100), nullable=False, comment='scheduler, user_id, or api'),
        sa.Column('executed_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('recommendations', JSONB, nullable=True, comment='List of recommendations'),
        sa.Column('alerts', JSONB, nullable=True, comment='List of alerts'),
        sa.Column('mode', sa.String(10), nullable=False, server_default='stub', comment='stub or live'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indices for meta_control_tower_runs
    op.create_index('ix_control_runs_status_executed', 'meta_control_tower_runs', ['system_status', 'executed_at'])
    op.create_index('ix_control_runs_type_status', 'meta_control_tower_runs', ['run_type', 'system_status'])
    op.create_index('ix_control_runs_command_executed', 'meta_control_tower_runs', ['command_type', 'executed_at'])
    
    # 2. Create meta_system_health_logs table
    op.create_table(
        'meta_system_health_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('module_name', sa.String(20), nullable=False, comment='10.1, 10.2, ..., 10.17'),
        sa.Column('module_full_name', sa.String(100), nullable=False, comment='Full module name'),
        sa.Column('health_status', sa.String(20), nullable=False, comment='online, degraded, offline, unknown'),
        sa.Column('success_rate', sa.Float, nullable=False, server_default='0.0', comment='0.0 to 1.0'),
        sa.Column('avg_execution_time_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_count_24h', sa.Integer, nullable=False, server_default='0'),
        sa.Column('api_calls_24h', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_scheduler_running', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_db_healthy', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_api_healthy', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_run', sa.DateTime, nullable=True),
        sa.Column('next_run', sa.DateTime, nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('last_error_time', sa.DateTime, nullable=True),
        sa.Column('recovery_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_recovery_action', sa.String(50), nullable=True),
        sa.Column('recovery_successful', sa.Boolean, nullable=True),
        sa.Column('db_connections', sa.Integer, nullable=False, server_default='0'),
        sa.Column('memory_usage_mb', sa.Float, nullable=True),
        sa.Column('cpu_usage_pct', sa.Float, nullable=True),
        sa.Column('checked_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('mode', sa.String(10), nullable=False, server_default='stub', comment='stub or live'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indices for meta_system_health_logs
    op.create_index('ix_health_logs_module_status', 'meta_system_health_logs', ['module_name', 'health_status'])
    op.create_index('ix_health_logs_module_checked', 'meta_system_health_logs', ['module_name', 'checked_at'])
    op.create_index('ix_health_logs_scheduler_db', 'meta_system_health_logs', ['is_scheduler_running', 'is_db_healthy'])
    op.create_index('ix_health_logs_errors', 'meta_system_health_logs', ['error_count_24h', 'checked_at'])

def downgrade():
    """Drop Meta Master Control Tower tables"""
    op.drop_index('ix_health_logs_errors', table_name='meta_system_health_logs')
    op.drop_index('ix_health_logs_scheduler_db', table_name='meta_system_health_logs')
    op.drop_index('ix_health_logs_module_checked', table_name='meta_system_health_logs')
    op.drop_index('ix_health_logs_module_status', table_name='meta_system_health_logs')
    op.drop_table('meta_system_health_logs')
    
    op.drop_index('ix_control_runs_command_executed', table_name='meta_control_tower_runs')
    op.drop_index('ix_control_runs_type_status', table_name='meta_control_tower_runs')
    op.drop_index('ix_control_runs_status_executed', table_name='meta_control_tower_runs')
    op.drop_table('meta_control_tower_runs')
