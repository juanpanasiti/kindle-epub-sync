"""Unit tests for the EPUB synchronization use case."""

from dataclasses import dataclass

from kindle_epub_sync.application.use_cases.synchronize_epub_files import (
    SynchronizeEpubFilesCommand,
    SynchronizeEpubFilesUseCase,
)
from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.domain.entities.processing_report import FileProcessingStatus


@dataclass(slots=True)
class RecordedRename:
    file_id: str
    new_name: str


@dataclass(slots=True)
class RecordedMove:
    file_id: str
    destination_folder_id: str


class FakeDriveGateway:
    def __init__(self, files: list[FileDescriptor], file_contents: dict[str, bytes]) -> None:
        self.files = files
        self.file_contents = file_contents
        self.renames: list[RecordedRename] = []
        self.moves: list[RecordedMove] = []
        self.raise_on_rename: set[str] = set()
        self.raise_on_download: set[str] = set()
        self.raise_on_move: set[str] = set()

    def list_files(self, folder_id: str) -> list[FileDescriptor]:
        return self.files

    def download_file(self, file_id: str) -> bytes:
        if file_id in self.raise_on_download:
            raise RuntimeError("download failed")
        return self.file_contents[file_id]

    def rename_file(self, file_id: str, new_name: str) -> None:
        if file_id in self.raise_on_rename:
            raise RuntimeError("rename failed")
        self.renames.append(RecordedRename(file_id=file_id, new_name=new_name))

    def move_file(self, file_id: str, destination_folder_id: str) -> None:
        if file_id in self.raise_on_move:
            raise RuntimeError("move failed")
        self.moves.append(
            RecordedMove(
                file_id=file_id,
                destination_folder_id=destination_folder_id,
            ),
        )


class FakeEmailGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bytes]] = []
        self.failures_by_filename: dict[str, int] = {}

    def send_epub(self, filename: str, content: bytes) -> None:
        self.calls.append((filename, content))
        pending_failures = self.failures_by_filename.get(filename, 0)
        if pending_failures > 0:
            self.failures_by_filename[filename] = pending_failures - 1
            raise RuntimeError("smtp failure")


def _build_use_case(
    files: list[FileDescriptor],
    file_contents: dict[str, bytes],
) -> tuple[SynchronizeEpubFilesUseCase, FakeDriveGateway, FakeEmailGateway]:
    drive_gateway = FakeDriveGateway(files=files, file_contents=file_contents)
    email_gateway = FakeEmailGateway()
    use_case = SynchronizeEpubFilesUseCase(
        drive_gateway=drive_gateway,
        email_gateway=email_gateway,
    )
    return use_case, drive_gateway, email_gateway


def test_skips_non_epub_files() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="notes.txt")],
        file_contents={"1": b"ignored"},
    )

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.total_files == 1
    assert report.results[0].status == FileProcessingStatus.SKIPPED_NON_EPUB
    assert drive_gateway.renames == []
    assert drive_gateway.moves == []
    assert email_gateway.calls == []


def test_processes_epub_without_rename_when_no_underscore() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="Book.epub")],
        file_contents={"1": b"content"},
    )

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].status == FileProcessingStatus.SUCCESS
    assert report.results[0].final_name == "Book.epub"
    assert report.results[0].email_attempts == 1
    assert drive_gateway.renames == []
    assert drive_gateway.moves == [RecordedMove(file_id="1", destination_folder_id="done")]
    assert email_gateway.calls == [("Book.epub", b"content")]


def test_renames_by_replacing_underscores_before_emailing() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="My_Book.EPUB")],
        file_contents={"1": b"content"},
    )

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].status == FileProcessingStatus.SUCCESS
    assert report.results[0].final_name == "My Book.EPUB"
    assert drive_gateway.renames == [RecordedRename(file_id="1", new_name="My Book.EPUB")]
    assert email_gateway.calls == [("My Book.EPUB", b"content")]


def test_uses_incremental_suffix_when_renamed_name_collides() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[
            FileDescriptor(file_id="1", name="My_Book.epub"),
            FileDescriptor(file_id="2", name="My Book.epub"),
            FileDescriptor(file_id="3", name="My Book_01.epub"),
        ],
        file_contents={"1": b"c1", "2": b"c2", "3": b"c3"},
    )

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].final_name == "My Book_02.epub"
    assert report.results[0].status == FileProcessingStatus.SUCCESS
    assert drive_gateway.renames[0] == RecordedRename(file_id="1", new_name="My Book_02.epub")
    assert email_gateway.calls[0][0] == "My Book_02.epub"


def test_retries_email_up_to_maximum_and_continues() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[
            FileDescriptor(file_id="1", name="Fail_Book.epub"),
            FileDescriptor(file_id="2", name="Next_Book.epub"),
        ],
        file_contents={"1": b"f1", "2": b"f2"},
    )
    email_gateway.failures_by_filename = {
        "Fail Book.epub": 5,
        "Next Book.epub": 0,
    }

    report = use_case.execute(
        SynchronizeEpubFilesCommand(
            source_folder_id="src",
            processed_folder_id="done",
            max_email_retries=3,
        ),
    )

    assert report.results[0].status == FileProcessingStatus.FAILED_EMAIL
    assert report.results[0].email_attempts == 3
    assert report.results[1].status == FileProcessingStatus.SUCCESS
    assert drive_gateway.moves == [RecordedMove(file_id="2", destination_folder_id="done")]


def test_reports_rename_error_and_skips_following_actions() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="Bad_Book.epub")],
        file_contents={"1": b"content"},
    )
    drive_gateway.raise_on_rename.add("1")

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].status == FileProcessingStatus.FAILED_RENAME
    assert report.results[0].error_message == "rename failed"
    assert email_gateway.calls == []
    assert drive_gateway.moves == []


def test_reports_download_error_and_does_not_move() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="Bad_Book.epub")],
        file_contents={"1": b"content"},
    )
    drive_gateway.raise_on_download.add("1")

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].status == FileProcessingStatus.FAILED_DOWNLOAD
    assert email_gateway.calls == []
    assert drive_gateway.moves == []


def test_reports_move_error_after_successful_email() -> None:
    use_case, drive_gateway, email_gateway = _build_use_case(
        files=[FileDescriptor(file_id="1", name="Book.epub")],
        file_contents={"1": b"content"},
    )
    drive_gateway.raise_on_move.add("1")

    report = use_case.execute(
        SynchronizeEpubFilesCommand(source_folder_id="src", processed_folder_id="done"),
    )

    assert report.results[0].status == FileProcessingStatus.FAILED_MOVE
    assert report.results[0].email_attempts == 1
    assert len(email_gateway.calls) == 1


def test_report_aggregates_counts() -> None:
    use_case, _, email_gateway = _build_use_case(
        files=[
            FileDescriptor(file_id="1", name="ignore.txt"),
            FileDescriptor(file_id="2", name="Ok.epub"),
            FileDescriptor(file_id="3", name="Fail.epub"),
        ],
        file_contents={"2": b"ok", "3": b"bad"},
    )
    email_gateway.failures_by_filename = {"Fail.epub": 5}

    report = use_case.execute(
        SynchronizeEpubFilesCommand(
            source_folder_id="src",
            processed_folder_id="done",
            max_email_retries=3,
        ),
    )

    assert report.total_files == 3
    assert report.succeeded == 1
    assert report.failed == 1
    assert report.skipped == 1
