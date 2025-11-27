"""Add Meta Creative Optimizer tables

Revision ID: 016_meta_creative_optimizer
Revises: 015_meta_creative_analyzer
Create Date: 2025-11-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '016_meta_creative_optimizer'
down_revision = '015_meta_creative_analyzer'
branch_labels = None
depends_on = None

def upgrade():
    # 1. meta_creative_decision
    op.create_table(
        'meta_creative_decision',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('creative_id', UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=False),
        sa.Column('optimization_id', UUID(as_uuid=True), nullable=False),
        
        # Role assignment
        sa.Column('assigned_role', sa.String(50), nullable=False),
        sa.Column('previous_role', sa.String(50), nullable=True),
        sa.Column('role_changed', sa.Boolean, nullable=False, server_default='false'),
        
        # Decision details
        sa.Column('recommended_actions', JSONB, nullable=False),
        sa.Column('priority', sa.Integer, nullable=False),
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('estimated_impact', sa.Float, nullable=True),
        
        # Budget decisions
        sa.Column('current_budget', sa.Float, nullable=True),
        sa.Column('recommended_budget', sa.Float, nullable=True),
        sa.Column('budget_change_pct', sa.Float, nullable=True),
        
        # Variant decisions
        sa.Column('should_generate_variants', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('variant_strategy', sa.String(50), nullable=True),
        sa.Column('should_recombine', sa.Boolean, nullable=False, server_default='false'),
        
        # Execution tracking
        sa.Column('actions_executed', JSONB, nullable=True),
        sa.Column('execution_status', sa.String(50), nullable=True),
        sa.Column('execution_errors', JSONB, nullable=True),
        
        # Processing metadata
        sa.Column('mode', sa.String(20), nullable=False, server_default='stub'),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('decided_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # 2. meta_creative_winner_log
    op.create_table(
        'meta_creative_winner_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=False),
        sa.Column('creative_id', UUID(as_uuid=True), nullable=False),
        sa.Column('optimization_id', UUID(as_uuid=True), nullable=False),
        
        # Winner selection details
        sa.Column('winner_score', sa.Float, nullable=False),
        sa.Column('overall_score', sa.Float, nullable=False),
        sa.Column('roas', sa.Float, nullable=False),
        sa.Column('ctr', sa.Float, nullable=False),
        sa.Column('cvr', sa.Float, nullable=False),
        sa.Column('spend', sa.Float, nullable=False),
        sa.Column('conversions', sa.Integer, nullable=False),
        
        # Runner-up info
        sa.Column('runner_up_creative_id', UUID(as_uuid=True), nullable=True),
        sa.Column('runner_up_score', sa.Float, nullable=True),
        sa.Column('candidates_evaluated', sa.Integer, nullable=False),
        
        # Decision metadata
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        
        # Performance tracking
        sa.Column('days_active', sa.Integer, nullable=False),
        sa.Column('days_as_winner', sa.Integer, nullable=False, server_default='0'),
        sa.Column('previous_winner_id', UUID(as_uuid=True), nullable=True),
        
        # Status
        sa.Column('is_current_winner', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('replaced_at', sa.DateTime, nullable=True),
        sa.Column('replaced_by_id', UUID(as_uuid=True), nullable=True),
        
        # Processing metadata
        sa.Column('mode', sa.String(20), nullable=False, server_default='stub'),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('selected_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # 3. meta_creative_optimization_audit
    op.create_table(
        'meta_creative_optimization_audit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('optimization_id', UUID(as_uuid=True), unique=True, nullable=False),
        
        # Scope
        sa.Column('campaign_ids', JSONB, nullable=False),
        sa.Column('campaigns_processed', sa.Integer, nullable=False),
        sa.Column('creatives_processed', sa.Integer, nullable=False),
        
        # Results summary
        sa.Column('winners_selected', sa.Integer, nullable=False),
        sa.Column('decisions_made', sa.Integer, nullable=False),
        sa.Column('actions_recommended', sa.Integer, nullable=False),
        sa.Column('orchestrations_executed', sa.Integer, nullable=False),
        
        # Decision breakdown
        sa.Column('winners_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('testers_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('fatigued_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('archived_count', sa.Integer, nullable=False, server_default='0'),
        
        # Action breakdown
        sa.Column('promote_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scale_budget_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('reduce_budget_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('generate_variants_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('recombine_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('pause_count', sa.Integer, nullable=False, server_default='0'),
        
        # Budget impact
        sa.Column('total_spend', sa.Float, nullable=False),
        sa.Column('total_budget_change', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('budget_scale_ups', sa.Integer, nullable=False, server_default='0'),
        sa.Column('budget_scale_downs', sa.Integer, nullable=False, server_default='0'),
        
        # Integration tracking
        sa.Column('data_sources_used', JSONB, nullable=False),
        sa.Column('orchestrator_calls', sa.Integer, nullable=False, server_default='0'),
        sa.Column('orchestrator_successes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('orchestrator_failures', sa.Integer, nullable=False, server_default='0'),
        
        # Errors
        sa.Column('errors', JSONB, nullable=True),
        sa.Column('warnings', JSONB, nullable=True),
        
        # Execution details
        sa.Column('execution_summary', sa.Text, nullable=True),
        sa.Column('trigger', sa.String(50), nullable=False),
        sa.Column('triggered_by', sa.String(100), nullable=True),
        
        # Processing metadata
        sa.Column('mode', sa.String(20), nullable=False, server_default='stub'),
        sa.Column('processing_time_ms', sa.Integer, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Indices for meta_creative_decision
    op.create_index('idx_creative_decision_creative_decided', 'meta_creative_decision', ['creative_id', 'decided_at'])
    op.create_index('idx_creative_decision_campaign_decided', 'meta_creative_decision', ['campaign_id', 'decided_at'])
    op.create_index('idx_creative_decision_optimization', 'meta_creative_decision', ['optimization_id', 'decided_at'])
    op.create_index('idx_creative_decision_role', 'meta_creative_decision', ['assigned_role', 'priority'])
    op.create_index('idx_creative_decision_actions', 'meta_creative_decision', ['should_generate_variants', 'should_recombine'])
    op.create_index('idx_creative_decision_execution', 'meta_creative_decision', ['execution_status', 'executed_at'])
    
    # Indices for meta_creative_winner_log
    op.create_index('idx_winner_log_campaign_selected', 'meta_creative_winner_log', ['campaign_id', 'selected_at'])
    op.create_index('idx_winner_log_creative_selected', 'meta_creative_winner_log', ['creative_id', 'selected_at'])
    op.create_index('idx_winner_log_current', 'meta_creative_winner_log', ['is_current_winner', 'campaign_id'])
    op.create_index('idx_winner_log_score', 'meta_creative_winner_log', ['winner_score', 'confidence'])
    op.create_index('idx_winner_log_performance', 'meta_creative_winner_log', ['roas', 'conversions'])
    
    # Indices for meta_creative_optimization_audit
    op.create_index('idx_optimization_audit_started', 'meta_creative_optimization_audit', ['started_at', 'mode'])
    op.create_index('idx_optimization_audit_trigger', 'meta_creative_optimization_audit', ['trigger', 'started_at'])
    op.create_index('idx_optimization_audit_performance', 'meta_creative_optimization_audit', ['campaigns_processed', 'processing_time_ms'])
    op.create_index('idx_optimization_audit_results', 'meta_creative_optimization_audit', ['winners_selected', 'decisions_made'])
    op.create_index('idx_optimization_audit_errors', 'meta_creative_optimization_audit', ['orchestrator_failures'])

def downgrade():
    op.drop_table('meta_creative_optimization_audit')
    op.drop_table('meta_creative_winner_log')
    op.drop_table('meta_creative_decision')
