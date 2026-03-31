"""Unit tests for Drive settings loading rules."""

from pathlib import Path

import pytest

from kindle_epub_sync.infrastructure.google_drive.settings import load_drive_sync_settings


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


def test_loads_settings_from_env_path_relative_to_project_root(project_root: Path) -> None:
    credentials_file = project_root / "secrets" / "service-account.json"
    credentials_file.parent.mkdir(parents=True)
    credentials_file.write_text("{}", encoding="utf-8")

    settings = load_drive_sync_settings(
        environment={
            "CREDENTIALS_FILE": "secrets/service-account.json",
            "NEW_EBOOKS_FOLDER_ID": "source-folder",
            "SYNCED_EBOOKS_FOLDER_ID": "processed-folder",
        },
        project_root=project_root,
    )

    assert settings.credentials_file == credentials_file
    assert settings.new_ebooks_folder_id == "source-folder"
    assert settings.synced_ebooks_folder_id == "processed-folder"


def test_uses_default_credentials_path_when_env_var_is_missing(project_root: Path) -> None:
    credentials_file = project_root / "credentials.json"
    credentials_file.write_text("{}", encoding="utf-8")

    settings = load_drive_sync_settings(
        environment={
            "NEW_EBOOKS_FOLDER_ID": "source-folder",
            "SYNCED_EBOOKS_FOLDER_ID": "processed-folder",
        },
        project_root=project_root,
    )

    assert settings.credentials_file == credentials_file


def test_raises_when_credentials_file_does_not_exist(project_root: Path) -> None:
    with pytest.raises(ValueError, match="Credentials file was not found"):
        load_drive_sync_settings(
            environment={
                "CREDENTIALS_FILE": "missing.json",
                "NEW_EBOOKS_FOLDER_ID": "source-folder",
                "SYNCED_EBOOKS_FOLDER_ID": "processed-folder",
            },
            project_root=project_root,
        )


def test_raises_when_source_folder_id_is_missing(project_root: Path) -> None:
    credentials_file = project_root / "credentials.json"
    credentials_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="NEW_EBOOKS_FOLDER_ID"):
        load_drive_sync_settings(
            environment={"SYNCED_EBOOKS_FOLDER_ID": "processed-folder"},
            project_root=project_root,
        )


def test_raises_when_processed_folder_id_is_missing(project_root: Path) -> None:
    credentials_file = project_root / "credentials.json"
    credentials_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="SYNCED_EBOOKS_FOLDER_ID"):
        load_drive_sync_settings(
            environment={"NEW_EBOOKS_FOLDER_ID": "source-folder"},
            project_root=project_root,
        )
