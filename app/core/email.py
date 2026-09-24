"""
Async outbound email for contact-form notifications.

Sent from a FastAPI BackgroundTask *after* the response is returned to the
visitor, so a slow or temporarily-down SMTP server never delays or fails
their form submission — the message is already safely in the database by
the time we attempt to email about it.

If SMTP isn't configured (e.g. local dev), EMAIL_ENABLED=False short-
circuits this to a no-op log line instead of raising.
"""
import logging

import aiosmtplib
from email.message import EmailMessage

from app.config import get_settings
from app.models.contact import ContactMessage

logger = logging.getLogger("app.email")


def _build_notification(msg: ContactMessage) -> EmailMessage:
    settings = get_settings()
    email = EmailMessage()
    email["From"] = settings.CONTACT_FROM_EMAIL
    email["To"] = settings.OWNER_NOTIFICATION_EMAIL
    email["Subject"] = f"New portfolio contact: {msg.subject or '(no subject)'}"
    email.set_content(
        f"New message from your portfolio contact form.\n\n"
        f"Name: {msg.name}\n"
        f"Email: {msg.email}\n"
        f"Phone: {msg.phone or '-'}\n"
        f"Intent: {msg.intent or '-'}\n"
        f"Subject: {msg.subject or '-'}\n\n"
        f"Message:\n{msg.message}\n\n"
        f"Message ID: {msg.id}\n"
        f"Received: {msg.created_at}\n"
    )
    return email


async def send_contact_notification(msg: ContactMessage) -> None:
    settings = get_settings()
    if not settings.EMAIL_ENABLED:
        logger.info("EMAIL_ENABLED is False — skipping notification for message %s", msg.id)
        return

    email = _build_notification(msg)
    try:
        await aiosmtplib.send(
            email,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=settings.SMTP_USE_TLS,
        )
    except Exception:
        # A failed notification email must never surface as an error to the
        # visitor (the message is already saved) and must never crash a
        # background task silently — so we log with full context instead.
        logger.exception("Failed to send contact notification for message %s", msg.id)
