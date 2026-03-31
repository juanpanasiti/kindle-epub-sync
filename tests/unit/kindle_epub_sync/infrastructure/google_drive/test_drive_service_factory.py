"""Unit tests for the Google Drive service factory."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from kindle_epub_sync.infrastructure.google_drive.drive_service_factory import (
    DRIVE_SCOPE,
    build_drive_service,
)


def test_build_drive_service_creates_authenticated_v3_client() -> None:
    fake_credentials = MagicMock()
    credentials_file = Path("/tmp/credentials.json")

    with patch(
        "kindle_epub_sync.infrastructure.google_drive.drive_service_factory"
        ".service_account.Credentials.from_service_account_file",
        return_value=fake_credentials,
    ) as credentials_loader, patch(
        "kindle_epub_sync.infrastructure.google_drive.drive_service_factory.build",
        return_value=MagicMock(name="drive-service"),
    ) as build_function:
        drive_service = build_drive_service(credentials_file=credentials_file)

    credentials_loader.assert_called_once_with(
        str(credentials_file),
        scopes=[DRIVE_SCOPE],
    )
    build_function.assert_called_once_with(
        "drive",
        "v3",
        credentials=fake_credentials,
        cache_discovery=False,
    )
    assert drive_service is build_function.return_value
