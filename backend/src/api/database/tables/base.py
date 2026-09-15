from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Read back the values the database computes (server_default, onupdate) with
    # RETURNING, in the same statement. Otherwise SQLAlchemy expires them and
    # lazy-loads them on the next access, which raises MissingGreenlet under
    # asyncio: the default "auto" only covers INSERT, not UPDATE.
    __mapper_args__ = {"eager_defaults": True}
