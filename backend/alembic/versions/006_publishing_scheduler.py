"""Publishing Scheduler - Add scheduling fields to publish_logs

Revision ID: 006_publishing_scheduler
Revises: 005_publishing_retries
Create Date: 2025-11-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_publishing_scheduler'
down_revision = '005_publishing_retries'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add scheduling fields to publish_logs table:
    - schedule_type: "immediate" or "scheduled"
    - scheduled_for: When to publish (for scheduled posts)
    - scheduled_window_end: End of scheduling window (optional)
    - scheduled_by: Who scheduled ("manual", "rule_engine", "campaign_orchestrator")
    """
    # Add schedule_type column with default "immediate"
    op.add_column(
        'publish_logs',
        sa.Column('schedule_type', sa.String(length=50), server_default='immediate', nullable=True)
    )
    
    # Add scheduled_for column (datetime, nullable)
    op.add_column(
        'publish_logs',
        sa.Column('scheduled_for', sa.DateTime(), nullable=True)
    )
    
    # Add scheduled_window_end column (datetime, nullable)
    op.add_column(
        'publish_logs',
        sa.Column('scheduled_window_end', sa.DateTime(), nullable=True)
    )
    
    # Add scheduled_by column (string, nullable)
    op.add_column(
        'publish_logs',
        sa.Column('scheduled_by', sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    """
    Remove scheduling fields from publish_logs table.
    """
    op.drop_column('publish_logs', 'scheduled_by')
    op.drop_column('publish_logs', 'scheduled_window_end')
    op.drop_column('publish_logs', 'scheduled_for')
    op.drop_column('publish_logs', 'schedule_type')
