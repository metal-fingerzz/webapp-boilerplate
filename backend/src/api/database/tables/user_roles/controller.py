import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.tables.roles.model import Role
from api.database.tables.user_roles.model import UserRole


async def grant_role(
    session: AsyncSession, *, user_id: uuid.UUID, role_name: str
) -> None:
    role_id: uuid.UUID | None = await session.scalar(
        select(Role.id).where(Role.name == role_name)
    )
    if role_id is None:
        raise LookupError(f"Role {role_name} is missing from the database")
    session.add(UserRole(user_id=user_id, role_id=role_id))
