from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Read back the values the database computes (server_default, onupdate) with
    # RETURNING, in the same statement. Otherwise SQLAlchemy expires them and
    # lazy-loads them on the next access, which raises MissingGreenlet under
    # asyncio: the default "auto" only covers INSERT, not UPDATE.
    __mapper_args__ = {"eager_defaults": True}

    # Every Mapped[datetime] becomes TIMESTAMP WITH TIME ZONE. The default mapping
    # drops the time zone, which a column without an explicit type would get.
    type_annotation_map = {datetime: DateTime(timezone=True)}
