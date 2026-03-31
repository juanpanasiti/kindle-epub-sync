"""Report rendering helpers for CLI output."""

import json
from dataclasses import asdict

from kindle_epub_sync.domain.entities.processing_report import (
    FileProcessingResult,
    SynchronizationReport,
)


def render_report_as_text(report: SynchronizationReport) -> str:
    """Render a synchronization report as a human-readable text block."""
    lines = [
        "Synchronization summary",
        f"- total_files: {report.total_files}",
        f"- succeeded: {report.succeeded}",
        f"- failed: {report.failed}",
        f"- skipped: {report.skipped}",
        "File results:",
    ]

    for result in report.results:
        lines.append(_render_file_result(result=result))

    return "\n".join(lines)


def render_report_as_json(report: SynchronizationReport) -> str:
    """Render a synchronization report as JSON."""
    payload = {
        "total_files": report.total_files,
        "succeeded": report.succeeded,
        "failed": report.failed,
        "skipped": report.skipped,
        "results": [asdict(result) for result in report.results],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _render_file_result(result: FileProcessingResult) -> str:
    parts = [
        f"- file_id={result.file_id}",
        f"status={result.status}",
        f"original_name={result.original_name}",
        f"final_name={result.final_name}",
        f"email_attempts={result.email_attempts}",
    ]
    if result.error_message:
        parts.append(f"error={result.error_message}")
    return " | ".join(parts)
