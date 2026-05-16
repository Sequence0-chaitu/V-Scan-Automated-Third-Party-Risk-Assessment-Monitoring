FROM python:3.12-slim

# ── System dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ──────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ───────────────────────────────────────────────────────
COPY src/ ./src/
COPY questionnaire.json .

# ── Data directory for SQLite ────────────────────────────────────────────────
RUN mkdir -p /app/data

# ── Expose web port ──────────────────────────────────────────────────────────
EXPOSE 8000

# ── Default: run the web server (CLI still available via docker exec) ─────────
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
