"""Verifies the email integration's real code path (connect, STARTTLS, authenticate, send)
without needing real mail credentials or network access - smtplib itself is mocked, but the
surrounding logic (which settings gate which branch, what gets sent to whom) is real."""
from unittest.mock import MagicMock, patch

from app.config import settings
from app.integrations.email_api import send_alert_email


def test_log_mode_never_touches_smtplib(monkeypatch, caplog):
    monkeypatch.setattr(settings, "email_mode", "log")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        result = send_alert_email("Test Subject", "Test body", recipient="manager@example.com")

    mock_smtp_cls.assert_not_called()
    assert result == {"mode": "log", "sent": False, "recipient": "manager@example.com", "subject": "Test Subject"}


def test_smtp_mode_connects_authenticates_and_sends(monkeypatch):
    monkeypatch.setattr(settings, "email_mode", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "alerts@example.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")

    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_alert_email("Disruption: Steel Plate", "Coverage gap detected.", recipient="manager@example.com")

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("alerts@example.com", "app-password")

    assert mock_server.sendmail.call_count == 1
    from_addr, to_addrs, raw_message = mock_server.sendmail.call_args[0]
    assert from_addr == "alerts@example.com"
    assert to_addrs == ["manager@example.com"]
    assert "Disruption: Steel Plate" in raw_message
    assert "Coverage gap detected." in raw_message

    assert result == {"mode": "smtp", "sent": True, "recipient": "manager@example.com", "subject": "Disruption: Steel Plate"}


def test_smtp_mode_without_user_skips_login(monkeypatch):
    """An open relay / no-auth internal SMTP server is a valid real-world setup - login
    must not be called when no credentials are configured."""
    monkeypatch.setattr(settings, "email_mode", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "internal-relay.local")
    monkeypatch.setattr(settings, "smtp_port", 25)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        send_alert_email("Subject", "Body", recipient="ops@example.com")

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_not_called()
    mock_server.sendmail.assert_called_once()
