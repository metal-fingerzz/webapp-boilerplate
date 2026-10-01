from fastapi import BackgroundTasks, status
from pydantic import SecretStr, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from api.database import DatabaseSession
from api.database.tables.email_verification_tokens.controller import (
    issue_email_verification_token,
)
from api.database.tables.roles.model import DEFAULT_ROLE_NAME
from api.database.tables.user_roles.controller import grant_role
from api.database.tables.users.controller import (
    EmailAlreadyRegistered,
    UsernameAlreadyTaken,
    create_user,
)
from api.database.tables.users.model import User
from api.email import send_email_in_the_background
from api.email.verification import verification_email
from api.error import ERROR_RESPONSE, HttpApiError
from api.routes.auth import auth_router, maybe_email_verification
from api.security.passwords import hash_password
from api.validation.fields.email import EmailField
from api.validation.fields.password import PasswordField
from api.validation.fields.username import UsernameField
from api.validation.models.message import ApiMessage
from api.validation.models.strict import StrictModel

CONTEXTUAL_TERM_MIN_LENGTH: int = 3


class NewUserData(StrictModel):
    email: EmailField
    username: UsernameField
    password: PasswordField

    # A field validator rather than a model one, so the error names the password
    # field. email and username are declared above it, hence already validated and
    # in info.data -- unless they failed, in which case they are simply not checked.
    @field_validator("password")
    @classmethod
    def ensure_password_is_not_contextual(
        cls, password: SecretStr, info: ValidationInfo
    ) -> SecretStr:
        context: list[str] = []
        if (username := info.data.get("username")) is not None:
            context.append(username.lower())
        if (email := info.data.get("email")) is not None:
            context.append(email.split(sep="@", maxsplit=1)[0])
        value: str = password.get_secret_value().lower()
        # Shorter terms are skipped: a one-letter local part would otherwise reject
        # every password holding that letter.
        if any(
            term in value for term in context if len(term) >= CONTEXTUAL_TERM_MIN_LENGTH
        ):
            raise PydanticCustomError(
                "password_contextual",
                "Password must not contain your username or the part of your email "
                "before the @, even as part of a longer word",
            )
        return password


@auth_router.post(
    path="/register",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_409_CONFLICT: ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ERROR_RESPONSE,
    },
)
async def register(
    request_body: NewUserData,
    database_session: DatabaseSession,
    background_tasks: BackgroundTasks,
) -> ApiMessage:
    email: EmailField = request_body.email
    username: UsernameField = request_body.username
    password: PasswordField = request_body.password
    password_hash: str = await hash_password(password.get_secret_value())
    try:
        user: User = await create_user(
            session=database_session,
            email=email,
            username=username,
            password_hash=password_hash,
        )
    except UsernameAlreadyTaken as error:
        raise HttpApiError(
            status_code=status.HTTP_409_CONFLICT,
            key="username_taken",
            message="This username is already taken",
            field="username",
        ) from error
    except EmailAlreadyRegistered:
        return maybe_email_verification
    await grant_role(
        session=database_session, user_id=user.id, role_name=DEFAULT_ROLE_NAME
    )
    email_verification_token: str = await issue_email_verification_token(
        session=database_session, user_id=user.id, email=user.email
    )
    # Before the mail is queued: a link must never point to an account that a
    # failed commit left out of the database.
    await database_session.commit()
    background_tasks.add_task(
        func=send_email_in_the_background,
        to=email,
        **verification_email(email_verification_token),
    )
    return maybe_email_verification
