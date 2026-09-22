import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import Mapped, mapped_column

from api.database.fields import created_at, links, primary_key, through, updated_at
from api.database.tables.base import Base
from api.database.tables.user_roles.model import UserRole

if TYPE_CHECKING:
    from api.database.tables.users.model import User


DEFAULT_ROLE_NAME: str = "user"
ADMINISTRATOR_ROLE_NAME: str = "admin"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = primary_key()
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user_links: Mapped[list[UserRole]] = links(back_populates="role")
    users: AssociationProxy[list[User]] = through("user_links", "user", UserRole)
