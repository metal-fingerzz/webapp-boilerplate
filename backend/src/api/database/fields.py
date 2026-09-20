import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, func, text
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship


def primary_key() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, server_default=text("uuidv7()"))


def created_at() -> Mapped[datetime]:
    return mapped_column(server_default=func.now())


# onupdate is SQLAlchemy-side, not a trigger: the compiler injects now() into the
# SET clause of every UPDATE it builds, ORM and Core alike. A statement that does
# not go through SQLAlchemy -- op.execute("UPDATE ...") in a data migration, a psql
# session -- leaves this column at its previous value, silently. That is the first
# path to check if a stale updated_at is ever the symptom.
#
# Handing the guarantee to the database means a trigger plus
# server_onupdate=FetchedValue() here, so SQLAlchemy reads the computed value back;
# the eager_defaults comment in tables/base.py explains why that read-back matters.
def updated_at() -> Mapped[datetime]:
    return mapped_column(server_default=func.now(), onupdate=func.now())


def foreign_key(target: str, *, ondelete: str, index: bool = True) -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey(target, ondelete=ondelete), index=index)


def parent(back_populates: str | None = None) -> Mapped[Any]:
    return relationship(back_populates=back_populates, lazy="raise")


def link_key(target: str, *, index: bool = False) -> Mapped[uuid.UUID]:
    return mapped_column(
        ForeignKey(target, ondelete="CASCADE"), primary_key=True, index=index
    )


def links(back_populates: str) -> Mapped[list[Any]]:
    return relationship(
        back_populates=back_populates,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


def through(
    collection: str, target: str, link_class: type
) -> AssociationProxy[list[Any]]:
    return association_proxy(
        collection, target, creator=lambda obj: link_class(**{target: obj})
    )
