"""Main entry point for FinPulse financial data ingestion."""

import argparse

from .core.runner import run_application


def main() -> None:
    """Main entry point."""
    ap = argparse.ArgumentParser(
        description="FinPulse v5.3.17 (robust CSV defaults; no YAML change needed)"
    )
    ap.add_argument("--config", default=None)
    ap.add_argument("--start", help="YYYY-MM-DD", default=None)
    ap.add_argument("--end", help="YYYY-MM-DD", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--workspace", default=None)
    ap.add_argument("--workbook", default=None)
    ap.add_argument("--inputs", default=None)
    args = ap.parse_args()

    run_application(args)


if __name__ == "__main__":
    main()