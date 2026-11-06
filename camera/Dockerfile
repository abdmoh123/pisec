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

# Create data directory with permissions
ENV DATA_DIR=/data/
RUN mkdir -p "$DATA_DIR"

# Run pisec-cam application
ENTRYPOINT [ "pisec-cam" ]
CMD []
