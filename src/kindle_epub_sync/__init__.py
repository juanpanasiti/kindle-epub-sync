"""Public package entrypoints for kindle-epub-sync."""

from kindle_epub_sync.entrypoints.cli import main as cli_main


def main() -> None:
    """Run CLI entrypoint exposed by package script configuration."""
    raise SystemExit(cli_main())
