"""seed default roles

Revision ID: 05048337db08
Revises: bd50723f9cfa
Create Date: 2026-09-22 20:10:24.015957

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = "05048337db08"
down_revision: str | Sequence[str] | None = "bd50723f9cfa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Reference data — the application assumes these roles exist (registration
# attaches "user" to every new account, and authorization checks will gate on
# them). Shipping the rows as a data migration keeps every environment in
# lockstep with the schema that introduced the requirement: no manual setup
# step to forget. The app-side mirror of these names lives in
# database/tables/roles/model.py, (USER_ROLE_NAME / ADMIN_ROLE_NAME); the strings are
# duplicated here on purpose, as a migration must stay a frozen snapshot.
DEFAULT_ROLES: list[dict[str, str]] = [
    {
        "name": "admin",
        "description": "Administrative access to the platform.",
    },
    {
        "name": "user",
        "description": "Default role granted to every registered account.",
    },
]


def upgrade() -> None:
    """Upgrade schema."""
    # Lightweight ad-hoc table for the insert: we don't import the SQLAlchemy
    # class because future schema changes to Role must not retroactively
    # alter the shape of an already-applied migration.
    #
    # created_at and updated_at are left out: omitted from the INSERT, they fall
    # back to their server_default now(), so these rows carry the database clock
    # like every other row the application writes.
    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    # Let the UNIQUE constraint on "name" decide which rows are missing, rather
    # than reading them first: the migration stays replayable against a database
    # seeded by hand, without a second statement that could disagree with it.
    # index_elements names the column, not the constraint, so PostgreSQL infers
    # the index backing it and the name it generated (roles_name_key) stays out.
    op.execute(
        insert(roles_table)
        .values(DEFAULT_ROLES)
        .on_conflict_do_nothing(index_elements=["name"])
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Delete by name rather than by id: a migration does not know the ids it
    # inserted, since uuidv7() computes them server-side and nothing reads them
    # back. The names are the only handle it still holds on its own rows.
    #
    # Two consequences, both accepted. The delete is wider than the insert was:
    # upgrade() skips a role already seeded by hand, but this removes it all the
    # same, having no way to tell it apart from one it created. And user_roles
    # references role_id with ON DELETE CASCADE, so dropping a role silently
    # drops every assignment pointing at it -- the only coherent outcome, since
    # an assignment cannot outlive the role it grants.
    roles_table = sa.table("roles", sa.column("name", sa.String))
    op.execute(
        roles_table.delete().where(
            roles_table.c.name.in_([role["name"] for role in DEFAULT_ROLES])
        )
    )
