# SocialForge - Multi-stage Dockerfile
# Stage 1: Build frontend with Bun
# Stage 2: Run backend + frontend with Python/uv + Node

# =============================================================================
# Stage 1: Frontend Build
# =============================================================================
FROM oven/bun:1-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile

COPY frontend/ ./
RUN bun run build

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.13-slim AS runtime

# Install Node.js for serving Next.js
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install backend dependencies
COPY backend/pyproject.toml backend/uv.lock* backend/README.md* ./
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# Copy backend source
COPY backend/app ./app

# Copy squad definitions
COPY socialforge/ ./socialforge/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/package.json ./frontend/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000 3333

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 & cd /app/frontend && npx next start -p 3333 -H 0.0.0.0 & wait"]
