"""Google Drive implementation for the DriveGateway port."""

from collections.abc import Sequence
from typing import Any

from kindle_epub_sync.application.ports.drive_gateway import DriveGateway
from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor


class GoogleDriveGateway(DriveGateway):
    """Adapter that maps Drive API operations into application port methods."""

    def __init__(self, drive_service: Any) -> None:
        self._drive_service = drive_service

    def list_files(self, folder_id: str) -> Sequence[FileDescriptor]:
        query = f"'{folder_id}' in parents and trashed = false"
        fields = "nextPageToken, files(id, name)"

        file_descriptors: list[FileDescriptor] = []
        page_token: str | None = None

        while True:
            response = (
                self._drive_service.files()
                .list(
                    q=query,
                    fields=fields,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    pageToken=page_token,
                )
                .execute()
            )

            for file_metadata in response.get("files", []):
                file_descriptors.append(
                    FileDescriptor(
                        file_id=file_metadata["id"],
                        name=file_metadata["name"],
                    ),
                )

            page_token = response.get("nextPageToken")
            if page_token is None:
                return file_descriptors

    def download_file(self, file_id: str) -> bytes:
        response = self._drive_service.files().get_media(fileId=file_id).execute()
        if isinstance(response, bytes):
            return response
        raise ValueError(f"Unexpected download payload type: {type(response)!r}")

    def rename_file(self, file_id: str, new_name: str) -> None:
        (
            self._drive_service.files()
            .update(
                fileId=file_id,
                body={"name": new_name},
                supportsAllDrives=True,
            )
            .execute()
        )

    def move_file(self, file_id: str, destination_folder_id: str) -> None:
        file_metadata = (
            self._drive_service.files()
            .get(
                fileId=file_id,
                fields="parents",
                supportsAllDrives=True,
            )
            .execute()
        )

        current_parent_ids = file_metadata.get("parents", [])
        remove_parents = ",".join(current_parent_ids)

        (
            self._drive_service.files()
            .update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=remove_parents,
                supportsAllDrives=True,
            )
            .execute()
        )
