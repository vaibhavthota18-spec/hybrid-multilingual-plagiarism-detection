# Multi-purpose Production Dockerfile for FastAPI Backend and RQ Worker
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TORCH_HOME=/app/storage/model_cache \
    HF_HOME=/app/storage/model_cache

WORKDIR /app

# Install system dependencies:
# - curl for health probes
# - chromium for headless print-to-pdf report export
# - Noto and Dejavu fonts for Indic (Devanagari, Telugu) and Latin Unicode typography
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    chromium \
    fonts-noto-core \
    fonts-deva \
    fonts-telu \
    fonts-dejavu \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copy build definition and install python dependencies
COPY pyproject.toml alembic.ini README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source code and migrations
COPY src ./src
COPY alembic ./alembic

# Ensure storage directories exist and assign ownership
RUN mkdir -p /app/storage/uploads /app/storage/reports /app/storage/private /app/storage/model_cache && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "plagiarism.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
