"""Configuration loader for SMTP email delivery settings."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587


@dataclass(frozen=True, slots=True)
class EmailSettings:
    """Resolved configuration values required by SMTP infrastructure."""

    kindle_email: str
    smtp_user: str
    smtp_password: str
    smtp_host: str = DEFAULT_SMTP_HOST
    smtp_port: int = DEFAULT_SMTP_PORT


def load_email_settings(environment: Mapping[str, str]) -> EmailSettings:
    """Load email settings from environment using safe defaults for Gmail."""
    kindle_email = environment.get("KINDLE_EMAIL")
    if not kindle_email:
        raise ValueError("Missing required environment variable: KINDLE_EMAIL")

    smtp_user = environment.get("SMTP_USER")
    if not smtp_user:
        raise ValueError("Missing required environment variable: SMTP_USER")

    smtp_password = environment.get("SMTP_PASSWORD")
    if not smtp_password:
        raise ValueError("Missing required environment variable: SMTP_PASSWORD")

    smtp_host = environment.get("SMTP_HOST", DEFAULT_SMTP_HOST)
    smtp_port = _parse_smtp_port(environment.get("SMTP_PORT"))

    return EmailSettings(
        kindle_email=kindle_email,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
    )


def _parse_smtp_port(raw_port: str | None) -> int:
    if raw_port is None or raw_port == "":
        return DEFAULT_SMTP_PORT

    try:
        smtp_port = int(raw_port)
    except ValueError as error:
        raise ValueError(f"Invalid SMTP_PORT value: {raw_port}") from error

    if smtp_port <= 0:
        raise ValueError("Invalid SMTP_PORT value: must be a positive integer")

    return smtp_port
