import re

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.tables.email_verification_tokens.model import (
    EmailVerificationToken,
)
from api.database.tables.roles.model import DEFAULT_ROLE_NAME, Role
from api.database.tables.user_roles.model import UserRole
from api.database.tables.users.controller import create_user
from api.database.tables.users.model import User
from api.security.passwords import DUMMY_PASSWORD_HASH, hasher
from api.security.tokens import hash_token
from tests.conftest import SentEmail

PASSWORD: str = "velvet-orbit-tangerine-42"
ACCEPTED_BODY: dict[str, str] = {
    "key": "maybe_email_verification",
    "message": "If the email is valid, a verification mail has been sent",
}


def new_user_data(**overrides: str) -> dict[str, str]:
    return {
        "email": "ada@example.com",
        "username": "ada",
        "password": PASSWORD,
    } | overrides


async def add_existing_user(session: AsyncSession, email: str, username: str) -> None:
    await create_user(
        session=session,
        email=email,
        username=username,
        password_hash=DUMMY_PASSWORD_HASH,
    )
    await session.commit()


async def count_users(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(User)) or 0


async def test_register_creates_the_user_with_the_default_role(
    client: AsyncClient, database_session: AsyncSession
) -> None:
    response = await client.post(
        "/register", json=new_user_data(email="  Ada@Example.com ")
    )

    assert response.status_code == 202
    assert response.json() == ACCEPTED_BODY
    user = await database_session.scalar(select(User))
    assert user is not None
    assert user.email == "ada@example.com"
    assert user.username == "ada"
    assert user.email_verified_at is None
    assert hasher.verify(user.password_hash, PASSWORD)
    role_names = await database_session.scalars(
        select(Role.name).join(UserRole).where(UserRole.user_id == user.id)
    )
    assert role_names.all() == [DEFAULT_ROLE_NAME]


async def test_register_mails_a_link_carrying_the_stored_token(
    client: AsyncClient,
    database_session: AsyncSession,
    sent_emails: list[SentEmail],
) -> None:
    await client.post("/register", json=new_user_data())

    assert [email.to for email in sent_emails] == ["ada@example.com"]
    match = re.search(r"/auth/verify-email\?t=(\S+)", sent_emails[0].text)
    assert match is not None
    token = await database_session.scalar(select(EmailVerificationToken))
    assert token is not None
    assert token.token_hash == hash_token(match.group(1))
    assert token.email == "ada@example.com"
    assert token.consumed_at is None
    assert token.invalidated_at is None


async def test_register_with_a_registered_email_answers_as_if_it_succeeded(
    client: AsyncClient,
    database_session: AsyncSession,
    sent_emails: list[SentEmail],
) -> None:
    await add_existing_user(database_session, email="ada@example.com", username="ada")

    response = await client.post(
        "/register", json=new_user_data(email="ADA@example.com", username="lovelace")
    )

    assert response.status_code == 202
    assert response.json() == ACCEPTED_BODY
    assert sent_emails == []
    assert await count_users(database_session) == 1


async def test_register_with_a_taken_username_returns_409_whatever_its_case(
    client: AsyncClient,
    database_session: AsyncSession,
    sent_emails: list[SentEmail],
) -> None:
    await add_existing_user(database_session, email="ada@example.com", username="Ada")

    response = await client.post(
        "/register", json=new_user_data(email="grace@example.com", username="ada")
    )

    assert response.status_code == 409
    assert response.json() == {
        "errors": [
            {
                "key": "username_taken",
                "message": "This username is already taken",
                "field": "username",
            }
        ]
    }
    assert sent_emails == []
    # The failed INSERT aborted the request's savepoint only: the test's own
    # transaction still answers.
    assert await count_users(database_session) == 1


@pytest.mark.parametrize(
    ("password", "key"),
    [
        ("ada-lovelace-1815", "password_contextual"),
        ("123456789012", "password_too_common"),
    ],
)
async def test_register_rejects_a_weak_password(
    client: AsyncClient,
    database_session: AsyncSession,
    sent_emails: list[SentEmail],
    password: str,
    key: str,
) -> None:
    response = await client.post("/register", json=new_user_data(password=password))

    assert response.status_code == 422
    [error] = response.json()["errors"]
    assert (error["key"], error["field"]) == (key, "password")
    assert sent_emails == []
    assert await count_users(database_session) == 0
