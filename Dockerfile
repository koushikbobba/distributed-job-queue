# Multi-stage / Production-ready Python Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies (build-essential, libpq-dev for PostgreSQL, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (optimizes Docker layer caching)
COPY requirements/ /app/requirements/

# Install python dependencies for local/dev
RUN pip install --upgrade pip && \
    pip install -r requirements/local.txt

# Copy entrypoint scripts
COPY docker/entrypoints/ /app/docker/entrypoints/
RUN chmod +x /app/docker/entrypoints/*.sh

# Copy project code
COPY . /app/

# Default entrypoint for api
EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoints/api.sh"]
