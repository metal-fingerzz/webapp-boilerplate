from sqlalchemy.ext.asyncio import AsyncSession

from api.database.tables.users.model import User


async def create_user(
    session: AsyncSession, email: str, username: str, password_hash: str
) -> User:
    user = User(email=email, username=username, password_hash=password_hash)
    session.add(user)
    await session.flush()
    return user
