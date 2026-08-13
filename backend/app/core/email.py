import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("armonitex.email")


async def send_email(to_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
    """Sends an email via SMTP or logs in development mock mode."""
    settings = get_settings()
    message = EmailMessage()
    message["From"] = f"{settings.emails_from_name} <{settings.emails_from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    password = settings.smtp_password.get_secret_value()
    if settings.smtp_host and password != "change-me-in-production":
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, password)
                server.send_message(message)
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e!s}")
            return False
    else:
        logger.info(
            f"📧 [EMAIL MOCK NOTIFICATION] To: {to_email} | Subject: {subject}\nBody:\n{body}"
        )
        return True
