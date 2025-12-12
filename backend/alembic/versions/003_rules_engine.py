"""
Migration: Create rules_engine_weights table

Revision ID: 003_rules_engine
Revises: 002_add_ledger_events
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '003_rules_engine'
down_revision = '003_base_video_clips'
branch_labels = None
depends_on = None


def upgrade():
    """Create rules_engine_weights table with initial data."""
    
    # Create table
    op.create_table(
        'rules_engine_weights',
        sa.Column('platform', sa.Text(), nullable=False),
        sa.Column('weights', JSONB, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('platform')
    )
    
    # Insert initial weights for each platform
    op.execute("""
        INSERT INTO rules_engine_weights (platform, weights, updated_at)
        VALUES 
            ('tiktok', 
             '{"visual_score": 0.5, "duration_ms": 0.2, "cut_position": 0.2, "motion_intensity": 0.1}'::jsonb,
             NOW()),
            ('instagram', 
             '{"visual_score": 0.5, "duration_ms": 0.2, "cut_position": 0.2, "motion_intensity": 0.1}'::jsonb,
             NOW()),
            ('youtube', 
             '{"visual_score": 0.5, "duration_ms": 0.2, "cut_position": 0.2, "motion_intensity": 0.1}'::jsonb,
             NOW())
    """)


def downgrade():
    """Drop rules_engine_weights table."""
    op.drop_table('rules_engine_weights')
