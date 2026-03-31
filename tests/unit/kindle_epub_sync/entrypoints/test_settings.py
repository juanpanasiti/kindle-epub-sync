"""Unit tests for runtime settings parsing."""

import pytest

from kindle_epub_sync.entrypoints.settings import (
    DEFAULT_SYNC_INTERVAL_MINUTES,
    load_runtime_settings,
)


def test_uses_default_interval_when_env_var_is_missing() -> None:
    settings = load_runtime_settings(environment={})
    assert settings.sync_interval_minutes == DEFAULT_SYNC_INTERVAL_MINUTES


def test_reads_interval_from_environment() -> None:
    settings = load_runtime_settings(environment={"SYNC_INTERVAL_MINUTES": "7"})
    assert settings.sync_interval_minutes == 7


def test_rejects_invalid_interval_values() -> None:
    with pytest.raises(ValueError, match="Invalid SYNC_INTERVAL_MINUTES"):
        load_runtime_settings(environment={"SYNC_INTERVAL_MINUTES": "abc"})

    with pytest.raises(ValueError, match="positive integer"):
        load_runtime_settings(environment={"SYNC_INTERVAL_MINUTES": "0"})
