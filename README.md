# V-Scan — Automated Third-Party Risk Assessment Platform

**A GRC-focused security tool that evaluates vendor risk against ISO 27001 and NIST CSF controls, combining automated technical scanning with structured compliance questionnaires.**

---

## 1. Overview

Organizations are required — under frameworks like **ISO 27001 (A.15 Supplier Relationships)** and the **NIST Cybersecurity Framework**, and by regulations such as **GDPR Art. 28** and **SOC 2 CC9** — to assess the security posture of third-party vendors before onboarding and periodically thereafter.

**V-Scan automates the first pass of that assessment.** It scans a vendor's public-facing infrastructure for baseline security hygiene (HTTP security headers, SSL/TLS configuration) and combines those objective, automated findings with a structured compliance questionnaire, producing a single risk score and risk tier that mirrors how a real TPRM analyst would triage a vendor.

---

## 2. Key Features

- **Automated technical checks** — 9 checks covering HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) and SSL/TLS certificate configuration
- **Compliance questionnaire scoring** — 11 controls mapped to ISO 27001 and NIST CSF (e.g. encryption at rest, MFA enforcement)
- **Weighted risk scoring engine** — produces a 0–100 score and a risk tier (LOW / MEDIUM / HIGH / CRITICAL)
- **Web dashboard** — submit scans, view live progress, and review a per-control breakdown with control references, without touching a terminal
- **REST API** — enables integration into a broader vendor onboarding workflow or ticketing system
- **Historical trending via Grafana** — supports periodic reassessment and tracking of a vendor's risk posture over time
- **CLI** — for scripted or batch scanning

---

## 3. Compliance Mapping

| Category | Framework Reference | What V-Scan Checks |
|---|---|---|
| Supplier security | ISO 27001 A.5.19–A.5.23 | Encryption, access control, incident notification (via questionnaire) |
| Protect function | NIST CSF PR.AC, PR.DS | MFA enforcement, encryption at rest/in transit |
| Transport security | ISO 27001 A.8.24 | TLS/SSL configuration, certificate validity |
| Secure configuration | NIST CSF PR.PT | HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) |

Each finding in the dashboard is tagged with its corresponding control reference, so results can be traced directly back to the framework requirement they support.

---

## 4. Risk Scoring Methodology

| Source | Checks | Points Each | Max Points |
|---|---|---|---|
| Automated (headers + SSL) | 9 | 5 | 45 |
| Questionnaire (ISO 27001 / NIST CSF) | 11 | 5 | 55 |
| **Total** | | | **100** |

| Score Range | Risk Level |
|---|---|
| ≥ 80 | LOW |
| 60 – 79 | MEDIUM |
| 40 – 59 | HIGH |
| < 40 | CRITICAL |

The 45/55 split is intentional: automated checks alone cannot confirm internal controls (e.g. whether MFA is actually enforced), so questionnaire attestations carry slightly more weight — consistent with how real TPRM programs treat self-reported controls as necessary but requiring independent validation over time.

---

## 5. Architecture

```
vscan/
├── scanner-app/
│   ├── src/
│   │   ├── main.py          # CLI entrypoint (Click)
│   │   ├── web_server.py    # FastAPI web server
│   │   ├── dashboard.html   # Web dashboard UI
│   │   ├── scanner.py       # HTTP header & SSL/TLS checks
│   │   ├── scoring.py       # Risk scoring engine
│   │   └── database.py      # SQLite persistence
│   ├── questionnaire.json   # Default questionnaire values
│   ├── requirements.txt
│   └── Dockerfile
├── grafana/                 # Provisioning & dashboards for historical trends
├── scripts/                 # Utility scripts
├── docker-compose.yml
└── .env
```

**Tech stack:** Python 3.12, FastAPI, SQLite, Docker Compose, Grafana

---

## 6. Getting Started

### Prerequisites
- Docker & Docker Compose
- (Optional, for local CLI use) Python ≥ 3.12

### Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd vscan

# 2. (Optional) copy and edit environment variables
cp .env .env.local

# 3. Start all services
docker compose up --build -d

# 4. Open the dashboard
open http://localhost:8000
```

| Interface | URL | Purpose |
|---|---|---|
| Web Dashboard | `http://localhost:8000` | Submit scans, view live results, browse history |
| REST API | `http://localhost:8000/api/` | Programmatic access |
| Grafana | `http://localhost:3000` | Historical charts & compliance trend tracking |

---

## 7. Using the Web Dashboard

1. Enter a vendor URL in the scan input (e.g. `github.com`)
2. Optionally expand **"Configure Questionnaire Answers"** and toggle the controls the vendor has confirmed
3. Click **RUN SCAN** — checks run in real time with progress feedback
4. Review the result: overall score, risk tier badge, and a per-check breakdown with ISO 27001 / NIST CSF control references
5. Scan history at the bottom of the dashboard updates automatically, supporting periodic reassessment

---

## 8. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scan` | Submit a new scan |
| `GET` | `/api/scans?limit=50` | List recent scans |
| `GET` | `/api/scans/{id}/checks` | Full control-level breakdown for a scan |

**Example — submit a scan:**

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

**Response:**

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

## 9. CLI Usage

```bash
# Via Docker
docker exec -it scanner-app python src/main.py \
  --url https://example.com \
  --questionnaire /app/questionnaire.json

# Or locally, outside Docker
cd scanner-app
pip install -r requirements.txt
python src/main.py --url https://example.com
```

---

## 10. Configuration

| Variable | Default | Description |
|---|---|---|
| `SCANNER_PORT` | `8000` | Web dashboard port |
| `GRAFANA_PORT` | `3000` | Grafana port |
| `SQLITE_DB_PATH` | `/app/data/vscan.db` | Database path |
| `SCANNER_LOG_LEVEL` | `INFO` | Log verbosity |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana login |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana password |

---

## 11.Disclaimer

---

