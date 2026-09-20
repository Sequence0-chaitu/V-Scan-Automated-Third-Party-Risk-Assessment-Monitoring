#!/usr/bin/env bash
# Reset (wipe) the V-Scan SQLite database
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")"

echo "⚠️  This will DELETE all scan history. Press Ctrl-C to abort."
read -rp "Type 'yes' to confirm: " confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

docker compose exec scanner-app rm -f /app/data/vscan.db
echo "✓ Database wiped. It will be recreated on the next scan."
