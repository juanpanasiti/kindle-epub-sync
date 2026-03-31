"""Integration tests focused on Stage 2 retry and failure behavior."""

from kindle_epub_sync.application.use_cases.synchronize_epub_files import (
    SynchronizeEpubFilesCommand,
    SynchronizeEpubFilesUseCase,
)
from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.domain.entities.processing_report import FileProcessingStatus


class DriveGatewayForRetryScenario:
    def __init__(self) -> None:
        self.moves: list[str] = []

    def list_files(self, folder_id: str) -> list[FileDescriptor]:
        return [
            FileDescriptor(file_id="1", name="will_fail.epub"),
            FileDescriptor(file_id="2", name="will_pass.epub"),
        ]

    def download_file(self, file_id: str) -> bytes:
        return file_id.encode("utf-8")

    def rename_file(self, file_id: str, new_name: str) -> None:
        return None

    def move_file(self, file_id: str, destination_folder_id: str) -> None:
        self.moves.append(file_id)


class EmailGatewayForRetryScenario:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}

    def send_epub(self, filename: str, content: bytes) -> None:
        self.calls[filename] = self.calls.get(filename, 0) + 1
        if filename == "will fail.epub":
            raise RuntimeError("smtp permanent failure")


def test_failed_email_does_not_move_file_and_next_file_is_processed() -> None:
    drive_gateway = DriveGatewayForRetryScenario()
    email_gateway = EmailGatewayForRetryScenario()
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

    assert report.results[0].status == FileProcessingStatus.FAILED_EMAIL
    assert report.results[0].email_attempts == 3
    assert report.results[1].status == FileProcessingStatus.SUCCESS
    assert drive_gateway.moves == ["2"]


def test_failed_file_is_retried_on_next_execution() -> None:
    class StatefulDriveGateway:
        def __init__(self) -> None:
            self.pending_files = [
                FileDescriptor(file_id="1", name="retry_me.epub"),
            ]
            self.moves: list[str] = []

        def list_files(self, folder_id: str) -> list[FileDescriptor]:
            return list(self.pending_files)

        def download_file(self, file_id: str) -> bytes:
            return b"payload"

        def rename_file(self, file_id: str, new_name: str) -> None:
            return None

        def move_file(self, file_id: str, destination_folder_id: str) -> None:
            self.moves.append(file_id)
            self.pending_files = [item for item in self.pending_files if item.file_id != file_id]

    class FlakyEmailGateway:
        def __init__(self) -> None:
            self.calls = 0

        def send_epub(self, filename: str, content: bytes) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary smtp failure")

    drive_gateway = StatefulDriveGateway()
    email_gateway = FlakyEmailGateway()
    use_case = SynchronizeEpubFilesUseCase(
        drive_gateway=drive_gateway,
        email_gateway=email_gateway,
    )

    first_report = use_case.execute(
        SynchronizeEpubFilesCommand(
            source_folder_id="source",
            processed_folder_id="processed",
            max_email_retries=1,
        ),
    )
    second_report = use_case.execute(
        SynchronizeEpubFilesCommand(
            source_folder_id="source",
            processed_folder_id="processed",
            max_email_retries=1,
        ),
    )

    assert first_report.results[0].status == FileProcessingStatus.FAILED_EMAIL
    assert second_report.results[0].status == FileProcessingStatus.SUCCESS
    assert drive_gateway.moves == ["1"]
