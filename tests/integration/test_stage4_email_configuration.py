"""Integration tests for Stage 4 email configuration behavior."""

from kindle_epub_sync.infrastructure.email.settings import load_email_settings


def test_stage4_email_configuration_defaults_match_gmail() -> None:
    settings = load_email_settings(
        environment={
            "KINDLE_EMAIL": "reader@kindle.com",
            "SMTP_USER": "sender@example.com",
            "SMTP_PASSWORD": "app-password",
        },
    )

    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 587
