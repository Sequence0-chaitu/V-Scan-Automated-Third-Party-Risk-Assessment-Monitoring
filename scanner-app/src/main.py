#!/usr/bin/env python3
"""
V-Scan — CLI entrypoint
Usage:
    python src/main.py --url https://example.com --questionnaire questionnaire.json
"""

import click
import json
import logging
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scanner import Scanner
from scoring import ScoringEngine
from database import Database

console = Console()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("vscan")


@click.command()
@click.option("--url", required=True, help="Vendor URL to scan (e.g. https://example.com)")
@click.option(
    "--questionnaire",
    default="questionnaire.json",
    help="Path to completed questionnaire JSON",
    show_default=True,
)
@click.option(
    "--db",
    default=os.getenv("SQLITE_DB_PATH", "/app/data/vscan.db"),
    help="SQLite database path",
    show_default=True,
)
def main(url: str, questionnaire: str, db: str):
    """V-Scan: Automated Third-Party Risk Assessment Scanner."""

    console.print(
        Panel.fit(
            "[bold cyan]V-Scan[/] — Third-Party Risk Assessment",
            border_style="cyan",
        )
    )

    # ── Load questionnaire ───────────────────────────────────────────────────
    try:
        with open(questionnaire) as f:
            q_data = json.load(f)
        log.info("Loaded questionnaire: %s", questionnaire)
    except FileNotFoundError:
        console.print(f"[red]Questionnaire file not found:[/] {questionnaire}")
        sys.exit(1)

    # ── Run scan ─────────────────────────────────────────────────────────────
    console.print(f"\n[bold]Target:[/] {url}\n")
    scanner = Scanner(url)
    scan_results = scanner.run()

    # ── Score ────────────────────────────────────────────────────────────────
    engine = ScoringEngine(scan_results, q_data)
    score, breakdown = engine.calculate()

    # ── Persist to SQLite ────────────────────────────────────────────────────
    database = Database(db)
    database.save_scan(url=url, score=score, results=scan_results, breakdown=breakdown)

    # ── Display results ──────────────────────────────────────────────────────
    _print_results(url, score, breakdown)


def _print_results(url: str, score: float, breakdown: dict):
    colour = (
        "green" if score >= 80
        else "yellow" if score >= 60
        else "orange1" if score >= 40
        else "red"
    )
    level = (
        "LOW" if score >= 80
        else "MEDIUM" if score >= 60
        else "HIGH" if score >= 40
        else "CRITICAL"
    )

    console.print(
        Panel(
            f"[bold {colour}]Risk Level: {level}[/]\n"
            f"[bold]Score: {score:.1f} / 100[/]",
            title="[bold]Scan Result[/]",
            border_style=colour,
        )
    )

    table = Table(title="Compliance Breakdown", show_header=True, header_style="bold magenta")
    table.add_column("Check", style="dim", width=35)
    table.add_column("Status")
    table.add_column("ISO 27001")
    table.add_column("NIST CSF")

    for check in breakdown:
        status = "[green]PASS ✓[/]" if check["passed"] else "[red]FAIL ✗[/]"
        table.add_row(check["name"], status, check.get("iso", "—"), check.get("nist", "—"))

    console.print(table)
    console.print(
        f"\n[dim]Results persisted to database. View dashboard at "
        f"[link=http://localhost:3000]http://localhost:3000[/link][/]"
    )


if __name__ == "__main__":
    main()
