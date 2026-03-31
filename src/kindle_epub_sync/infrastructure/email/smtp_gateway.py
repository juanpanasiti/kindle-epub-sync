"""SMTP implementation for the EmailGateway port."""

import smtplib
import ssl
from collections.abc import Callable
from email.message import EmailMessage
from typing import Protocol, cast

from kindle_epub_sync.application.ports.email_gateway import EmailGateway
from kindle_epub_sync.infrastructure.email.settings import EmailSettings

SMTP_TIMEOUT_SECONDS = 30


class SmtpClient(Protocol):
    """Small protocol that captures the SMTP client behavior used by the adapter."""

    def __enter__(self) -> SmtpClient: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> object: ...

    def ehlo(self) -> tuple[int, bytes]: ...

    def starttls(self, *, context: ssl.SSLContext) -> tuple[int, bytes]: ...

    def login(self, user: str, password: str) -> tuple[int, bytes]: ...

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]: ...


SmtpClientFactory = Callable[..., SmtpClient]


class SmtpEmailGateway(EmailGateway):
    """Adapter that delivers one EPUB attachment per SMTP message."""

    def __init__(
        self,
        settings: EmailSettings,
        smtp_client_factory: SmtpClientFactory | None = None,
    ) -> None:
        self._settings = settings
        self._smtp_client_factory = smtp_client_factory or _default_smtp_client_factory

    def send_epub(self, filename: str, content: bytes) -> None:
        message = EmailMessage()
        message["From"] = self._settings.smtp_user
        message["To"] = self._settings.kindle_email
        message["Subject"] = "Kindle EPUB delivery"
        message.set_content("Automated EPUB delivery for Kindle.")
        message.add_attachment(
            content,
            maintype="application",
            subtype="epub+zip",
            filename=filename,
        )

        self._send_message(message)

    def send_admin_notification(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._settings.smtp_user
        message["To"] = self._settings.admin_email or self._settings.smtp_user
        message["Subject"] = subject
        message.set_content(body)

        self._send_message(message)

    def _send_message(self, message: EmailMessage) -> None:

        with self._smtp_client_factory(
            host=self._settings.smtp_host,
            port=self._settings.smtp_port,
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as smtp_client:
            smtp_client.ehlo()
            smtp_client.starttls(context=ssl.create_default_context())
            smtp_client.ehlo()
            smtp_client.login(
                user=self._settings.smtp_user,
                password=self._settings.smtp_password,
            )
            smtp_client.send_message(message)


def _default_smtp_client_factory(*, host: str, port: int, timeout: int) -> SmtpClient:
    return cast(SmtpClient, smtplib.SMTP(host=host, port=port, timeout=timeout))
