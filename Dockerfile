# ===== build stage =====
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project


# ===== runtime stage =====
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY --from=builder /root/.cache /root/.cache

COPY . .

RUN cp .env.example .env

CMD ["uv", "run", "freebuff2api"]
