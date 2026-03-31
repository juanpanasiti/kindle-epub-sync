"""Integration tests for Stage 1 project bootstrap behavior."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_stage1_expected_paths_exist() -> None:
    """Verify that all required architectural roots are present together."""
    expected_paths = [
        ROOT / "src" / "kindle_epub_sync" / "domain" / "entities",
        ROOT / "src" / "kindle_epub_sync" / "application" / "use_cases",
        ROOT / "src" / "kindle_epub_sync" / "application" / "ports",
        ROOT / "src" / "kindle_epub_sync" / "adapters",
        ROOT / "src" / "kindle_epub_sync" / "infrastructure",
        ROOT / "src" / "kindle_epub_sync" / "entrypoints",
        ROOT / "tests" / "unit",
        ROOT / "tests" / "integration",
    ]

    for path in expected_paths:
        assert path.exists()
        assert path.is_dir()
