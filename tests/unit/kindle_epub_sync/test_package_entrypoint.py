"""Unit tests for package entrypoint behavior."""

import pytest

import kindle_epub_sync


def test_main_delegates_to_cli_and_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure package script executes CLI entrypoint and exits with its code."""
    monkeypatch.setattr("kindle_epub_sync.cli_main", lambda: 0)

    with pytest.raises(SystemExit, match="0"):
        kindle_epub_sync.main()
