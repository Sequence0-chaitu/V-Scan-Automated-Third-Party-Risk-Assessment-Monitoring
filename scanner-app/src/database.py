"""
database.py — SQLite persistence layer
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("vscan.database")


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_url  TEXT    NOT NULL,
                    score       REAL    NOT NULL,
                    risk_level  TEXT    NOT NULL,
                    timestamp   INTEGER NOT NULL    -- Unix epoch (seconds)
                );

                CREATE TABLE IF NOT EXISTS scan_checks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id     INTEGER NOT NULL REFERENCES scans(id),
                    check_name  TEXT    NOT NULL,
                    passed      INTEGER NOT NULL,   -- 1 / 0
                    iso_control TEXT,
                    nist_control TEXT,
                    source      TEXT
                );
                """
            )
        log.debug("Database schema initialised: %s", self.db_path)

    def save_scan(
        self,
        url: str,
        score: float,
        results: list[dict],
        breakdown: list[dict],
    ) -> int:
        risk_level = (
            "LOW" if score >= 80
            else "MEDIUM" if score >= 60
            else "HIGH" if score >= 40
            else "CRITICAL"
        )
        ts = int(datetime.now(timezone.utc).timestamp())

        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO scans (vendor_url, score, risk_level, timestamp) VALUES (?,?,?,?)",
                (url, score, risk_level, ts),
            )
            scan_id = cur.lastrowid

            conn.executemany(
                """
                INSERT INTO scan_checks
                    (scan_id, check_name, passed, iso_control, nist_control, source)
                VALUES (?,?,?,?,?,?)
                """,
                [
                    (
                        scan_id,
                        chk["name"],
                        1 if chk["passed"] else 0,
                        chk.get("iso"),
                        chk.get("nist"),
                        chk.get("source"),
                    )
                    for chk in breakdown
                ],
            )

        log.info(
            "Scan #%d saved — %s score=%.1f (%s)", scan_id, url, score, risk_level
        )
        return scan_id

    def get_scan_checks(self, scan_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scan_checks WHERE scan_id = ? ORDER BY id", (scan_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_scans(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
