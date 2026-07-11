FROM python:3.12-slim

WORKDIR /app

# ── System deps ────────────────────────────────────────────────────────────
# curl  — used by HEALTHCHECK
# build-essential / libmupdf-dev — required by PyMuPDF (fitz) compilation
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libmupdf-dev \
        libfreetype6-dev \
 && rm -rf /var/lib/apt/lists/*

# ── Python deps — backend ─────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Python deps — ingestion (optional; install if requirements exist) ──────
COPY ../ingestion/requirements.txt /tmp/ingestion-requirements.txt
RUN pip install --no-cache-dir -r /tmp/ingestion-requirements.txt || \
    echo "Warning: ingestion requirements not found; skipping."

# ── Copy source code ──────────────────────────────────────────────────────
COPY app/ ./app/

# Copy the ingestion package so kb_startup can invoke it as a module.
# movie_scripts/ and chroma_db/ are mounted as Docker volumes at runtime;
# they are NOT baked into the image.
COPY ../ingestion/ ./ingestion/

# ── Create runtime directories ────────────────────────────────────────────
# These are empty placeholders; actual data comes from Docker volumes.
RUN mkdir -p /data/movie_scripts /data/chroma_db /data/logs

# ── Environment ───────────────────────────────────────────────────────────
ENV PROJECT_ROOT=/app \
    MOVIE_SCRIPTS_DIR=/data/movie_scripts \
    CHROMA_DB_DIR=/data/chroma_db \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ── Non-root user ─────────────────────────────────────────────────────────
RUN useradd -m appuser \
 && chown -R appuser /app /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
