from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Indexes follow PostgreSQL's own shape -- table first, kind last -- so a name
    # SQLAlchemy generates sits alongside the ones PostgreSQL generates for
    # constraints (users_pkey, roles_name_key, ..._fkey) rather than against them.
    # pk, uq, fk and ck are deliberately left unset: PostgreSQL names those by
    # documented, deterministic rules, and a "ck" key would force every
    # CheckConstraint in a project built from this template to carry a name.
    # Indexes named by hand imitate this shape. The ones over an expression have no
    # choice: PostgreSQL names those after the function, so both lower() indexes on
    # users would land as users_lower_idx and users_lower_idx1.
    metadata = MetaData(
        naming_convention={"ix": "%(table_name)s_%(column_0_N_name)s_idx"}
    )

    # Read back the values the database computes (server_default, onupdate) with
    # RETURNING, in the same statement. Otherwise SQLAlchemy expires them and
    # lazy-loads them on the next access, which raises MissingGreenlet under
    # asyncio: the default "auto" only covers INSERT, not UPDATE.
    __mapper_args__ = {"eager_defaults": True}

    # Every Mapped[datetime] becomes TIMESTAMP WITH TIME ZONE. The default mapping
    # drops the time zone, which a column without an explicit type would get.
    type_annotation_map = {datetime: DateTime(timezone=True)}
