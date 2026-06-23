# syntax=docker/dockerfile:1

# --- Builder: install dependencies with uv ---
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy everything the build backend needs (pyproject references README.md and
# the src/ package), then install the project + dependencies in one step.
COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache .

# --- Runtime ---
FROM python:3.13-slim AS runtime

# Run as non-root
RUN useradd --create-home --uid 1000 mourice
USER mourice

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

ENTRYPOINT ["mourice"]
