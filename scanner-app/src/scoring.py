"""
scoring.py — Risk scoring engine

Weights:
  • Each automated check:       ~5 pts  (9 checks  = 45 pts)
  • Each questionnaire answer:  ~5 pts  (11 items  = 55 pts)
Total max = 100
"""

import logging

log = logging.getLogger("vscan.scoring")

# Weights per automated check
CHECK_WEIGHT = 5

# Questionnaire items with weights and control mappings
Q_ITEMS = [
    ("encryption_at_rest",      5, "A.10.1", "PR.DS-1"),
    ("encryption_in_transit",   5, "A.10.1", "PR.DS-2"),
    ("access_control_policy",   5, "A.9.1",  "PR.AC-1"),
    ("mfa_enforced",            5, "A.9.4",  "PR.AC-7"),
    ("patch_management",        5, "A.12.6", "ID.RA-1"),
    ("incident_response_plan",  5, "A.16.1", "RS.RP-1"),
    ("security_awareness",      5, "A.7.2",  "PR.AT-1"),
    ("vendor_risk_program",     5, "A.15.1", "ID.SC-2"),
    ("data_classification",     5, "A.8.2",  "PR.DS-5"),
    ("backup_restore_tested",   5, "A.12.3", "PR.IP-4"),
    ("penetration_testing",     5, "A.14.2", "DE.CM-8"),
]


class ScoringEngine:
    def __init__(self, scan_results: list[dict], questionnaire: dict):
        self.scan_results = scan_results
        self.questionnaire = questionnaire

    def calculate(self) -> tuple[float, list[dict]]:
        """Return (score, full_breakdown)."""
        breakdown = []
        total = 0.0

        # ── Automated checks ─────────────────────────────────────────────────
        for check in self.scan_results:
            if check["passed"]:
                total += CHECK_WEIGHT
            breakdown.append(
                {
                    "name": check["name"],
                    "passed": check["passed"],
                    "iso": check.get("iso", "—"),
                    "nist": check.get("nist", "—"),
                    "source": "automated",
                }
            )

        # ── Questionnaire checks ──────────────────────────────────────────────
        for key, weight, iso, nist in Q_ITEMS:
            value = self.questionnaire.get(key, False)
            passed = bool(value)
            if passed:
                total += weight
            breakdown.append(
                {
                    "name": f"Q: {key.replace('_', ' ').title()}",
                    "passed": passed,
                    "iso": iso,
                    "nist": nist,
                    "source": "questionnaire",
                }
            )

        # ── Clamp to 100 ─────────────────────────────────────────────────────
        score = min(total, 100.0)
        log.info("Risk score calculated: %.1f / 100", score)
        return score, breakdown
