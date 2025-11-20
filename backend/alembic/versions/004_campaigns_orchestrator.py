"""
Alembic migration: Add best_clip_decisions table for campaigns orchestrator.

Revision ID: 004_campaigns_orchestrator
Revises: 003_rules_engine
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_campaigns_orchestrator'
down_revision = '003_rules_engine'
branch_labels = None
depends_on = None


def upgrade():
    """Create best_clip_decisions table."""
    # Create best_clip_decisions table
    op.create_table(
        'best_clip_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('video_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('video_asset_id', 'platform', name='uq_video_asset_platform')
    )
    
    # Create indexes
    op.create_index(
        'idx_best_clip_decisions_video_platform',
        'best_clip_decisions',
        ['video_asset_id', 'platform']
    )
    op.create_index(
        'idx_best_clip_decisions_clip',
        'best_clip_decisions',
        ['clip_id']
    )


def downgrade():
    """Drop best_clip_decisions table."""
    op.drop_index('idx_best_clip_decisions_clip', table_name='best_clip_decisions')
    op.drop_index('idx_best_clip_decisions_video_platform', table_name='best_clip_decisions')
    op.drop_table('best_clip_decisions')
