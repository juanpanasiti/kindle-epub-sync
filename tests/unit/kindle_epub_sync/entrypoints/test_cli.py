"""Unit tests for CLI command behavior."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from kindle_epub_sync.domain.entities.processing_report import SynchronizationReport
from kindle_epub_sync.entrypoints import cli


@dataclass(slots=True)
class FakeUseCase:
    call_count: int = 0

    def execute(self, command: object) -> SynchronizationReport:
        self.call_count += 1
        return SynchronizationReport(results=[])


@dataclass(frozen=True, slots=True)
class FakeRuntimeSettings:
    sync_interval_minutes: int = 7


@dataclass(frozen=True, slots=True)
class FakeApplicationContext:
    use_case: FakeUseCase
    command: object
    runtime_settings: FakeRuntimeSettings


def test_run_command_executes_single_cycle(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_use_case = FakeUseCase()
    app_context = FakeApplicationContext(
        use_case=fake_use_case,
        command=object(),
        runtime_settings=FakeRuntimeSettings(sync_interval_minutes=9),
    )

    monkeypatch.setattr(
        "kindle_epub_sync.entrypoints.cli.build_application_context",
        lambda: app_context,
    )

    exit_code = cli.main(argv=["run"])

    assert exit_code == 0
    assert fake_use_case.call_count == 1
    assert "Synchronization summary" in capsys.readouterr().out


def test_schedule_command_uses_runtime_interval_and_stops_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_use_case = FakeUseCase()
    app_context = FakeApplicationContext(
        use_case=fake_use_case,
        command=object(),
        runtime_settings=FakeRuntimeSettings(sync_interval_minutes=11),
    )

    scheduler_calls: dict[str, Any] = {}

    def fake_scheduler_start(
        *,
        interval_minutes: int,
        run_once: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        scheduler_calls["interval_minutes"] = interval_minutes
        run_once()
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        "kindle_epub_sync.entrypoints.cli.build_application_context",
        lambda: app_context,
    )
    monkeypatch.setattr(
        "kindle_epub_sync.entrypoints.cli.start_scheduler",
        fake_scheduler_start,
    )

    exit_code = cli.main(argv=["schedule"])

    assert exit_code == 0
    assert scheduler_calls["interval_minutes"] == 11
    assert fake_use_case.call_count == 1
