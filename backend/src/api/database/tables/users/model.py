import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index, func
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import Mapped

from api.database.fields import created_at, links, primary_key, through, updated_at
from api.database.tables.base import Base
from api.database.tables.user_roles.model import UserRole

if TYPE_CHECKING:
    from api.database.tables.roles.model import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = primary_key()
    email: Mapped[str]
    username: Mapped[str]
    password_hash: Mapped[str]
    email_verified_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    role_links: Mapped[list[UserRole]] = links(back_populates="user")
    roles: AssociationProxy[list[Role]] = through("role_links", "role", UserRole)


# Unique over the lowercased value, so two addresses differing only in case cannot
# both exist. Indexes rather than UNIQUE constraints because PostgreSQL does not
# accept a constraint over an expression, which is also why they are named by hand,
# imitating the convention in tables/base.py.
#
# Declared here rather than in __table_args__ because User.email only exists once
# the class body is closed. Naming the column as raw SQL there would work, but it
# would hide the dependency from SQLAlchemy: a renamed column would take the index
# with it when the generated migration drops the old one, and autogenerate would
# report nothing.
Index("users_email_lower_idx", func.lower(User.email), unique=True)
Index("users_username_lower_idx", func.lower(User.username), unique=True)
