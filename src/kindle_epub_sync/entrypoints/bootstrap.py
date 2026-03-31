"""Dependency wiring helpers for CLI and scheduler entrypoints."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from kindle_epub_sync.application.use_cases.synchronize_epub_files import (
    SynchronizeEpubFilesCommand,
    SynchronizeEpubFilesUseCase,
)
from kindle_epub_sync.application.ports.email_gateway import EmailGateway
from kindle_epub_sync.entrypoints.settings import RuntimeSettings, load_runtime_settings
from kindle_epub_sync.infrastructure.email.settings import load_email_settings
from kindle_epub_sync.infrastructure.email.smtp_gateway import SmtpEmailGateway
from kindle_epub_sync.infrastructure.google_drive.drive_gateway import GoogleDriveGateway
from kindle_epub_sync.infrastructure.google_drive.drive_service_factory import build_drive_service
from kindle_epub_sync.infrastructure.google_drive.settings import load_drive_sync_settings


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Runtime object graph required by entrypoints."""

    use_case: SynchronizeEpubFilesUseCase
    command: SynchronizeEpubFilesCommand
    runtime_settings: RuntimeSettings
    email_gateway: EmailGateway


def build_application_context(
    project_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> ApplicationContext:
    """Build all dependencies needed by the CLI and scheduler commands."""
    resolved_project_root = project_root or _default_project_root()

    if environment is None:
        load_dotenv(dotenv_path=resolved_project_root / ".env", override=False)
        resolved_environment: Mapping[str, str] = os.environ
    else:
        resolved_environment = environment

    drive_settings = load_drive_sync_settings(
        environment=resolved_environment,
        project_root=resolved_project_root,
    )
    email_settings = load_email_settings(environment=resolved_environment)
    runtime_settings = load_runtime_settings(environment=resolved_environment)

    drive_service = build_drive_service(credentials_file=drive_settings.credentials_file)
    drive_gateway = GoogleDriveGateway(drive_service=drive_service)
    email_gateway = SmtpEmailGateway(settings=email_settings)

    use_case = SynchronizeEpubFilesUseCase(
        drive_gateway=drive_gateway,
        email_gateway=email_gateway,
    )
    command = SynchronizeEpubFilesCommand(
        source_folder_id=drive_settings.new_ebooks_folder_id,
        processed_folder_id=drive_settings.synced_ebooks_folder_id,
    )

    return ApplicationContext(
        use_case=use_case,
        command=command,
        runtime_settings=runtime_settings,
        email_gateway=email_gateway,
    )


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]
