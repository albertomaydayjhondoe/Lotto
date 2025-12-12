"""
Alembic migration: Add secure credentials storage to social_accounts.

Revision ID: 007_credentials_encryption
Revises: 006_publishing_scheduler
Create Date: 2025-11-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_credentials_encryption'
down_revision = '006_publishing_scheduler'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add encrypted credentials columns to social_accounts table.
    
    Compatible with both SQLite and PostgreSQL.
    """
    # Add encrypted_credentials column (binary data for Fernet-encrypted credentials)
    op.add_column(
        'social_accounts',
        sa.Column('encrypted_credentials', sa.LargeBinary(), nullable=True)
    )
    
    # Add credentials_version column (to track encryption algorithm version)
    op.add_column(
        'social_accounts',
        sa.Column('credentials_version', sa.String(50), nullable=True)
    )
    
    # Add credentials_updated_at column (timestamp of last credential update)
    op.add_column(
        'social_accounts',
        sa.Column('credentials_updated_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    """
    Remove encrypted credentials columns from social_accounts table.
    
    WARNING: This will permanently delete all encrypted credentials data!
    """
    op.drop_column('social_accounts', 'credentials_updated_at')
    op.drop_column('social_accounts', 'credentials_version')
    op.drop_column('social_accounts', 'encrypted_credentials')
