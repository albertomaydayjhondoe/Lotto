"""Add Meta Creative Analyzer tables

Revision ID: 015_meta_creative_analyzer
Revises: 014_meta_rt_engine
Create Date: 2025-01-XX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '015_meta_creative_analyzer'
down_revision = '014_meta_rt_engine'
branch_labels = None
depends_on = None

def upgrade():
    # 1. meta_creative_analysis
    op.create_table(
        'meta_creative_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('creative_id', UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=False),
        sa.Column('metrics', JSONB, nullable=False),
        sa.Column('overall_score', sa.Float, nullable=False),
        sa.Column('performance_score', sa.Float, nullable=False),
        sa.Column('engagement_score', sa.Float, nullable=False),
        sa.Column('completion_score', sa.Float, nullable=False),
        sa.Column('fatigue_penalty', sa.Float, nullable=False),
        sa.Column('score_components', JSONB, nullable=False),
        sa.Column('score_reasoning', sa.Text, nullable=True),
        sa.Column('is_fatigued', sa.Boolean, nullable=False),
        sa.Column('fatigue_score', sa.Float, nullable=False),
        sa.Column('fatigue_level', sa.String(50), nullable=False),
        sa.Column('fatigue_signals', JSONB, nullable=True),
        sa.Column('days_active', sa.Integer, nullable=False),
        sa.Column('impressions_total', sa.Integer, nullable=False),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('recommendation_type', sa.String(50), nullable=True),
        sa.Column('urgency', sa.String(50), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('analyzed_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # 2. meta_creative_variant
    op.create_table(
        'meta_creative_variant',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('variant_id', UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column('base_creative_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variant_number', sa.Integer, nullable=False),
        sa.Column('changes', JSONB, nullable=False),
        sa.Column('estimated_improvement', sa.Float, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('recombination_id', UUID(as_uuid=True), nullable=True),
        sa.Column('recombination_strategy', sa.String(50), nullable=True),
        sa.Column('actual_performance', JSONB, nullable=True),
        sa.Column('performance_vs_base', sa.Float, nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('tested', sa.Boolean, nullable=False),
        sa.Column('generated_at', sa.DateTime, nullable=False),
        sa.Column('tested_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # 3. meta_creative_health_log
    op.create_table(
        'meta_creative_health_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('creative_id', UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=False),
        sa.Column('health_status', sa.String(50), nullable=False),
        sa.Column('overall_score', sa.Float, nullable=False),
        sa.Column('is_fatigued', sa.Boolean, nullable=False),
        sa.Column('fatigue_level', sa.String(50), nullable=True),
        sa.Column('fatigue_score', sa.Float, nullable=True),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('recommendation_type', sa.String(50), nullable=True),
        sa.Column('urgency', sa.String(50), nullable=False),
        sa.Column('actions_taken', JSONB, nullable=True),
        sa.Column('auto_applied', sa.Boolean, nullable=False),
        sa.Column('metrics_snapshot', JSONB, nullable=True),
        sa.Column('mode', sa.String(20), nullable=False),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('checked_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Indices
    op.create_index('idx_creative_analysis_creative_analyzed', 'meta_creative_analysis', ['creative_id', 'analyzed_at'])
    op.create_index('idx_creative_analysis_fatigued', 'meta_creative_analysis', ['is_fatigued', 'fatigue_level', 'urgency'])
    op.create_index('idx_variant_base_creative', 'meta_creative_variant', ['base_creative_id', 'variant_number'])
    op.create_index('idx_variant_status', 'meta_creative_variant', ['status', 'tested'])
    op.create_index('idx_health_log_creative_checked', 'meta_creative_health_log', ['creative_id', 'checked_at'])
    op.create_index('idx_health_log_urgency', 'meta_creative_health_log', ['health_status', 'urgency'])

def downgrade():
    op.drop_table('meta_creative_health_log')
    op.drop_table('meta_creative_variant')
    op.drop_table('meta_creative_analysis')
