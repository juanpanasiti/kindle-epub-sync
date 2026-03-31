"""Runtime settings for CLI and scheduler behavior."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_SYNC_INTERVAL_MINUTES = 5


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Settings that control runtime orchestration behavior."""

    sync_interval_minutes: int = DEFAULT_SYNC_INTERVAL_MINUTES


def load_runtime_settings(environment: Mapping[str, str]) -> RuntimeSettings:
    """Load runtime settings from environment variables."""
    sync_interval_minutes = _parse_interval_minutes(
        raw_value=environment.get("SYNC_INTERVAL_MINUTES"),
    )
    return RuntimeSettings(sync_interval_minutes=sync_interval_minutes)


def _parse_interval_minutes(raw_value: str | None) -> int:
    if raw_value is None or raw_value == "":
        return DEFAULT_SYNC_INTERVAL_MINUTES

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"Invalid SYNC_INTERVAL_MINUTES value: {raw_value}") from error

    if value <= 0:
        raise ValueError("Invalid SYNC_INTERVAL_MINUTES value: must be a positive integer")

    return value
