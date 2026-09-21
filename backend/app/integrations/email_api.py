"""Notification channel for the Alert & Response Planning Agent.

Defaults to log-mode: it records the notification to the AgentDecisionLog/console instead of
sending real email, so running the demo never dispatches an actual message to a real address.
Set EMAIL_MODE=smtp and the SMTP_* variables to send for real.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("notifications")


def send_alert_email(subject: str, body: str, recipient: str | None = None) -> dict:
    recipient = recipient or settings.alert_recipient

    if settings.email_mode != "smtp" or not settings.smtp_host:
        logger.info("[LOG-MODE EMAIL] to=%s subject=%s\n%s", recipient, subject, body)
        return {"mode": "log", "sent": False, "recipient": recipient, "subject": subject}

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_user or "noreply@supplychain.local"
    message["To"] = recipient

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(message["From"], [recipient], message.as_string())

    return {"mode": "smtp", "sent": True, "recipient": recipient, "subject": subject}
