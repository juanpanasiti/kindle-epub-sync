"""Integration tests for Stage 5 CLI entrypoint behavior."""

import pytest

from kindle_epub_sync.domain.entities.processing_report import SynchronizationReport
from kindle_epub_sync.entrypoints import cli


def test_stage5_cli_supports_json_report_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeUseCase:
        def execute(
            self,
            command: object,
        ) -> SynchronizationReport:
            return SynchronizationReport(results=[])

    class FakeContext:
        def __init__(self) -> None:
            self.use_case = FakeUseCase()
            self.command = object()
            self.runtime_settings = type("Runtime", (), {"sync_interval_minutes": 5})()

    monkeypatch.setattr(
        "kindle_epub_sync.entrypoints.cli.build_application_context",
        lambda: FakeContext(),
    )

    exit_code = cli.main(argv=["run", "--json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"total_files": 0' in output
    assert '"results": []' in output
