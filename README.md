# V-Scan — Third-Party Risk Assessment

Automated security scanner that checks vendor URLs for HTTP security headers, SSL/TLS configuration, and questionnaire-based compliance controls (ISO 27001 / NIST CSF).

---

## Web Dashboard

V-Scan ships with a built-in web dashboard so you can submit scans and view results directly in the browser — no terminal required(If in need of terminal usage,refer below as mentioned).

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Web Dashboard** | `http://localhost:8000` | Submit scans, view live results, browse history |
| **REST API** | `http://localhost:8000/api/` | Programmatic access (see endpoints below) |
| **Grafana** | `http://localhost:3000` | Historical charts & compliance trends |

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo> && cd vscan

# 2. (Optional) copy and edit environment variables
cp .env .env.local

# 3. Start all services
docker compose up --build -d

# 4. Open the dashboard
open http://localhost:8000
```

---

## Web Dashboard Usage

1. **Enter a vendor URL** in the scan input (e.g. `github.com`)
2. **Optionally configure questionnaire answers** by toggling *"Configure Questionnaire Answers"* — flip the switches for any controls the vendor has confirmed
3. **Click RUN SCAN** — the progress bar animates through each check in real time
4. **View the result** — score circle, risk badge (LOW / MEDIUM / HIGH / CRITICAL), and per-check breakdown with ISO 27001 and NIST CSF control references
5. **Scan history** at the bottom updates automatically after every scan

---

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scan` | Submit a new scan |
| `GET` | `/api/scans` | List recent scans (`?limit=50`) |
| `GET` | `/api/scans/{id}/checks` | Full check breakdown for a scan |

### POST /api/scan — example

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "questionnaire": {
      "encryption_at_rest": true,
      "mfa_enforced": true
    }
  }'
```

Response:
```json
{
  "scan_id": 1,
  "url": "https://example.com",
  "score": 35.0,
  "risk_level": "CRITICAL",
  "breakdown": [...]
}
```

---

## CLI (available)

The CLI is available via `docker exec`:

```bash
docker exec -it scanner-app python src/main.py \
  --url https://example.com \
  --questionnaire /app/questionnaire.json
```

Or run directly (outside Docker) with Python ≥ 3.12:

```bash
cd scanner-app
pip install -r requirements.txt
python src/main.py --url https://example.com
```

---

## Scoring

| Source | Checks | Points each | Max |
|--------|--------|-------------|-----|
| Automated (headers + SSL) | 9 | 5 | 45 |
| Questionnaire | 11 | 5 | 55 |
| **Total** | | | **100** |

| Score | Risk Level |
|-------|-----------|
| ≥ 80 | LOW |
| 60–79 | MEDIUM |
| 40–59 | HIGH |
| < 40 | CRITICAL |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCANNER_PORT` | `8000` | Web dashboard port |
| `GRAFANA_PORT` | `3000` | Grafana port |
| `SQLITE_DB_PATH` | `/app/data/vscan.db` | Database path |
| `SCANNER_LOG_LEVEL` | `INFO` | Log verbosity |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana login |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana password |

---

## Project Structure

```
vscan/
├── scanner-app/
│   ├── src/
│   │   ├── main.py          # CLI entrypoint (click)
│   │   ├── web_server.py    # FastAPI web server  ← NEW
│   │   ├── dashboard.html   # Web dashboard UI    ← NEW
│   │   ├── scanner.py       # HTTP header & SSL checks
│   │   ├── scoring.py       # Risk scoring engine
│   │   └── database.py      # SQLite persistence
│   ├── questionnaire.json   # Default questionnaire values
│   ├── requirements.txt
│   └── Dockerfile
├── grafana/                 # Grafana provisioning & dashboards
├── scripts/                 # Utility scripts
├── docker-compose.yml
└── .env
```
