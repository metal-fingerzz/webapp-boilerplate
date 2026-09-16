import uuid
from datetime import datetime

from sqlalchemy import Index, text
from sqlalchemy.orm import Mapped, mapped_column

from api.database.fields import created_at, foreign_key, parent, primary_key, updated_at
from api.database.tables.base import Base
from api.database.tables.users.model import User


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        Index(
            "uq_email_verification_tokens_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL AND invalidated_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = primary_key()
    token_hash: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    expires_at: Mapped[datetime]
    consumed_at: Mapped[datetime | None]
    invalidated_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    user_id: Mapped[uuid.UUID] = foreign_key("users.id", ondelete="CASCADE")
    user: Mapped[User] = parent()
