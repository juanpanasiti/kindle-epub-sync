"""Unit tests that enforce the Clean Architecture package map."""

from importlib import import_module

EXPECTED_PACKAGES = [
    "kindle_epub_sync.domain",
    "kindle_epub_sync.domain.entities",
    "kindle_epub_sync.application",
    "kindle_epub_sync.application.use_cases",
    "kindle_epub_sync.application.ports",
    "kindle_epub_sync.adapters",
    "kindle_epub_sync.infrastructure",
    "kindle_epub_sync.entrypoints",
]


def test_clean_architecture_packages_are_importable() -> None:
    """Protect package boundaries by ensuring each planned layer exists."""
    for package_name in EXPECTED_PACKAGES:
        module = import_module(package_name)
        assert module is not None
