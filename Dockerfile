# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

COPY frontend/ .
RUN npm run build


# ── Stage 2: Install Python dependencies ──────────────────────────────────────
FROM python:3.12-slim AS python-builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 3: Production runtime ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Python packages from builder
COPY --from=python-builder /install /usr/local

# Built React app → served by FastAPI as static files
COPY --from=frontend-builder /app/dist /app/static

# Non-root user
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Application source
COPY --chown=appuser:appuser app/ app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
