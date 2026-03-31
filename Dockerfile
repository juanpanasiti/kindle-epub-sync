FROM python:3.14-slim

# Keep Python deterministic and avoid writing .pyc files in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl only to bootstrap uv, then remove apt metadata in same layer.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy lock and metadata first to maximize Docker layer cache reuse.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install only runtime dependencies and project package.
RUN uv sync --frozen --no-dev

# The scheduler command performs one immediate run and then loops.
CMD ["uv", "run", "kindle-epub-sync", "schedule"]
