"""
auth.py — Minimal API key authentication for V-Scan

Protects the scan/history endpoints behind a static API key read from
the environment (consistent with how DB_PATH/Q_PATH are already read
in web_server.py, and passed in via docker-compose's .env).
"""

import os
import secrets
import logging

from fastapi import Header, HTTPException, status

log = logging.getLogger("vscan.auth")

API_KEY = os.getenv("VSCAN_API_KEY")

if not API_KEY:
    log.warning(
        "VSCAN_API_KEY is not set — protected endpoints will reject all "
        "requests until it is configured in your .env file."
    )


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """
    FastAPI dependency — validates the X-API-Key header against
    VSCAN_API_KEY. Raises 401 if missing, unset, or invalid.

    Uses secrets.compare_digest for a constant-time comparison, so
    response timing can't be used to infer the key character-by-character
    (a plain `==` check exits early on the first mismatch, which leaks
    timing information over many requests).
    """
    if not API_KEY or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
