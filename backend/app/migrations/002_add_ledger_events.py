"""placeholder migration to restore chain: 002_add_ledger_events"""

from alembic import op
import sqlalchemy as sa

revision = '002_add_ledger_events'
down_revision = '001_ledger_events'
branch_labels = None
depends_on = None

def upgrade():
    pass


def downgrade():
    pass
