"""Create base tables: video_assets, clips, jobs

Revision ID: 003_base_video_clips
Revises: 002_add_ledger_events
Create Date: 2025-11-29 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_base_video_clips'
down_revision = '002_add_ledger_events'
branch_labels = None
depends_on = None


def upgrade():
    """Create base tables for video assets, clips, and jobs."""
    
    # Create video_assets table
    op.create_table(
        'video_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('release_date', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create unique index on idempotency_key
    op.create_index('idx_video_assets_idempotency_key', 'video_assets', ['idempotency_key'], unique=True)
    
    # Create clips table
    op.create_table(
        'clips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('video_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_ms', sa.Integer(), nullable=False),
        sa.Column('end_ms', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('visual_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for clips
    op.create_index('idx_clips_video_asset_id', 'clips', ['video_asset_id'])
    op.create_index('idx_clips_status', 'clips', ['status'])
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dedup_key', sa.String(255), nullable=True),
        sa.Column('video_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='SET NULL'),
    )
    
    # Create unique index on dedup_key
    op.create_index('idx_jobs_dedup_key', 'jobs', ['dedup_key'], unique=True)
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_video_asset_id', 'jobs', ['video_asset_id'])
    op.create_index('idx_jobs_clip_id', 'jobs', ['clip_id'])


def downgrade():
    """Drop base tables."""
    op.drop_table('jobs')
    op.drop_table('clips')
    op.drop_table('video_assets')
