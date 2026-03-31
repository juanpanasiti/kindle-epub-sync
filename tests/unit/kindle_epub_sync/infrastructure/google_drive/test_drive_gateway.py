"""Unit tests for GoogleDriveGateway."""

from unittest.mock import MagicMock

import pytest

from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.infrastructure.google_drive.drive_gateway import GoogleDriveGateway


@pytest.fixture
def drive_service() -> MagicMock:
    return MagicMock(name="drive-service")


@pytest.fixture
def gateway(drive_service: MagicMock) -> GoogleDriveGateway:
    return GoogleDriveGateway(drive_service=drive_service)


def test_list_files_maps_metadata_into_file_descriptors(
    drive_service: MagicMock,
    gateway: GoogleDriveGateway,
) -> None:
    list_request_page_1 = MagicMock()
    list_request_page_1.execute.return_value = {
        "files": [{"id": "1", "name": "A.epub"}],
        "nextPageToken": "token-2",
    }
    list_request_page_2 = MagicMock()
    list_request_page_2.execute.return_value = {
        "files": [{"id": "2", "name": "B.epub"}],
    }

    drive_service.files.return_value.list.side_effect = [
        list_request_page_1,
        list_request_page_2,
    ]

    files = gateway.list_files(folder_id="source")

    assert files == [
        FileDescriptor(file_id="1", name="A.epub"),
        FileDescriptor(file_id="2", name="B.epub"),
    ]


def test_download_file_returns_bytes_payload(
    drive_service: MagicMock,
    gateway: GoogleDriveGateway,
) -> None:
    media_request = MagicMock()
    media_request.execute.return_value = b"epub-content"
    drive_service.files.return_value.get_media.return_value = media_request

    content = gateway.download_file(file_id="file-1")

    assert content == b"epub-content"


def test_download_file_raises_for_unexpected_payload_type(
    drive_service: MagicMock,
    gateway: GoogleDriveGateway,
) -> None:
    media_request = MagicMock()
    media_request.execute.return_value = "not-bytes"
    drive_service.files.return_value.get_media.return_value = media_request

    with pytest.raises(ValueError, match="Unexpected download payload type"):
        gateway.download_file(file_id="file-1")


def test_rename_file_updates_name(
    drive_service: MagicMock,
    gateway: GoogleDriveGateway,
) -> None:
    update_request = MagicMock()
    drive_service.files.return_value.update.return_value = update_request

    gateway.rename_file(file_id="file-1", new_name="new.epub")

    drive_service.files.return_value.update.assert_called_once_with(
        fileId="file-1",
        body={"name": "new.epub"},
        supportsAllDrives=True,
    )
    update_request.execute.assert_called_once_with()


def test_move_file_adds_destination_and_removes_current_parents(
    drive_service: MagicMock,
    gateway: GoogleDriveGateway,
) -> None:
    get_request = MagicMock()
    get_request.execute.return_value = {"parents": ["origin-a", "origin-b"]}

    update_request = MagicMock()

    drive_service.files.return_value.get.return_value = get_request
    drive_service.files.return_value.update.return_value = update_request

    gateway.move_file(file_id="file-1", destination_folder_id="destination")

    drive_service.files.return_value.get.assert_called_once_with(
        fileId="file-1",
        fields="parents",
        supportsAllDrives=True,
    )
    drive_service.files.return_value.update.assert_called_once_with(
        fileId="file-1",
        addParents="destination",
        removeParents="origin-a,origin-b",
        supportsAllDrives=True,
    )
    update_request.execute.assert_called_once_with()
