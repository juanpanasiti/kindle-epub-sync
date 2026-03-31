"""Integration tests for Stage 4 SMTP gateway contract behavior."""

import ssl
from email.message import EmailMessage

from kindle_epub_sync.infrastructure.email.settings import EmailSettings
from kindle_epub_sync.infrastructure.email.smtp_gateway import SmtpEmailGateway


class CapturingSmtpClient:
    def __init__(self) -> None:
        self.sent_messages: list[EmailMessage] = []

    def __enter__(self) -> CapturingSmtpClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def ehlo(self) -> tuple[int, bytes]:
        return (250, b"ok")

    def starttls(self, *, context: ssl.SSLContext) -> tuple[int, bytes]:
        return (220, b"ready")

    def login(self, user: str, password: str) -> tuple[int, bytes]:
        return (235, b"authenticated")

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.sent_messages.append(msg)
        return {}


def test_stage4_gateway_sends_exactly_one_epub_attachment() -> None:
    settings = EmailSettings(
        kindle_email="reader@kindle.com",
        smtp_user="sender@example.com",
        smtp_password="app-password",
    )

    capturing_client = CapturingSmtpClient()

    gateway = SmtpEmailGateway(
        settings=settings,
        smtp_client_factory=lambda **_: capturing_client,
    )

    gateway.send_epub(filename="Novel.epub", content=b"epub-content")

    assert len(capturing_client.sent_messages) == 1
    message = capturing_client.sent_messages[0]

    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "Novel.epub"
    assert attachments[0].get_content_type() == "application/epub+zip"
