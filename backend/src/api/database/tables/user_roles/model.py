import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped

from api.database.fields import created_at, link_key, parent
from api.database.tables.base import Base

if TYPE_CHECKING:
    from api.database.tables.roles.model import Role
    from api.database.tables.users.model import User


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = link_key("users.id")
    role_id: Mapped[uuid.UUID] = link_key("roles.id", index=True)
    created_at: Mapped[datetime] = created_at()

    user: Mapped[User] = parent(back_populates="role_links")
    role: Mapped[Role] = parent(back_populates="user_links")
