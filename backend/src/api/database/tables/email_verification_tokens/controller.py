import uuid
from datetime import UTC, datetime

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.tables.email_verification_tokens.model import (
    VERIFICATION_TOKEN_TTL,
    EmailVerificationToken,
)
from api.security.tokens import generate_token, hash_token


async def issue_verification_token(
    session: AsyncSession, *, user_id: uuid.UUID, email: str
) -> str:
    # The live token, if any, is retired first: the partial unique index on user_id
    # would otherwise reject the INSERT. Its WHERE repeats the index predicate, so
    # the UPDATE goes through that index.
    await session.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.consumed_at.is_(None),
            EmailVerificationToken.invalidated_at.is_(None),
        )
        .values(invalidated_at=func.now())
    )
    # expires_at is computed here rather than as now() + interval in SQL: an
    # attribute assigned a SQL expression is expired after the flush, and reading it
    # back would lazy-load, which raises MissingGreenlet under asyncio.
    token: str = generate_token()
    session.add(
        EmailVerificationToken(
            token_hash=hash_token(token),
            email=email,
            expires_at=datetime.now(UTC) + VERIFICATION_TOKEN_TTL,
            user_id=user_id,
        )
    )
    await session.flush()
    return token
