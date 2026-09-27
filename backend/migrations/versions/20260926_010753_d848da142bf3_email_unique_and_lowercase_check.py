"""email unique and lowercase check

Revision ID: d848da142bf3
Revises: 05048337db08
Create Date: 2026-09-26 01:07:53.658968

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d848da142bf3"
down_revision: str | Sequence[str] | None = "05048337db08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # A row stored before EmailField lowercased addresses would fail the CHECK.
    # Lowering it cannot collide: users_email_lower_idx, still in place at this
    # point, already forbids two addresses differing only in case.
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")
    op.drop_index("users_email_lower_idx", table_name="users")
    op.create_unique_constraint("users_email_key", "users", ["email"])
    # Written by hand: autogenerate does not compare CHECK constraints.
    op.create_check_constraint("users_email_check", "users", "email = lower(email)")


def downgrade() -> None:
    """Downgrade schema."""
    # The original case of the addresses lowered by upgrade() is not restored: it
    # was never kept anywhere.
    op.drop_constraint("users_email_check", "users", type_="check")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_index(
        "users_email_lower_idx",
        "users",
        [sa.literal_column("lower(email)")],
        unique=True,
    )
