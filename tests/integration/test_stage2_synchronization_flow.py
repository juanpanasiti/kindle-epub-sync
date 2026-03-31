"""Integration tests for the Stage 2 synchronization functionality."""

from dataclasses import dataclass

from kindle_epub_sync.application.use_cases.synchronize_epub_files import (
    SynchronizeEpubFilesCommand,
    SynchronizeEpubFilesUseCase,
)
from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.domain.entities.processing_report import FileProcessingStatus


@dataclass(slots=True)
class InMemoryFile:
    file_id: str
    name: str
    content: bytes


class InMemoryDriveGateway:
    def __init__(self, source_files: list[InMemoryFile]) -> None:
        self.source_files = source_files
        self.processed_files: list[InMemoryFile] = []

    def list_files(self, folder_id: str) -> list[FileDescriptor]:
        return [
            FileDescriptor(file_id=source_file.file_id, name=source_file.name)
            for source_file in self.source_files
        ]

    def download_file(self, file_id: str) -> bytes:
        return self._find_source_file(file_id).content

    def rename_file(self, file_id: str, new_name: str) -> None:
        file_to_rename = self._find_source_file(file_id)
        file_to_rename.name = new_name

    def move_file(self, file_id: str, destination_folder_id: str) -> None:
        source_file = self._find_source_file(file_id)
        self.source_files.remove(source_file)
        self.processed_files.append(source_file)

    def _find_source_file(self, file_id: str) -> InMemoryFile:
        for source_file in self.source_files:
            if source_file.file_id == file_id:
                return source_file
        raise ValueError(f"source file not found: {file_id}")


class InMemoryEmailGateway:
    def __init__(self, failures_by_filename: dict[str, int] | None = None) -> None:
        self.failures_by_filename = failures_by_filename or {}
        self.deliveries: list[tuple[str, bytes]] = []

    def send_epub(self, filename: str, content: bytes) -> None:
        retries_remaining = self.failures_by_filename.get(filename, 0)
        if retries_remaining > 0:
            self.failures_by_filename[filename] = retries_remaining - 1
            raise RuntimeError("temporary smtp failure")
        self.deliveries.append((filename, content))


def test_synchronization_end_to_end_with_collision_and_retry() -> None:
    drive_gateway = InMemoryDriveGateway(
        source_files=[
            InMemoryFile(file_id="1", name="Alpha_Book.epub", content=b"alpha"),
            InMemoryFile(file_id="2", name="Alpha Book.epub", content=b"collision"),
            InMemoryFile(file_id="3", name="Manual.EPUB", content=b"manual"),
            InMemoryFile(file_id="4", name="notes.txt", content=b"skip"),
            InMemoryFile(file_id="5", name="Retry_Book.epub", content=b"retry"),
        ],
    )
    email_gateway = InMemoryEmailGateway(failures_by_filename={"Retry Book.epub": 2})

    use_case = SynchronizeEpubFilesUseCase(
        drive_gateway=drive_gateway,
        email_gateway=email_gateway,
    )

    report = use_case.execute(
        SynchronizeEpubFilesCommand(
            source_folder_id="source",
            processed_folder_id="processed",
            max_email_retries=3,
        ),
    )

    assert report.total_files == 5
    assert report.succeeded == 4
    assert report.failed == 0
    assert report.skipped == 1

    status_by_file_id = {result.file_id: result.status for result in report.results}
    assert status_by_file_id == {
        "1": FileProcessingStatus.SUCCESS,
        "2": FileProcessingStatus.SUCCESS,
        "3": FileProcessingStatus.SUCCESS,
        "4": FileProcessingStatus.SKIPPED_NON_EPUB,
        "5": FileProcessingStatus.SUCCESS,
    }

    processed_names = sorted(source_file.name for source_file in drive_gateway.processed_files)
    assert processed_names == [
        "Alpha Book.epub",
        "Alpha Book_01.epub",
        "Manual.EPUB",
        "Retry Book.epub",
    ]

    remaining_source_names = sorted(source_file.name for source_file in drive_gateway.source_files)
    assert remaining_source_names == ["notes.txt"]

    delivered_filenames = sorted(filename for filename, _ in email_gateway.deliveries)
    assert delivered_filenames == [
        "Alpha Book.epub",
        "Alpha Book_01.epub",
        "Manual.EPUB",
        "Retry Book.epub",
    ]
