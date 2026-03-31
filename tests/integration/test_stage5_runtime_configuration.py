"""Integration tests for Stage 5 runtime configuration behavior."""

from kindle_epub_sync.entrypoints.settings import load_runtime_settings


def test_stage5_runtime_interval_defaults_to_five_minutes() -> None:
    settings = load_runtime_settings(environment={})
    assert settings.sync_interval_minutes == 5


def test_stage5_runtime_interval_reads_env_value() -> None:
    settings = load_runtime_settings(environment={"SYNC_INTERVAL_MINUTES": "12"})
    assert settings.sync_interval_minutes == 12
