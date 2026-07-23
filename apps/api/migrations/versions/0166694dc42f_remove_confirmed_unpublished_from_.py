"""remove confirmed_unpublished from taskstatus enum

Revision ID: 0166694dc42f
Revises: c572b59f57ba
Create Date: 2026-07-23 14:58:31.226800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0166694dc42f'
down_revision: Union[str, Sequence[str], None] = 'c572b59f57ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Update existing rows: CONFIRMED_UNPUBLISHED -> UNCONFIRMED
    op.execute(
        "UPDATE task SET status = 'UNCONFIRMED' WHERE status = 'CONFIRMED_UNPUBLISHED'"
    )
    # 2. Drop the old enum type and create a new one without CONFIRMED_UNPUBLISHED
    #    PostgreSQL doesn't allow removing values from an enum, so we recreate it.
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
        "CREATE TYPE taskstatus AS ENUM('UNCONFIRMED', 'CONFIRMED_UNPUBLISHED', 'BIDDING', 'PENDING_START', 'IN_PROGRESS', 'PAUSED', 'COMPLETED')"
    )
    op.execute(
        "ALTER TABLE task ALTER COLUMN status TYPE taskstatus USING status::text::taskstatus"
    )
    op.execute("DROP TYPE taskstatus_old")