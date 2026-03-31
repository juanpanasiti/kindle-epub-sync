"""SMTP email infrastructure adapter package."""

from kindle_epub_sync.infrastructure.email.settings import (
    EmailSettings,
    load_email_settings,
)
from kindle_epub_sync.infrastructure.email.smtp_gateway import SmtpEmailGateway

__all__ = ["EmailSettings", "SmtpEmailGateway", "load_email_settings"]
