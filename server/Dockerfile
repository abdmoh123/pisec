# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.13.5-python3.14-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=0 \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Create and switch to work directory
WORKDIR /app

# Installs dependencies via uv venv 
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# Copies the source code in and installs it
COPY . ./
RUN uv sync --locked

# Create a non-root system user (/app becomes readonly)
RUN useradd --system --no-create-home pisec-server

# Create data directory with permissions
ENV VIDEO_DIR=/data/videos/
RUN mkdir -p "$VIDEO_DIR" && chown pisec-server "$VIDEO_DIR"

USER pisec-server

# Set env variables relating to project itself
ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE ${PORT}

# Run FastAPI server
CMD exec pisec-server --host "$HOST" --port "$PORT"
