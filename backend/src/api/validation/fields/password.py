from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr

from api.security.passwords import ensure_not_blacklisted

MIN_LENGTH: int = 12
MAX_LENGTH: int = 128

PasswordField = Annotated[
    SecretStr,
    Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH),
    AfterValidator(ensure_not_blacklisted),
]

# An already-existing password (login, current password): only the upper bound
# matters — we just guard against absurdly large payloads. The minimum length is
# a policy for *new* passwords; enforcing it here would reject valid credentials
# (or leak the policy) and turn a wrong password into a 422 instead of a 401.
ExistingPasswordField = Annotated[SecretStr, Field(max_length=MAX_LENGTH)]
