"""Integration tests for Stage 3 Drive configuration loading behavior."""

from pathlib import Path

from kindle_epub_sync.infrastructure.google_drive.settings import load_drive_sync_settings


def test_stage3_loads_configuration_from_environment_and_project_root(tmp_path: Path) -> None:
    credentials_file = tmp_path / "credentials.json"
    credentials_file.write_text("{}", encoding="utf-8")

    settings = load_drive_sync_settings(
        environment={
            "NEW_EBOOKS_FOLDER_ID": "new-folder-id",
            "SYNCED_EBOOKS_FOLDER_ID": "synced-folder-id",
        },
        project_root=tmp_path,
    )

    assert settings.credentials_file == credentials_file
    assert settings.new_ebooks_folder_id == "new-folder-id"
    assert settings.synced_ebooks_folder_id == "synced-folder-id"
