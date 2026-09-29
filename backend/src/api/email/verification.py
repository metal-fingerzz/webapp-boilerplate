from html import escape

from api.config import settings
from api.database.tables.email_verification_tokens.model import (
    EMAIL_VERIFICATION_TOKEN_TTL,
)
from api.email import EmailSendingParameters

SUBJECT: str = "Verify your email address"
PURPOSE: str = "Confirm your email address to finish creating your account."
BUTTON_LABEL: str = "Verify my email"
FALLBACK_INTRO: str = "If the button doesn't work, copy this link into your browser:"
IGNORE_NOTICE: str = "If you didn't create an account, you can ignore this email."


def verification_email(email_verification_token: str) -> EmailSendingParameters:
    link: str = (
        f"{settings.FRONTEND_URL}/auth/verify-email?t={email_verification_token}"
    )
    hours: int = int(EMAIL_VERIFICATION_TOKEN_TTL.total_seconds() // 3600)
    expiry: str = f"This link expires in {hours} hours."
    return {
        "subject": SUBJECT,
        "text": f"{PURPOSE}\n\n{link}\n\n{expiry}\n\n{IGNORE_NOTICE}\n",
        "html": _html(link=escape(link), expiry=expiry),
    }


def _html(link: str, expiry: str) -> str:
    styles = {
        "text": "margin:0 0 16px;font-size:16px;line-height:1.5;color:#1f2328",
        "small": "margin:0 0 16px;font-size:14px;line-height:1.5;color:#59636e",
        "button": (
            "display:inline-block;padding:12px 24px;border-radius:6px;"
            "background:#1f6feb;color:#ffffff;font-size:16px;font-weight:600;"
            "text-decoration:none"
        ),
    }
    return (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width">'
        f"<title>{SUBJECT}</title>"
        "</head>"
        '<body style="margin:0;padding:24px;background:#ffffff;'
        'font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
        '<div style="max-width:480px;margin:0 auto">'
        f'<p style="{styles["text"]}">{PURPOSE}</p>'
        f'<p style="margin:0 0 24px"><a href="{link}" style="{styles["button"]}">'
        f"{BUTTON_LABEL}</a></p>"
        f'<p style="{styles["small"]}">{FALLBACK_INTRO}<br>'
        f'<a href="{link}" style="color:#1f6feb;word-break:break-all">{link}</a></p>'
        f'<p style="{styles["small"]}">{expiry}</p>'
        f'<p style="{styles["small"]}">{IGNORE_NOTICE}</p>'
        "</div>"
        "</body>"
        "</html>"
    )
