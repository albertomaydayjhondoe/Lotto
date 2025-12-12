"""placeholder migration to restore chain: 005_publishing_retries"""

from alembic import op
import sqlalchemy as sa

revision = '005_publishing_retries'
down_revision = '004_campaigns_orchestrator'
branch_labels = None
depends_on = None

def upgrade():
    pass


def downgrade():
    pass
