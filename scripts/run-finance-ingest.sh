#!/bin/zsh
# run-finance-ingest.sh
# Purpose: Run FinPulse financial data ingestion
# Usage: ./run-finance-ingest.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "→ Moving to: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Prefer your local .venv if present
if [[ -d ".venv" ]]; then
  echo "→ Activating .venv"
  source .venv/bin/activate
  PY="python"
else
  PY="python3"
fi

# Run with interactive prompts
echo "→ Running: $PY -m src.finpulse.main"
$PY -m src.finpulse.main
echo "✓ Done."