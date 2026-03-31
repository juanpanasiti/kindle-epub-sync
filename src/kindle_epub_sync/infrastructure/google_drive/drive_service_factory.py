"""Factory functions that build authenticated Google Drive service clients."""

from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


def build_drive_service(credentials_file: Path) -> Any:
    """Create a Google Drive API client authenticated via service account."""
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_file),
        scopes=[DRIVE_SCOPE],
    )  # type: ignore[no-untyped-call]
    return build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )
