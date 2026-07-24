"""remove pause_requested from taskstatus enum

Revision ID: 6b6522a1db4f
Revises: f229af67f56e
Create Date: 2026-07-24 17:01:24.864696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b6522a1db4f'
down_revision: Union[str, Sequence[str], None] = 'f229af67f56e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Ensure no existing rows use PAUSE_REQUESTED (migrate to PAUSED if any)
    op.execute(
        "UPDATE task SET status = 'PAUSED' WHERE status = 'PAUSE_REQUESTED'"
    )
    # 2. Recreate the enum without PAUSE_REQUESTED
    op.execute("ALTER TYPE taskstatus RENAME TO taskstatus_old")
    op.execute(
        "CREATE TYPE taskstatus AS ENUM('UNCONFIRMED', 'BIDDING', 'PENDING_START', 'IN_PROGRESS', 'PAUSED', 'COMPLETED')"
    )
    op.execute(
        "ALTER TABLE task ALTER COLUMN status TYPE taskstatus USING status::text::taskstatus"
    )
    op.execute("DROP TYPE taskstatus_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TYPE taskstatus RENAME TO taskstatus_old"
    )
    op.execute(
        "CREATE TYPE taskstatus AS ENUM('UNCONFIRMED', 'BIDDING', 'PENDING_START', 'IN_PROGRESS', 'PAUSED', 'PAUSE_REQUESTED', 'COMPLETED')"
    )
    op.execute(
        "ALTER TABLE task ALTER COLUMN status TYPE taskstatus USING status::text::taskstatus"
    )
    op.execute("DROP TYPE taskstatus_old")