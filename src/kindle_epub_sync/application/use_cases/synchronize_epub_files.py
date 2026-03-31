"""Use case that synchronizes EPUB files from source to processed storage."""

from dataclasses import dataclass

from kindle_epub_sync.application.ports.drive_gateway import DriveGateway
from kindle_epub_sync.application.ports.email_gateway import EmailGateway
from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.domain.entities.processing_report import (
    FileProcessingResult,
    FileProcessingStatus,
    SynchronizationReport,
)


@dataclass(frozen=True, slots=True)
class SynchronizeEpubFilesCommand:
    """Input data needed to execute synchronization."""

    source_folder_id: str
    processed_folder_id: str
    max_email_retries: int = 3


class SynchronizeEpubFilesUseCase:
    """Coordinates listing, renaming, emailing, and moving EPUB files."""

    def __init__(self, drive_gateway: DriveGateway, email_gateway: EmailGateway) -> None:
        self._drive_gateway = drive_gateway
        self._email_gateway = email_gateway

    def execute(self, command: SynchronizeEpubFilesCommand) -> SynchronizationReport:
        """Process files from source folder and return structured execution details."""
        source_files = list(self._drive_gateway.list_files(command.source_folder_id))
        existing_names = {source_file.name for source_file in source_files}

        results: list[FileProcessingResult] = []

        for source_file in source_files:
            result = self._process_single_file(
                source_file=source_file,
                processed_folder_id=command.processed_folder_id,
                max_email_retries=command.max_email_retries,
                existing_names=existing_names,
            )
            results.append(result)

        return SynchronizationReport(results=results)

    def _process_single_file(
        self,
        source_file: FileDescriptor,
        processed_folder_id: str,
        max_email_retries: int,
        existing_names: set[str],
    ) -> FileProcessingResult:
        original_name = source_file.name

        if not self._is_epub_file(original_name):
            return FileProcessingResult(
                file_id=source_file.file_id,
                original_name=original_name,
                final_name=original_name,
                status=FileProcessingStatus.SKIPPED_NON_EPUB,
            )

        target_name = self._build_target_name(
            source_file=source_file,
            existing_names=existing_names,
        )

        if target_name != original_name:
            try:
                self._drive_gateway.rename_file(file_id=source_file.file_id, new_name=target_name)
            except Exception as error:
                return FileProcessingResult(
                    file_id=source_file.file_id,
                    original_name=original_name,
                    final_name=original_name,
                    status=FileProcessingStatus.FAILED_RENAME,
                    error_message=str(error),
                )

            existing_names.discard(original_name)
            existing_names.add(target_name)

        try:
            file_content = self._drive_gateway.download_file(file_id=source_file.file_id)
        except Exception as error:
            return FileProcessingResult(
                file_id=source_file.file_id,
                original_name=original_name,
                final_name=target_name,
                status=FileProcessingStatus.FAILED_DOWNLOAD,
                error_message=str(error),
            )

        email_attempts = 0
        email_error_message: str | None = None

        for _ in range(max_email_retries):
            email_attempts += 1
            try:
                self._email_gateway.send_epub(filename=target_name, content=file_content)
                email_error_message = None
                break
            except Exception as error:
                email_error_message = str(error)

        if email_error_message is not None:
            return FileProcessingResult(
                file_id=source_file.file_id,
                original_name=original_name,
                final_name=target_name,
                status=FileProcessingStatus.FAILED_EMAIL,
                email_attempts=email_attempts,
                error_message=email_error_message,
            )

        try:
            self._drive_gateway.move_file(
                file_id=source_file.file_id,
                destination_folder_id=processed_folder_id,
            )
        except Exception as error:
            return FileProcessingResult(
                file_id=source_file.file_id,
                original_name=original_name,
                final_name=target_name,
                status=FileProcessingStatus.FAILED_MOVE,
                email_attempts=email_attempts,
                error_message=str(error),
            )

        return FileProcessingResult(
            file_id=source_file.file_id,
            original_name=original_name,
            final_name=target_name,
            status=FileProcessingStatus.SUCCESS,
            email_attempts=email_attempts,
        )

    @staticmethod
    def _is_epub_file(filename: str) -> bool:
        return filename.lower().endswith(".epub")

    @staticmethod
    def _build_target_name(source_file: FileDescriptor, existing_names: set[str]) -> str:
        renamed_name = source_file.name.replace("_", " ")
        if renamed_name == source_file.name:
            return source_file.name

        unavailable_names = existing_names - {source_file.name}
        if renamed_name not in unavailable_names:
            return renamed_name

        stem, extension = SynchronizeEpubFilesUseCase._split_name_and_extension(renamed_name)

        sequence = 1
        while True:
            candidate = f"{stem}_{sequence:02d}{extension}"
            if candidate not in unavailable_names:
                return candidate
            sequence += 1

    @staticmethod
    def _split_name_and_extension(filename: str) -> tuple[str, str]:
        if "." not in filename:
            return filename, ""

        stem, extension = filename.rsplit(".", maxsplit=1)
        return stem, f".{extension}"
