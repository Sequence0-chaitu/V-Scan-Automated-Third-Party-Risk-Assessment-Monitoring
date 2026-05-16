"""
web_server.py — FastAPI web interface for V-Scan
Provides REST API + serves the dashboard UI
"""

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from scanner import Scanner
from scoring import ScoringEngine
from database import Database

log = logging.getLogger("vscan.web")

DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/vscan.db")
Q_PATH = os.getenv("QUESTIONNAIRE_PATH", "/app/questionnaire.json")

app = FastAPI(title="V-Scan", description="Third-Party Risk Assessment API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ──────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str
    questionnaire: dict | None = None  # Optional override; uses default file if omitted


class ScanResponse(BaseModel):
    scan_id: int
    url: str
    score: float
    risk_level: str
    breakdown: list[dict]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_default_questionnaire() -> dict:
    try:
        with open(Q_PATH) as f:
            data = json.load(f)
        # Strip comments key
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except FileNotFoundError:
        log.warning("questionnaire.json not found at %s, using all-false defaults", Q_PATH)
        return {}


def _risk_level(score: float) -> str:
    if score >= 80:
        return "LOW"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "HIGH"
    return "CRITICAL"


# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "vscan"}


@app.post("/api/scan", response_model=ScanResponse)
async def run_scan(body: ScanRequest):
    """Submit a URL for security scanning."""
    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    log.info("Web scan requested: %s", url)

    # Run automated scan
    try:
        scanner = Scanner(url)
        scan_results = scanner.run()
    except Exception as exc:
        log.error("Scanner error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Scanner error: {exc}")

    # Score
    q_data = body.questionnaire if body.questionnaire else _load_default_questionnaire()
    engine = ScoringEngine(scan_results, q_data)
    score, breakdown = engine.calculate()

    # Persist
    try:
        db = Database(DB_PATH)
        scan_id = db.save_scan(url=url, score=score, results=scan_results, breakdown=breakdown)
    except Exception as exc:
        log.error("DB error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    return ScanResponse(
        scan_id=scan_id,
        url=url,
        score=round(score, 1),
        risk_level=_risk_level(score),
        breakdown=breakdown,
    )


@app.get("/api/scans")
async def list_scans(limit: int = 50):
    """Retrieve recent scans from the database."""
    try:
        db = Database(DB_PATH)
        scans = db.get_latest_scans(limit=limit)
        return {"scans": scans}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/scans/{scan_id}/checks")
async def get_scan_checks(scan_id: int):
    """Get check breakdown for a specific scan."""
    try:
        db = Database(DB_PATH)
        checks = db.get_scan_checks(scan_id)
        if not checks:
            raise HTTPException(status_code=404, detail="Scan not found")
        return {"scan_id": scan_id, "checks": checks}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Dashboard UI (served at /) ───────────────────────────────────────────────

DASHBOARD_HTML_PATH = Path(__file__).parent / "dashboard.html"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    if DASHBOARD_HTML_PATH.exists():
        return HTMLResponse(content=DASHBOARD_HTML_PATH.read_text())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
