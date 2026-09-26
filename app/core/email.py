"""
Async outbound email for contact-form notifications.

Sent from a FastAPI BackgroundTask *after* the response is returned to the
visitor.
"""
import logging
import aiosmtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("app.email")


def _build_notification(msg_data: dict) -> EmailMessage:
    settings = get_settings()
    email = EmailMessage()
    email["From"] = settings.CONTACT_FROM_EMAIL
    email["To"] = settings.OWNER_NOTIFICATION_EMAIL
    
    subject = msg_data.get("subject", "(no subject)")
    email["Subject"] = f"New portfolio contact: {subject}"
    
    email.set_content(
        f"New message from your portfolio contact form.\n\n"
        f"Name: {msg_data.get('name')}\n"
        f"Email: {msg_data.get('email')}\n"
        f"Phone: {msg_data.get('phone') or '-'}\n"
        f"Intent: {msg_data.get('intent') or '-'}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{msg_data.get('message')}\n\n"
        f"Message ID: {msg_data.get('id', 'N/A')}\n"
    )
    return email


async def send_contact_notification(msg_data: dict) -> None:
    settings = get_settings()
    msg_id = msg_data.get("id", "Unknown")
    
    if not settings.EMAIL_ENABLED:
        logger.info("EMAIL_ENABLED is False — skipping notification for message %s", msg_id)
        return

    email = _build_notification(msg_data)
    
    try:
        await aiosmtplib.send(
            email,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=settings.SMTP_USE_TLS,
        )
        logger.info("Successfully sent contact notification for message %s", msg_id)
    except Exception:
        # Logs the full stack trace to your terminal so you can see if SMTP auth failed
        logger.exception("Failed to send contact notification for message %s", msg_id)