"""Unit tests for scheduler loop orchestration."""

from collections.abc import Callable

import pytest

from kindle_epub_sync.entrypoints.scheduler import start_scheduler


class FakeScheduledJob:
    def __init__(self) -> None:
        self.registered_callback: Callable[[], None] | None = None

    @property
    def minutes(self) -> FakeScheduledJob:
        return self

    def do(self, callback: Callable[[], None]) -> FakeScheduledJob:
        self.registered_callback = callback
        return self


class FakeScheduler:
    def __init__(self) -> None:
        self.every_calls: list[int] = []
        self.run_pending_calls = 0
        self.job = FakeScheduledJob()

    def every(self, interval: int) -> FakeScheduledJob:
        self.every_calls.append(interval)
        return self.job

    def run_pending(self) -> None:
        self.run_pending_calls += 1


def test_start_scheduler_runs_immediately_and_registers_periodic_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_scheduler = FakeScheduler()
    run_once_calls: list[str] = []

    def run_once() -> None:
        run_once_calls.append("run")

    def stop_scheduler(_seconds: int) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr("kindle_epub_sync.entrypoints.scheduler.time.sleep", stop_scheduler)

    try:
        start_scheduler(
            interval_minutes=5,
            run_once=run_once,
            sleep_seconds=0,
            scheduler=fake_scheduler,
        )
        raise AssertionError("Expected KeyboardInterrupt")
    except KeyboardInterrupt:
        pass

    assert run_once_calls == ["run"]
    assert fake_scheduler.every_calls == [5]
    assert fake_scheduler.job.registered_callback is run_once
    assert fake_scheduler.run_pending_calls == 1
