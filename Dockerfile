# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim

RUN apt-get update && apt-get -y install build-essential

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

# Compile bytecode to speed up the application.
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install the project into `/app`
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD uv run gunicorn -c core/gunicorn_config.py
