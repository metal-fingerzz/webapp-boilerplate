import uuid
from datetime import datetime, timedelta

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from api.database.fields import created_at, foreign_key, parent, primary_key, updated_at
from api.database.tables.base import Base
from api.database.tables.users.model import User

VERIFICATION_TOKEN_TTL: timedelta = timedelta(hours=24)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

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


# At most one live token per user. The predicate is what allows it: a plain UNIQUE
# would also reject the consumed and invalidated rows a user accumulates over time.
#
# It leaves two indexes on user_id, this one and the one foreign_key() creates. They
# are not redundant: a partial index only serves queries that repeat its predicate,
# so reading a user's whole token history, and the ON DELETE CASCADE, still go
# through the plain one.
#
# Declared here, and written over the columns rather than as raw SQL, for the reason
# given in users/model.py: SQLAlchemy then knows the index depends on them.
Index(
    "email_verification_tokens_active_user_idx",
    EmailVerificationToken.user_id,
    unique=True,
    postgresql_where=(
        EmailVerificationToken.consumed_at.is_(None)
        & EmailVerificationToken.invalidated_at.is_(None)
    ),
)
