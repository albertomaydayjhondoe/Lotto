"""Add ledger_events table for system auditing

Revision ID: 001_ledger_events
Revises: 
Create Date: 2025-11-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_ledger_events'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create EventSeverity enum type
    event_severity_enum = postgresql.ENUM('INFO', 'WARN', 'ERROR', name='eventseverity')
    event_severity_enum.create(op.get_bind(), checkfirst=True)
    
    # Create ledger_events table
    op.create_table(
        'ledger_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('severity', event_severity_enum, nullable=False),
        sa.Column('worker_id', sa.String(length=100), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_ledger_events_timestamp', 'ledger_events', ['timestamp'])
    op.create_index('ix_ledger_events_event_type', 'ledger_events', ['event_type'])
    op.create_index('ix_ledger_events_job_id', 'ledger_events', ['job_id'])
    op.create_index('ix_ledger_events_clip_id', 'ledger_events', ['clip_id'])
    op.create_index('idx_entity_lookup', 'ledger_events', ['entity_type', 'entity_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_entity_lookup', table_name='ledger_events')
    op.drop_index('ix_ledger_events_clip_id', table_name='ledger_events')
    op.drop_index('ix_ledger_events_job_id', table_name='ledger_events')
    op.drop_index('ix_ledger_events_event_type', table_name='ledger_events')
    op.drop_index('ix_ledger_events_timestamp', table_name='ledger_events')
    
    # Drop table
    op.drop_table('ledger_events')
    
    # Drop enum type
    sa.Enum(name='eventseverity').drop(op.get_bind(), checkfirst=True)
