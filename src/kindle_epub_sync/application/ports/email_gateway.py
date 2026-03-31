"""Port abstraction for Kindle email delivery."""

from typing import Protocol


class EmailGateway(Protocol):
    """Defines attachment delivery needed by the application use case."""

    def send_epub(self, filename: str, content: bytes) -> None:
        """Send an EPUB attachment to the Kindle destination."""

    def send_admin_notification(self, subject: str, body: str) -> None:
        """Send a plain-text notification email to the admin inbox."""
