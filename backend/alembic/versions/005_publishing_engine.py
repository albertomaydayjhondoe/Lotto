"""
Alembic migration: Add publishing engine tables.

Revision ID: 005_publishing_engine
Revises: 004_campaigns_orchestrator
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_publishing_engine'
down_revision = '004_campaigns_orchestrator'
branch_labels = None
depends_on = None


def upgrade():
    """Create social_accounts and publish_logs tables."""
    
    # Create social_accounts table
    op.create_table(
        'social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('handle', sa.String(255), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('is_main_account', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),  
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Create publish_logs table
    op.create_table(
        'publish_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('social_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('external_post_id', sa.String(255), nullable=True),
        sa.Column('external_url', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),  
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['social_account_id'], ['social_accounts.id'], ondelete='SET NULL')
    )
    
    # Create indexes on publish_logs
    op.create_index(
        'idx_publish_logs_platform_status',
        'publish_logs',
        ['platform', 'status']
    )
    op.create_index(
        'idx_publish_logs_clip_id',
        'publish_logs',
        ['clip_id']
    )
    op.create_index(
        'idx_publish_logs_social_account_id',
        'publish_logs',
        ['social_account_id']
    )


def downgrade():
    """Drop publishing engine tables."""
    op.drop_index('idx_publish_logs_social_account_id', table_name='publish_logs')
    op.drop_index('idx_publish_logs_clip_id', table_name='publish_logs')
    op.drop_index('idx_publish_logs_platform_status', table_name='publish_logs')
    op.drop_table('publish_logs')
    op.drop_table('social_accounts')
