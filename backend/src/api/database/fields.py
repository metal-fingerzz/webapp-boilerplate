import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column


def _datetime() -> DateTime:
    return DateTime(timezone=True)


def primary_key() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, server_default=text("uuidv7()"))


def created_at() -> Mapped[datetime]:
    return mapped_column(_datetime(), server_default=func.now())


def updated_at() -> Mapped[datetime]:
    return mapped_column(_datetime(), server_default=func.now(), onupdate=func.now())
