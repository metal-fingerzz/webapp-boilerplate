from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    database_session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.database_session_factory
    )
    async with database_session_factory() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(dependency=get_database_session)]
