import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, func
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import Mapped, mapped_column

from api.database.fields import created_at, links, primary_key, through, updated_at
from api.database.tables.base import Base
from api.database.tables.user_roles.model import UserRole

if TYPE_CHECKING:
    from api.database.tables.roles.model import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = primary_key()
    email: Mapped[str] = mapped_column(
        CheckConstraint("email = lower(email)"), unique=True
    )
    username: Mapped[str]
    password_hash: Mapped[str]
    email_verified_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    role_links: Mapped[list[UserRole]] = links(back_populates="user")
    roles: AssociationProxy[list[Role]] = through("role_links", "role", UserRole)


username_unique_index = Index(
    "users_username_lower_idx", func.lower(User.username), unique=True
)
