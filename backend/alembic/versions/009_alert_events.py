"""009_alert_events

Create alert_events table for alerting system.

Revision ID: 009_alert_events
Revises: 008_oauth_tokens
Create Date: 2025-11-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_alert_events'
down_revision = '008_oauth_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create alert_events table."""
    op.create_table(
        'alert_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('read', sa.Integer(), nullable=False, server_default='0'),
    )
    
    # Create indices for common queries
    op.create_index('idx_alert_events_created_at', 'alert_events', ['created_at'])
    op.create_index('idx_alert_events_read', 'alert_events', ['read'])
    op.create_index('idx_alert_events_type', 'alert_events', ['alert_type'])
    op.create_index('idx_alert_events_severity', 'alert_events', ['severity'])


def downgrade() -> None:
    """Drop alert_events table."""
    op.drop_index('idx_alert_events_severity', table_name='alert_events')
    op.drop_index('idx_alert_events_type', table_name='alert_events')
    op.drop_index('idx_alert_events_read', table_name='alert_events')
    op.drop_index('idx_alert_events_created_at', table_name='alert_events')
    op.drop_table('alert_events')
