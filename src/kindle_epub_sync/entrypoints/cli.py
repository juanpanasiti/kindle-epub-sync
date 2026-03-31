"""Command-line entrypoint for manual and scheduled synchronization."""

import argparse
import sys
from collections.abc import Sequence

from kindle_epub_sync.entrypoints.bootstrap import ApplicationContext, build_application_context
from kindle_epub_sync.entrypoints.reporting import render_report_as_json, render_report_as_text
from kindle_epub_sync.entrypoints.scheduler import start_scheduler


def main(argv: Sequence[str] | None = None) -> int:
    """Execute CLI command and return process exit code."""
    args = _parse_arguments(argv=argv)
    application_context = build_application_context()

    if args.command == "run":
        _run_once(application_context=application_context, as_json=args.json)
        return 0

    if args.command == "schedule":
        try:
            start_scheduler(
                interval_minutes=application_context.runtime_settings.sync_interval_minutes,
                run_once=lambda: _run_once(
                    application_context=application_context,
                    as_json=args.json,
                ),
            )
        except KeyboardInterrupt:
            print("Scheduler stopped by user.", file=sys.stderr)
            return 0
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="kindle-epub-sync",
        description="Synchronize EPUB files from Google Drive to Kindle delivery.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one synchronization cycle")
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print synchronization report in JSON format",
    )

    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Run synchronization in a periodic scheduler loop",
    )
    schedule_parser.add_argument(
        "--json",
        action="store_true",
        help="Print synchronization report in JSON format",
    )

    return parser.parse_args(list(argv) if argv is not None else None)


def _run_once(application_context: ApplicationContext, as_json: bool) -> None:
    report = application_context.use_case.execute(application_context.command)
    output = render_report_as_json(report) if as_json else render_report_as_text(report)
    print(output)

    processed_ebooks = report.succeeded + report.failed
    if processed_ebooks == 0:
        return

    subject = "Kindle EPUB sync execution summary"
    body = render_report_as_text(report)

    try:
        application_context.email_gateway.send_admin_notification(subject=subject, body=body)
    except Exception as error:
        print(f"Admin notification failed: {error}", file=sys.stderr)
