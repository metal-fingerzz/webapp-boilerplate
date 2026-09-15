import uuid
from datetime import datetime

from sqlalchemy import Index, func, text
from sqlalchemy.orm import Mapped

from api.database.fields import created_at, primary_key, updated_at
from api.database.tables.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_email_lower", func.lower(text("email")), unique=True),
        Index("uq_users_username_lower", func.lower(text("username")), unique=True),
    )

    id: Mapped[uuid.UUID] = primary_key()
    email: Mapped[str]
    username: Mapped[str]
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
