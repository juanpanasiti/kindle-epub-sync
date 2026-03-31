"""Port abstraction for file repository operations."""

from collections.abc import Sequence
from typing import Protocol

from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor


class DriveGateway(Protocol):
    """Defines source and destination folder operations required by the use case."""

    def list_files(self, folder_id: str) -> Sequence[FileDescriptor]:
        """Return file descriptors currently available in a source folder."""

    def download_file(self, file_id: str) -> bytes:
        """Return the raw file content for email delivery."""

    def rename_file(self, file_id: str, new_name: str) -> None:
        """Rename a file in the source folder."""

    def move_file(self, file_id: str, destination_folder_id: str) -> None:
        """Move a file to the processed folder."""
