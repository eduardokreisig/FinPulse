#!/bin/zsh
# run-finance-ingest-modular.sh
# Purpose: Run the modular version of fin_statements_ingest
# Usage: ./run-finance-ingest-modular.sh [--start YYYY-MM-DD] [--end YYYY-MM-DD]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT_NAME="fin_statements_ingest.py"
CONFIG_NAME="config.yaml"

# Parse args
START_ARG=""
END_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --start) START_ARG="--start $2"; shift 2 ;;
    --end)   END_ARG="--end $2";   shift 2 ;;
    *) echo "Unknown arg: $1"; echo "Usage: $0 [--start YYYY-MM-DD] [--end YYYY-MM-DD]"; exit 1 ;;
  esac
done

echo "→ Moving to: $PROJECT_DIR"
cd "$PROJECT_DIR"

[[ -f "src/$SCRIPT_NAME" ]] || { echo "ERROR: src/$SCRIPT_NAME not found"; exit 1; }
[[ -f "config/$CONFIG_NAME" ]] || { echo "ERROR: config/$CONFIG_NAME not found"; exit 1; }

# Add src to Python path so finpulse package can be imported
export PYTHONPATH="$PROJECT_DIR/src:${PYTHONPATH:-}"

# Prefer your local .venv if present
if [[ -d ".venv" ]]; then
  echo "→ Activating .venv"
  source .venv/bin/activate
  PY="python"
else
  PY="python3"
fi

# Run
echo "→ Running: $PY src/$SCRIPT_NAME --config config/$CONFIG_NAME $START_ARG $END_ARG"
set -x
$PY "src/$SCRIPT_NAME" --config "config/$CONFIG_NAME" $START_ARG $END_ARG
set +x
echo "✓ Done."