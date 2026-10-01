from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.tables.users.model import User, username_unique_index


class EmailAlreadyRegistered(Exception):
    """The address belongs to an existing account."""


class UsernameAlreadyTaken(Exception):
    """The username belongs to an existing account."""


async def create_user(
    session: AsyncSession, email: str, username: str, password_hash: str
) -> User:
    user = User(email=email, username=username, password_hash=password_hash)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as error:
        # SQLAlchemy wraps the driver's error twice: only asyncpg's own exception
        # carries the name of the violated constraint.
        cause = error.orig.__cause__ if error.orig is not None else None
        if isinstance(cause, UniqueViolationError):
            match cause.as_dict().get("constraint_name"):
                case username_unique_index.name:
                    raise UsernameAlreadyTaken from error
                # PostgreSQL's own name for the UNIQUE that users/model.py leaves
                # unnamed on email.
                case "users_email_key":
                    raise EmailAlreadyRegistered from error
        raise
    return user
