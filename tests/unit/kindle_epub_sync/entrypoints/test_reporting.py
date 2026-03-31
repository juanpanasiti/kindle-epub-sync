"""Unit tests for synchronization report rendering."""

from kindle_epub_sync.domain.entities.processing_report import (
    FileProcessingResult,
    FileProcessingStatus,
    SynchronizationReport,
)
from kindle_epub_sync.entrypoints.reporting import (
    render_report_as_json,
    render_report_as_text,
)


def _build_report() -> SynchronizationReport:
    return SynchronizationReport(
        results=[
            FileProcessingResult(
                file_id="1",
                original_name="A_Book.epub",
                final_name="A Book.epub",
                status=FileProcessingStatus.SUCCESS,
                email_attempts=1,
            ),
            FileProcessingResult(
                file_id="2",
                original_name="B.epub",
                final_name="B.epub",
                status=FileProcessingStatus.FAILED_EMAIL,
                email_attempts=3,
                error_message="smtp failed",
            ),
        ],
    )


def test_render_report_as_text_contains_summary_and_file_lines() -> None:
    output = render_report_as_text(report=_build_report())

    assert "Synchronization summary" in output
    assert "- total_files: 2" in output
    assert "status=success" in output
    assert "status=failed_email" in output
    assert "failed_step=failed_email" in output
    assert "error=smtp failed" in output


def test_render_report_as_json_contains_expected_fields() -> None:
    output = render_report_as_json(report=_build_report())

    assert '"total_files": 2' in output
    assert '"succeeded": 1' in output
    assert '"failed": 1' in output
    assert '"status": "failed_email"' in output
