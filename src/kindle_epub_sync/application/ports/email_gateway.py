"""Port abstraction for Kindle email delivery."""

from typing import Protocol


class EmailGateway(Protocol):
    """Defines attachment delivery needed by the application use case."""

    def send_epub(self, filename: str, content: bytes) -> None:
        """Send an EPUB attachment to the Kindle destination."""
