from fastapi import APIRouter

from api.validation.models.message import ApiMessage

auth_router = APIRouter()

maybe_email_verification = ApiMessage(
    key="maybe_email_verification",
    message="If the email is valid, a verification mail has been sent",
)

import api.routes.auth.register  # noqa: E402, F401
