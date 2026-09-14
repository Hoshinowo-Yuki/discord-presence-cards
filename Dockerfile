FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # compile bytecode at build time for faster container startup
    UV_COMPILE_BYTECODE=1 \
    # copy packages into the venv rather than symlinking to the cache
    UV_LINK_MODE=copy

WORKDIR /app

# deps layer: only rebuilds when lock/pyproject change
COPY pyproject.toml uv.lock README.md ./
# no-install-project: install deps only, not your code yet (keeps this layer stable)
RUN uv sync --frozen --no-dev --no-install-project

# project layer: rebuilds on code edits, but deps above stay cached
COPY src/ ./src/
RUN uv sync --frozen --no-dev

EXPOSE 8000

# uv sync builds a .venv; run through `uv run` so it's used automatically. No --reload in prod.
CMD ["uv", "run", "uvicorn", "presence_cards.main:app", "--host", "0.0.0.0", "--port", "8000"]