FROM python:3.12-slim

WORKDIR /app

# System dependencies for Playwright, trafilatura, yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
COPY pyproject.toml ./
RUN uv sync --no-dev

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps || true

COPY src/ ./src/

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
