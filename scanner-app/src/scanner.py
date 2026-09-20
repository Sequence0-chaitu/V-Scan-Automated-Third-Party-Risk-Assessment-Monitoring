"""
scanner.py — HTTP header and SSL certificate checks
"""

import logging
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

log = logging.getLogger("vscan.scanner")

SECURITY_HEADERS = [
    ("Strict-Transport-Security", "A.14.1", "PR.PT-3"),
    ("Content-Security-Policy", "A.14.2", "DE.CM-8"),
    ("X-Frame-Options", "A.14.2", "PR.PT-3"),
    ("X-Content-Type-Options", "A.14.2", "PR.PT-3"),
    ("Referrer-Policy", "A.14.2", "PR.DS-5"),
    ("Permissions-Policy", "A.14.2", "PR.PT-3"),
]


class Scanner:
    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.hostname = urlparse(url).hostname

    def run(self) -> list[dict]:
        """Execute all checks and return a list of result dicts."""
        results = []
        results.extend(self._check_headers())
        results.extend(self._check_ssl())
        return results

    # ── HTTP Header Checks ───────────────────────────────────────────────────
    def _check_headers(self) -> list[dict]:
        results = []
        try:
            resp = requests.get(self.url, timeout=self.timeout, allow_redirects=True)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            log.info("Headers fetched from %s (HTTP %s)", self.url, resp.status_code)
        except requests.RequestException as exc:
            log.error("Header check failed: %s", exc)
            # Mark all header checks as failed
            for name, iso, nist in SECURITY_HEADERS:
                results.append(
                    _result(f"Header: {name}", False, iso, nist, error=str(exc))
                )
            return results

        for name, iso, nist in SECURITY_HEADERS:
            present = name.lower() in headers
            results.append(_result(f"Header: {name}", present, iso, nist))
            log.debug("  %s → %s", name, "PASS" if present else "FAIL")

        return results

    # ── SSL / TLS Checks ─────────────────────────────────────────────────────
    def _check_ssl(self) -> list[dict]:
        results = []
        context = ssl.create_default_context()

        try:
            with socket.create_connection((self.hostname, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert = ssock.getpeercert()
                    tls_version = ssock.version()

            # 1. Valid certificate (no exception = valid)
            results.append(_result("SSL: Valid Certificate", True, "A.10.1", "PR.DS-2"))

            # 2. Certificate expiry
            not_after = cert.get("notAfter", "")
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            days_left = (expiry - datetime.now(timezone.utc)).days
            expiry_ok = days_left >= 30
            results.append(
                _result(
                    f"SSL: Certificate Expiry (>{30}d, {days_left}d left)",
                    expiry_ok,
                    "A.10.1",
                    "PR.DS-2",
                )
            )

            # 3. TLS version
            tls_ok = tls_version in ("TLSv1.2", "TLSv1.3")
            results.append(
                _result(
                    f"SSL: TLS Version ≥ 1.2 ({tls_version})",
                    tls_ok,
                    "A.10.1",
                    "PR.DS-2",
                )
            )
            log.info("SSL checks passed for %s (%s, %d days)", self.hostname, tls_version, days_left)

        except ssl.SSLError as exc:
            log.error("SSL error: %s", exc)
            for name in ["SSL: Valid Certificate", "SSL: Certificate Expiry", "SSL: TLS Version ≥ 1.2"]:
                results.append(_result(name, False, "A.10.1", "PR.DS-2", error=str(exc)))
        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            log.error("Connection error: %s", exc)
            for name in ["SSL: Valid Certificate", "SSL: Certificate Expiry", "SSL: TLS Version ≥ 1.2"]:
                results.append(_result(name, False, "A.10.1", "PR.DS-2", error=str(exc)))

        return results


def _result(name: str, passed: bool, iso: str, nist: str, error: str = "") -> dict:
    return {"name": name, "passed": passed, "iso": iso, "nist": nist, "error": error}
