import os

# api.config resolves its .env file from ENV at import time, so this has to run
# before anything imports the application. pytest loads conftest.py before it
# imports any test module.
os.environ["ENV"] = "test"

import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from api.config import BACKEND_PATH, settings
from api.database import get_database_session
from api.main import api

# The server's own database, always present: CREATE and DROP DATABASE cannot run
# against the database they target.
MAINTENANCE_DATABASE: str = "postgres"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An HTTP client bound to the application, without a network layer."""
    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as client:
        yield client


# --- Database ---


async def _recreate_database(url: URL, keep: bool) -> None:
    engine = create_async_engine(
        url.set(database=MAINTENANCE_DATABASE),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    async with engine.connect() as connection:
        # FORCE closes the connections a crashed run may have left open.
        await connection.execute(
            text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')
        )
        if keep:
            await connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    await engine.dispose()


@pytest.fixture(scope="session")
def database() -> Iterator[None]:
    """The test database, created and migrated once per run, dropped at the end.

    A leftover from an interrupted run is dropped first. The schema comes from the
    migrations rather than from the models, because they also seed the roles.
    """
    url: URL = make_url(str(settings.DATABASE_URL))
    asyncio.run(_recreate_database(url, keep=True))
    # No alembic.ini: env.py would hand its logging section to fileConfig, which
    # disables every logger already created -- the application's included.
    alembic_config = Config()
    alembic_config.set_main_option("script_location", str(BACKEND_PATH / "migrations"))
    command.upgrade(alembic_config, "head")
    yield
    asyncio.run(_recreate_database(url, keep=False))


@pytest.fixture
async def database_connection(database: None) -> AsyncIterator[AsyncConnection]:
    """A connection whose transaction every test rolls back, requests included.

    Each request gets its own session on this connection, as it would get one from
    the pool. In create_savepoint mode, a session's commit() only releases a
    savepoint: the outer transaction stays open, and the rollback at teardown
    undoes everything the test wrote.

    The engine lives as long as the test: asyncpg connections are bound to the
    event loop, and each test has its own.
    """
    engine = create_async_engine(str(settings.DATABASE_URL), poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()

        async def get_test_database_session() -> AsyncIterator[AsyncSession]:
            async with _session_on(connection) as session:
                yield session

        api.dependency_overrides[get_database_session] = get_test_database_session
        try:
            yield connection
        finally:
            del api.dependency_overrides[get_database_session]
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def database_session(
    database_connection: AsyncConnection,
) -> AsyncIterator[AsyncSession]:
    """A session for the test itself, separate from the ones requests get.

    Reading through it goes back to the database instead of an identity map that
    the request filled.
    """
    async with _session_on(database_connection) as session:
        yield session


def _session_on(connection: AsyncConnection) -> AsyncSession:
    return AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


# --- Mail ---


@dataclass(frozen=True)
class SentEmail:
    to: str
    subject: str
    text: str
    html: str | None


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[SentEmail]:
    """The mails the application sent, recorded instead of delivered.

    Autouse: with no SMTP server, every mail would cost the retries' full delay.
    """
    sent: list[SentEmail] = []

    async def record(to: str, subject: str, text: str, html: str | None = None):
        sent.append(SentEmail(to=to, subject=subject, text=text, html=html))

    # send_email rather than the callers' send_email_in_the_background: every route
    # that mails goes through it, whatever name it imported.
    monkeypatch.setattr("api.email.send_email", record)
    return sent
