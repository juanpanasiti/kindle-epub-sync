"""Configuration loader for Google Drive synchronization settings."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DriveSyncSettings:
    """Resolved configuration values required by Drive infrastructure."""

    credentials_file: Path
    new_ebooks_folder_id: str
    synced_ebooks_folder_id: str


def load_drive_sync_settings(
    environment: Mapping[str, str],
    project_root: Path,
) -> DriveSyncSettings:
    """Load Drive settings from environment with deterministic fallback rules."""
    credentials_file = _resolve_credentials_file(environment=environment, project_root=project_root)

    new_ebooks_folder_id = environment.get("NEW_EBOOKS_FOLDER_ID")
    if not new_ebooks_folder_id:
        raise ValueError("Missing required environment variable: NEW_EBOOKS_FOLDER_ID")

    synced_ebooks_folder_id = environment.get("SYNCED_EBOOKS_FOLDER_ID")
    if not synced_ebooks_folder_id:
        raise ValueError("Missing required environment variable: SYNCED_EBOOKS_FOLDER_ID")

    return DriveSyncSettings(
        credentials_file=credentials_file,
        new_ebooks_folder_id=new_ebooks_folder_id,
        synced_ebooks_folder_id=synced_ebooks_folder_id,
    )


def _resolve_credentials_file(
    environment: Mapping[str, str],
    project_root: Path,
) -> Path:
    configured_credentials_path = environment.get("CREDENTIALS_FILE")

    if configured_credentials_path:
        credentials_file = Path(configured_credentials_path)
        if not credentials_file.is_absolute():
            credentials_file = project_root / credentials_file
    else:
        credentials_file = project_root / "credentials.json"

    if not credentials_file.exists():
        raise ValueError(f"Credentials file was not found: {credentials_file}")

    return credentials_file
