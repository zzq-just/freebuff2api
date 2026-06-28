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

# ⚠️ 关键：把 uv 也带进来
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# runtime 依赖
COPY --from=builder /usr/local /usr/local

COPY . .

RUN cp .env.example .env

CMD ["uv", "run", "freebuff2api"]
