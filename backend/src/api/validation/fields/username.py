from typing import Annotated

from pydantic import BeforeValidator, Field

from api.validation.fields import strip

UsernameField = Annotated[
    str,
    Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$"),
    BeforeValidator(strip),
]
