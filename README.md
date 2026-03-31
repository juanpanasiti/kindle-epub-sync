# Kindle EPUB Sync

Python 3.14 application managed with `uv`.

## Stage 1 Scope

Stage 1 establishes the engineering baseline for the project:

- `src/` package layout aligned with Clean Architecture boundaries.
- Testing setup with `pytest`, including unit and integration suites.
- Static analysis setup with `ruff` and `mypy`.
- A minimal package entrypoint to keep the project executable during incremental delivery.

## Architecture Skeleton

The source package is organized under `src/kindle_epub_sync/`:

- `domain/entities/`: Enterprise entities and core business structures.
- `application/use_cases/`: Application-specific orchestration logic.
- `application/ports/`: Contracts used to decouple use cases from external systems.
- `adapters/`: Translators between ports and concrete implementations.
- `infrastructure/`: Concrete implementations for external services.
- `entrypoints/`: CLI and scheduler entrypoints.

## Development Commands

Install runtime and development dependencies:

```bash
uv sync --group dev
```

Run tests (unit + integration):

```bash
uv run --group dev pytest
```

Run linting:

```bash
uv run --group dev ruff check .
```

Run type checking:

```bash
uv run --group dev mypy .
```

## Test Strategy Baseline

- Unit tests mirror package modules under `tests/unit/`.
- Integration tests are grouped by functionality under `tests/integration/`.
- Both suites run in the default `pytest` execution path.

## Stage 2 Scope

Stage 2 introduces the core business flow in the inner architecture:

- Domain entities for source file metadata and synchronization reports.
- Application ports to decouple Google Drive and email delivery concerns.
- Use case orchestration for list, rename, email, and move steps.
- Retry policy for email failures (up to `max_email_retries`, default `3`).

### Stage 2 Behavior Rules

- EPUB detection is case-insensitive (`.epub`, `.EPUB`, etc.).
- Every EPUB is processed, including filenames without underscores.
- Renaming replaces underscores with spaces.
- When the renamed target collides, the use case appends an incremental suffix before extension: `_01`, `_02`, ...
- If email fails after all retries, processing continues with the next file.
- Files are moved only after successful email delivery.

### Stage 2 Report Model

The use case returns a structured `SynchronizationReport` with per-file outcomes:

- `success`
- `skipped_non_epub`
- `failed_rename`
- `failed_download`
- `failed_email`
- `failed_move`

Aggregate counters are available through:

- `total_files`
- `succeeded`
- `failed`
- `skipped`

## Stage 3 Scope

Stage 3 adds the Google Drive infrastructure layer with Service Account support:

- Authenticated Drive service factory based on `google-api-python-client` and `google-auth`.
- `GoogleDriveGateway` adapter implementing `DriveGateway`.
- Configuration loader for credentials path and source/destination Drive folder IDs.

### Stage 3 Configuration Rules

- `CREDENTIALS_FILE` points to a Service Account JSON file.
- If `CREDENTIALS_FILE` is missing, credentials default to `credentials.json` in project root.
- `NEW_EBOOKS_FOLDER_ID` is required and identifies source folder.
- `SYNCED_EBOOKS_FOLDER_ID` is required and identifies destination folder.

### Stage 3 Drive Adapter Behavior

- `list_files`: lists files from the source folder and excludes trashed files.
- `download_file`: returns raw file bytes for email delivery.
- `rename_file`: updates file name in Drive.
- `move_file`: adds destination parent and removes current parents.

All Stage 3 behavior is covered with unit and integration tests using test doubles, without calling
Google services in the automated test suite.

## Stage 4 Scope

Stage 4 adds the SMTP email infrastructure used to deliver EPUB files to Kindle:

- SMTP settings loader from environment variables.
- Gmail-friendly defaults for host and port.
- `SmtpEmailGateway` adapter implementing `EmailGateway`.

### Stage 4 Configuration Rules

- `KINDLE_EMAIL` is required.
- `SMTP_USER` is required.
- `SMTP_PASSWORD` is required.
- `SMTP_HOST` is optional and defaults to `smtp.gmail.com`.
- `SMTP_PORT` is optional and defaults to `587`.

### Stage 4 SMTP Adapter Behavior

- Uses STARTTLS with SMTP authentication.
- Sends one EPUB attachment per message.
- Uses `SMTP_USER` as sender and `KINDLE_EMAIL` as recipient.
- Subject and body are minimal, because Kindle processing depends on the attachment.

## Stage 5 Scope

Stage 5 introduces runtime entrypoints for manual execution and periodic scheduling:

- CLI command for one-time synchronization (`run`).
- Scheduler command for continuous execution (`schedule`).
- Automatic environment loading from `.env`.
- Runtime interval configuration via environment variables.

### Stage 5 Runtime Rules

- `kindle-epub-sync run`: executes one synchronization cycle.
- `kindle-epub-sync schedule`: runs one immediate synchronization and then repeats.
- `SYNC_INTERVAL_MINUTES` controls schedule frequency and defaults to `5`.
- `--json` is available for both commands to print structured report output.

## Stage 6 Scope

Stage 6 provides containerized runtime with automatic restart behavior:

- Docker image based on `python:3.14-slim`.
- Runtime dependency installation through `uv` in container build.
- Default container command runs scheduler entrypoint.
- Compose service configured with restart policy.

### Stage 6 Container Files

- `Dockerfile`: installs `uv`, syncs runtime dependencies, and runs `kindle-epub-sync schedule`.
- `docker-compose.yml`: loads `.env`, mounts `credentials.json` read-only, and sets `restart: unless-stopped`.
- `.dockerignore`: excludes local secrets and development artifacts from build context.

### Stage 6 Usage

Build image:

```bash
docker build -t kindle-epub-sync .
```

Run with compose (recommended):

```bash
docker compose up -d --build
```

Run a one-time manual sync in container:

```bash
docker compose run --rm kindle-epub-sync uv run kindle-epub-sync run
```
