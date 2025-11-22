"""Add OAuth token fields to social_accounts

Revision ID: 008_oauth_tokens
Revises: 007_credentials_encryption
Create Date: 2025-11-22 11:00:00.000000

This migration adds OAuth infrastructure fields to the social_accounts table
to support OAuth token management and automatic token refresh for social
media platforms (Instagram, TikTok, YouTube).

Fields added:
- oauth_provider: Provider identifier (instagram, tiktok, youtube, etc.)
- oauth_access_token: OAuth access token for API calls
- oauth_refresh_token: Refresh token for automatic token renewal
- oauth_expires_at: Expiration timestamp for access token
- oauth_scopes: JSON list of granted OAuth scopes

All fields are nullable for backward compatibility.
Compatible with SQLite and PostgreSQL.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '008_oauth_tokens'
down_revision = '007_credentials_encryption'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add OAuth token fields to social_accounts table."""
    # Check if we're using SQLite or PostgreSQL
    connection = op.get_bind()
    dialect_name = connection.dialect.name
    
    # Use appropriate JSON type
    json_type = JSON if dialect_name == 'postgresql' else sa.Text
    
    with op.batch_alter_table('social_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('oauth_provider', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('oauth_access_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('oauth_refresh_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('oauth_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('oauth_scopes', json_type, nullable=True))


def downgrade() -> None:
    """Remove OAuth token fields from social_accounts table.
    
    WARNING: This will permanently delete all stored OAuth tokens.
    Accounts will need to re-authenticate after downgrade.
    """
    with op.batch_alter_table('social_accounts', schema=None) as batch_op:
        batch_op.drop_column('oauth_scopes')
        batch_op.drop_column('oauth_expires_at')
        batch_op.drop_column('oauth_refresh_token')
        batch_op.drop_column('oauth_access_token')
        batch_op.drop_column('oauth_provider')
