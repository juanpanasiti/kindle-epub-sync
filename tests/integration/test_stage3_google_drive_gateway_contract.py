"""Integration tests for Stage 3 Google Drive gateway contract behavior."""

from dataclasses import dataclass
from typing import Any

from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.infrastructure.google_drive.drive_gateway import GoogleDriveGateway


@dataclass(slots=True)
class FakeRequest:
    payload: Any

    def execute(self) -> Any:
        return self.payload


class FakeFilesResource:
    def __init__(self) -> None:
        self.list_payloads: list[dict[str, Any]] = [
            {
                "files": [{"id": "1", "name": "First.epub"}],
                "nextPageToken": "page-2",
            },
            {
                "files": [{"id": "2", "name": "Second.epub"}],
            },
        ]
        self.list_calls: list[dict[str, Any]] = []
        self.last_rename_call: dict[str, Any] | None = None
        self.last_move_call: dict[str, Any] | None = None

    def list(self, **kwargs: Any) -> FakeRequest:
        self.list_calls.append(kwargs)
        payload = self.list_payloads.pop(0)
        return FakeRequest(payload=payload)

    def get_media(self, **kwargs: Any) -> FakeRequest:
        return FakeRequest(payload=b"binary-epub")

    def get(self, **kwargs: Any) -> FakeRequest:
        return FakeRequest(payload={"parents": ["source-parent"]})

    def update(self, **kwargs: Any) -> FakeRequest:
        if "body" in kwargs:
            self.last_rename_call = kwargs
        else:
            self.last_move_call = kwargs
        return FakeRequest(payload={})


class FakeDriveService:
    def __init__(self) -> None:
        self.files_resource = FakeFilesResource()

    def files(self) -> FakeFilesResource:
        return self.files_resource


def test_stage3_gateway_contract_for_list_download_rename_and_move() -> None:
    gateway = GoogleDriveGateway(drive_service=FakeDriveService())

    listed_files = gateway.list_files(folder_id="source-folder")
    downloaded_payload = gateway.download_file(file_id="1")
    gateway.rename_file(file_id="1", new_name="Renamed.epub")
    gateway.move_file(file_id="1", destination_folder_id="processed-folder")

    assert listed_files == [
        FileDescriptor(file_id="1", name="First.epub"),
        FileDescriptor(file_id="2", name="Second.epub"),
    ]
    assert downloaded_payload == b"binary-epub"

    files_resource = gateway._drive_service.files()  # noqa: SLF001
    assert files_resource.last_rename_call == {
        "fileId": "1",
        "body": {"name": "Renamed.epub"},
        "supportsAllDrives": True,
    }
    assert files_resource.last_move_call == {
        "fileId": "1",
        "addParents": "processed-folder",
        "removeParents": "source-parent",
        "supportsAllDrives": True,
    }
