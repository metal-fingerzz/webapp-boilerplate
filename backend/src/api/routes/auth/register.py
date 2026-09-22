from typing import Self

from fastapi import status
from pydantic import model_validator
from sqlalchemy.exc import IntegrityError

from api.database import DatabaseSession
from api.database.tables.roles.model import DEFAULT_ROLE_NAME
from api.database.tables.user_roles.controller import grant_role
from api.database.tables.users.controller import create_user
from api.database.tables.users.model import User
from api.error import ERROR_RESPONSE
from api.routes.auth import auth_router
from api.security.passwords import hash
from api.validation.fields.email import EmailField
from api.validation.fields.password import PasswordField
from api.validation.fields.username import UsernameField
from api.validation.models.strict import StrictModel


class NewUserData(StrictModel):
    email: EmailField
    username: UsernameField
    password: PasswordField

    @model_validator(mode="after")
    def ensure_password_is_not_contextual(self) -> Self:
        is_password_contextual: bool = False
        context: list[str] = [
            self.username.lower(),
            self.email.split(sep="@", maxsplit=1)[0],
        ]
        if any(term in self.password.get_secret_value().lower() for term in context):
            is_password_contextual = True
        if is_password_contextual:
            raise ValueError("Password must not contain your username or your mail")
        return self


@auth_router.post(
    path="/register",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_409_CONFLICT: ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ERROR_RESPONSE,
    },
)
async def register(request_body: NewUserData, database_session: DatabaseSession):
    email: EmailField = request_body.email
    username: UsernameField = request_body.username
    password: PasswordField = request_body.password
    password_hash: str = await hash(password.get_secret_value())
    try:
        user: User = await create_user(
            session=database_session,
            email=email,
            username=username,
            password_hash=password_hash,
        )
        await grant_role(
            session=database_session, user_id=user.id, role_name=DEFAULT_ROLE_NAME
        )
    except IntegrityError:
        pass
    except LookupError:
        pass
