from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr
from pydantic_core import PydanticCustomError

from api.security.passwords import password_blacklist

PASSWORD_MIN_LENGTH: int = 12
PASSWORD_MAX_LENGTH: int = 128


def ensure_password_is_not_blacklisted(password: SecretStr) -> SecretStr:
    value: str = password.get_secret_value()
    if value.lower() in password_blacklist():
        raise PydanticCustomError(
            "password_too_common",
            "Password is too common, choose a less predictable one",
        )
    return password


PasswordField = Annotated[
    SecretStr,
    Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    AfterValidator(ensure_password_is_not_blacklisted),
]

# An already-existing password (login, current password): only the upper bound
# matters — we just guard against absurdly large payloads. The minimum length is
# a policy for *new* passwords; enforcing it here would reject valid credentials
# (or leak the policy) and turn a wrong password into a 422 instead of a 401.
ExistingPasswordField = Annotated[SecretStr, Field(max_length=PASSWORD_MAX_LENGTH)]
