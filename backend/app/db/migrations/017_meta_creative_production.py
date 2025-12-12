"""017_meta_creative_production.py — PASO 10.17 Migration"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    """Create 4 tables for creative production engine"""
    
    # Table 1: Master creatives
    op.create_table(
        'meta_creative_productions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('video_url', sa.String(500), nullable=False),
        sa.Column('duration_seconds', sa.Float, nullable=False),
        sa.Column('authorized_pixels', JSONB, nullable=False),
        sa.Column('authorized_subgenres', JSONB, nullable=False),
        sa.Column('genre', sa.String(100), nullable=False),
        sa.Column('fragments', JSONB, nullable=False),
        sa.Column('style_guide', JSONB, nullable=False),
        sa.Column('human_instructions', sa.Text, nullable=True),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('total_variants_generated', sa.Integer, default=0, nullable=False),
        sa.Column('mode', sa.String(20), default='stub', nullable=False),
    )
    
    # Table 2: Variants
    op.create_table(
        'meta_creative_variants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variant_number', sa.Integer, nullable=False),
        sa.Column('variant_type', sa.String(50), nullable=False),
        sa.Column('narrative_structure', sa.String(50), nullable=False),
        sa.Column('fragments_order', JSONB, nullable=False),
        sa.Column('caption', sa.Text, nullable=False),
        sa.Column('hashtags', JSONB, nullable=False),
        sa.Column('text_overlay', sa.String(500), nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=False),
        sa.Column('duration_category', sa.String(20), nullable=False),
        sa.Column('color_lut', sa.String(100), nullable=True),
        sa.Column('changes', JSONB, nullable=False),
        sa.Column('estimated_score', sa.Float, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('actual_performance', JSONB, nullable=True),
        sa.Column('performance_score', sa.Float, nullable=True),
        sa.Column('meta_creative_id', sa.String(100), nullable=True),
        sa.Column('meta_ad_id', sa.String(100), nullable=True),
        sa.Column('upload_status', sa.String(20), default='generated', nullable=False),
        sa.Column('uploaded_at', sa.DateTime, nullable=True),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=True),
        sa.Column('adset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), default='generated', nullable=False),
        sa.Column('days_active', sa.Integer, default=0, nullable=False),
        sa.Column('is_fatigued', sa.Boolean, default=False, nullable=False),
        sa.Column('fatigue_score', sa.Float, nullable=True),
        sa.Column('archived_at', sa.DateTime, nullable=True),
        sa.Column('generated_at', sa.DateTime, nullable=False),
        sa.Column('last_updated', sa.DateTime, nullable=True),
        sa.Column('mode', sa.String(20), default='stub', nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['meta_creative_productions.id'], ondelete='CASCADE')
    )
    
    # Table 3: Fragments
    op.create_table(
        'meta_creative_fragments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('fragment_type', sa.String(20), nullable=False),
        sa.Column('video_url', sa.String(500), nullable=False),
        sa.Column('start_time', sa.Float, nullable=False),
        sa.Column('end_time', sa.Float, nullable=False),
        sa.Column('duration', sa.Float, nullable=False),
        sa.Column('master_creative_id', UUID(as_uuid=True), nullable=True),
        sa.Column('approved', sa.Boolean, default=False, nullable=False),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('performance_score', sa.Float, nullable=True),
        sa.Column('usage_count', sa.Integer, default=0, nullable=False),
        sa.Column('success_rate', sa.Float, nullable=True),
        sa.Column('best_for_structure', sa.String(50), nullable=True),
        sa.Column('best_with_pixels', JSONB, nullable=True),
        sa.Column('performance_by_structure', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_used', sa.DateTime, nullable=True),
        sa.Column('mode', sa.String(20), default='stub', nullable=False),
        sa.ForeignKeyConstraint(['master_creative_id'], ['meta_creative_productions.id'], ondelete='SET NULL')
    )
    
    # Table 4: Promotion logs
    op.create_table(
        'meta_creative_promotion_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('variant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('promotion_type', sa.String(20), nullable=False),
        sa.Column('meta_creative_id', sa.String(100), nullable=True),
        sa.Column('meta_ad_id', sa.String(100), nullable=True),
        sa.Column('meta_campaign_id', sa.String(100), nullable=True),
        sa.Column('meta_adset_id', sa.String(100), nullable=True),
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=True),
        sa.Column('adset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('promotion_status', sa.String(20), default='pending', nullable=False),
        sa.Column('upload_timestamp', sa.DateTime, nullable=False),
        sa.Column('completed_timestamp', sa.DateTime, nullable=True),
        sa.Column('success', sa.Boolean, default=False, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('budget_allocated', sa.Float, nullable=True),
        sa.Column('targeting_details', JSONB, nullable=True),
        sa.Column('promoted_by', sa.String(100), nullable=True),
        sa.Column('mode', sa.String(20), default='stub', nullable=False),
        sa.ForeignKeyConstraint(['variant_id'], ['meta_creative_variants.id'], ondelete='CASCADE')
    )

def downgrade():
    """Drop 4 tables"""
    op.drop_table('meta_creative_promotion_logs')
    op.drop_table('meta_creative_fragments')
    op.drop_table('meta_creative_variants')
    op.drop_table('meta_creative_productions')
