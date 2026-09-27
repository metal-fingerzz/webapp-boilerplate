from api.config import settings
from api.email import EmailSendingParameters


def verification_email(email_verification_token: str) -> EmailSendingParameters:
    return {
        "subject": "",
        "text": f"{settings.FRONTEND_URL}/?t={email_verification_token}",
        "html": (
            "<!DOCTYPE html>"
            '<html lang="en">'
            "<head>"
            ' <meta charset="utf-8">'
            ' <meta name="viewport" content="width=device-width">'
            " <title>TITLE</title>"
            "</head>"
            "<body>"
            "</body>"
            "</html>"
        ),
    }
