"""Unit tests for SmtpEmailGateway."""

import ssl
from email.message import EmailMessage

from kindle_epub_sync.infrastructure.email.settings import EmailSettings
from kindle_epub_sync.infrastructure.email.smtp_gateway import (
    SMTP_TIMEOUT_SECONDS,
    SmtpEmailGateway,
)


class FakeSmtpClient:
    def __init__(self) -> None:
        self.starttls_called = False
        self.login_calls: list[tuple[str, str]] = []
        self.sent_messages: list[EmailMessage] = []

    def __enter__(self) -> FakeSmtpClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def ehlo(self) -> tuple[int, bytes]:
        return (250, b"ok")

    def starttls(self, *, context: ssl.SSLContext) -> tuple[int, bytes]:
        self.starttls_called = True
        return (220, b"ready")

    def login(self, user: str, password: str) -> tuple[int, bytes]:
        self.login_calls.append((user, password))
        return (235, b"authenticated")

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.sent_messages.append(msg)
        return {}


def test_send_epub_authenticates_and_sends_single_attachment() -> None:
    settings = EmailSettings(
        kindle_email="reader@kindle.com",
        smtp_user="sender@example.com",
        smtp_password="app-password",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
    )

    fake_smtp_client = FakeSmtpClient()
    call_arguments: list[tuple[str, int, int]] = []

    def smtp_factory(*, host: str, port: int, timeout: int) -> FakeSmtpClient:
        call_arguments.append((host, port, timeout))
        return fake_smtp_client

    gateway = SmtpEmailGateway(
        settings=settings,
        smtp_client_factory=smtp_factory,
    )

    gateway.send_epub(filename="Book.epub", content=b"epub-bytes")

    assert call_arguments == [("smtp.gmail.com", 587, SMTP_TIMEOUT_SECONDS)]
    assert fake_smtp_client.starttls_called is True
    assert fake_smtp_client.login_calls == [("sender@example.com", "app-password")]
    assert len(fake_smtp_client.sent_messages) == 1

    message = fake_smtp_client.sent_messages[0]
    assert message["From"] == "sender@example.com"
    assert message["To"] == "reader@kindle.com"

    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "Book.epub"
    assert attachments[0].get_content_type() == "application/epub+zip"


def test_send_epub_propagates_smtp_errors() -> None:
    settings = EmailSettings(
        kindle_email="reader@kindle.com",
        smtp_user="sender@example.com",
        smtp_password="app-password",
    )

    class FailingSmtpClient(FakeSmtpClient):
        def login(self, user: str, password: str) -> tuple[int, bytes]:
            raise RuntimeError("smtp auth failed")

    def smtp_factory(*, host: str, port: int, timeout: int) -> FailingSmtpClient:
        return FailingSmtpClient()

    gateway = SmtpEmailGateway(
        settings=settings,
        smtp_client_factory=smtp_factory,
    )

    try:
        gateway.send_epub(filename="Book.epub", content=b"epub-bytes")
        raise AssertionError("Expected RuntimeError to be raised")
    except RuntimeError as error:
        assert str(error) == "smtp auth failed"
