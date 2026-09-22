from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, EmailStr, Field

from api.validation.fields import lower, strip

EmailField = Annotated[
    EmailStr,
    Field(max_length=254),
    BeforeValidator(strip),
    AfterValidator(lower),
]
