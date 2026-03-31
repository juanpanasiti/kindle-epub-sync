"""Scheduler runtime for periodic synchronization execution."""

import time
from collections.abc import Callable
from typing import Protocol

import schedule


class ScheduledJob(Protocol):
    """Represents a scheduler job handle that can register callbacks."""

    @property
    def minutes(self) -> ScheduledJob: ...

    def do(self, callback: Callable[[], None]) -> ScheduledJob: ...


class SchedulerLike(Protocol):
    """Represents minimal scheduler behavior needed by the runtime loop."""

    def every(self, interval: int) -> ScheduledJob: ...

    def run_pending(self) -> None: ...


def start_scheduler(
    interval_minutes: int,
    run_once: Callable[[], None],
    sleep_seconds: int = 1,
    scheduler: SchedulerLike | None = None,
) -> None:
    """Run one immediate synchronization and keep running periodically."""
    scheduler_instance = scheduler or schedule.Scheduler()

    run_once()
    scheduler_instance.every(interval_minutes).minutes.do(run_once)

    while True:
        scheduler_instance.run_pending()
        time.sleep(sleep_seconds)
