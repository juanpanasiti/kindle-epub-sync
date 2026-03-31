"""Unit tests for SMTP settings loading rules."""

import pytest

from kindle_epub_sync.infrastructure.email.settings import (
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    load_email_settings,
)


def test_loads_required_smtp_settings_with_defaults() -> None:
    settings = load_email_settings(
        environment={
            "KINDLE_EMAIL": "reader@kindle.com",
            "SMTP_USER": "sender@example.com",
            "SMTP_PASSWORD": "app-password",
        },
    )

    assert settings.kindle_email == "reader@kindle.com"
    assert settings.smtp_user == "sender@example.com"
    assert settings.smtp_password == "app-password"
    assert settings.smtp_host == DEFAULT_SMTP_HOST
    assert settings.smtp_port == DEFAULT_SMTP_PORT


def test_overrides_default_host_and_port_when_present() -> None:
    settings = load_email_settings(
        environment={
            "KINDLE_EMAIL": "reader@kindle.com",
            "SMTP_USER": "sender@example.com",
            "SMTP_PASSWORD": "app-password",
            "SMTP_HOST": "mail.example.com",
            "SMTP_PORT": "2525",
        },
    )

    assert settings.smtp_host == "mail.example.com"
    assert settings.smtp_port == 2525


def test_raises_when_required_values_are_missing() -> None:
    with pytest.raises(ValueError, match="KINDLE_EMAIL"):
        load_email_settings(environment={})

    with pytest.raises(ValueError, match="SMTP_USER"):
        load_email_settings(environment={"KINDLE_EMAIL": "reader@kindle.com"})

    with pytest.raises(ValueError, match="SMTP_PASSWORD"):
        load_email_settings(
            environment={
                "KINDLE_EMAIL": "reader@kindle.com",
                "SMTP_USER": "sender@example.com",
            },
        )


def test_raises_when_smtp_port_is_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid SMTP_PORT"):
        load_email_settings(
            environment={
                "KINDLE_EMAIL": "reader@kindle.com",
                "SMTP_USER": "sender@example.com",
                "SMTP_PASSWORD": "app-password",
                "SMTP_PORT": "not-a-number",
            },
        )

    with pytest.raises(ValueError, match="positive integer"):
        load_email_settings(
            environment={
                "KINDLE_EMAIL": "reader@kindle.com",
                "SMTP_USER": "sender@example.com",
                "SMTP_PASSWORD": "app-password",
                "SMTP_PORT": "0",
            },
        )
