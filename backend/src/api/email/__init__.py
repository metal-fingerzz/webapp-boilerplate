import asyncio
import logging
from email.message import EmailMessage
from email.utils import formataddr
from typing import NotRequired, TypedDict

import aiosmtplib

from api.config import settings

logger: logging.Logger = logging.getLogger(name=__name__)

MAX_SENDING_ATTEMPT: int = 3
SENDING_TIMEOUT_IN_SECONDS: float = 15.0


class EmailSendingParameters(TypedDict):
    subject: str
    text: str
    html: NotRequired[str]


def is_transient_error(error: aiosmtplib.SMTPException) -> bool:
    def is_transient_code(code: int) -> bool:
        return 400 <= code < 500

    match error:
        case aiosmtplib.SMTPRecipientsRefused():
            return all(is_transient_code(refusal.code) for refusal in error.recipients)
        case aiosmtplib.SMTPResponseException():
            return is_transient_code(error.code)
        case (
            aiosmtplib.SMTPConnectError()
            | aiosmtplib.SMTPServerDisconnected()
            | aiosmtplib.SMTPTimeoutError()
        ):
            return True
        case _:
            return False


async def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    message = EmailMessage()
    message["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_FROM))
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    if html is not None:
        message.add_alternative(html, subtype="html")
    for attempt in range(1, MAX_SENDING_ATTEMPT + 1):
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD.get_secret_value()
                if settings.SMTP_PASSWORD
                else None,
                use_tls=settings.SMTP_TLS == "ssl",
                start_tls=settings.SMTP_TLS == "starttls",
                timeout=SENDING_TIMEOUT_IN_SECONDS,
            )
        except aiosmtplib.SMTPException as error:
            if attempt == MAX_SENDING_ATTEMPT or not is_transient_error(error):
                raise
            await asyncio.sleep(SENDING_TIMEOUT_IN_SECONDS)
        else:
            return


async def send_email_in_the_background(
    to: str, subject: str, text: str, html: str | None = None
) -> None:
    try:
        await send_email(to=to, subject=subject, text=text, html=html)
    except Exception:
        logger.exception("Mail delivery failed (to=%s subject=%r)", to, subject)
