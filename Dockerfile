# ---- build stage ----
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# --no-editable: build the wheel and COPY presence_cards into the venv's
# site-packages, instead of writing a .pth pointer to /app/src
RUN uv sync --frozen --no-dev --no-editable

# ---- runtime stage ----
FROM python:3.11-slim

RUN useradd --create-home --uid 1000 app

WORKDIR /app

# copy ONLY the venv — the package now lives inside it, so we don't need src/
COPY --from=builder --chown=app:app /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
CMD ["python", "-m", "presence_cards.main"]
