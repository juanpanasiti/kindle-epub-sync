"""Domain report entities for the EPUB synchronization flow."""

from dataclasses import dataclass, field
from enum import StrEnum


class FileProcessingStatus(StrEnum):
    """Outcome states produced while handling a single source file."""

    SKIPPED_NON_EPUB = "skipped_non_epub"
    SUCCESS = "success"
    FAILED_RENAME = "failed_rename"
    FAILED_DOWNLOAD = "failed_download"
    FAILED_EMAIL = "failed_email"
    FAILED_MOVE = "failed_move"


@dataclass(frozen=True, slots=True)
class FileProcessingResult:
    """Per-file result emitted by the synchronization use case."""

    file_id: str
    original_name: str
    final_name: str
    status: FileProcessingStatus
    email_attempts: int = 0
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class SynchronizationReport:
    """Aggregate execution report for a single synchronization run."""

    results: list[FileProcessingResult] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        """Return the number of files evaluated in the run."""
        return len(self.results)

    @property
    def succeeded(self) -> int:
        """Return the number of files fully processed."""
        return sum(result.status == FileProcessingStatus.SUCCESS for result in self.results)

    @property
    def failed(self) -> int:
        """Return the number of files that failed during processing."""
        non_failure_statuses = {
            FileProcessingStatus.SUCCESS,
            FileProcessingStatus.SKIPPED_NON_EPUB,
        }
        return sum(result.status not in non_failure_statuses for result in self.results)

    @property
    def skipped(self) -> int:
        """Return the number of files skipped by filtering rules."""
        return sum(
            result.status == FileProcessingStatus.SKIPPED_NON_EPUB
            for result in self.results
        )
