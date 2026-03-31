"""Integration tests for Stage 6 containerization artifacts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_stage6_dockerfile_uses_uv_and_scheduler_command() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.14-slim" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert "CMD [\"uv\", \"run\", \"kindle-epub-sync\", \"schedule\"]" in dockerfile


def test_stage6_compose_has_restart_policy_and_env_file() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "restart: unless-stopped" in compose
    assert "env_file:" in compose
    assert "- .env" in compose
    assert "credentials.json:/app/credentials.json:ro" in compose


def test_stage6_dockerignore_excludes_local_secrets() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert ".env" in dockerignore
    assert "credentials.json" in dockerignore
