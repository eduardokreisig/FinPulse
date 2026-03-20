"""Main entry point for FinPulse financial data ingestion and ML operations.

FinPulse can be run in two modes:

1. Interactive Mode (Simplest way to use and recommended for most users)
   Run without arguments to access a menu-driven interface:
   
   python -m src.finpulse.main
   
   This presents a simple menu with 5 options:
   - Data Ingestion and Inference
   - Data Ingestion Only
   - Category and Subcategory Inference Only
   - Model Retraining
   - Help

2. Command-Line Interface (CLI) with subcommands
   Run with specific commands and arguments for automation and scripting.
   
   Available commands:
   - ingest: Ingest and process bank transaction data
   - ml train: Train machine learning models for transaction categorization
   - ml infer: Run ML inference on transactions
   
   Getting help:
     python -m src.finpulse.main --help
     python -m src.finpulse.main ingest --help
     python -m src.finpulse.main ml --help
     python -m src.finpulse.main ml train --help
     python -m src.finpulse.main ml infer --help
   
   Examples:
     # Ingest transactions (default command)
     python -m src.finpulse.main ingest --config config.yaml --start 2025-01-01
     python -m src.finpulse.main --config config.yaml --start 2025-01-01
     
     # Train ML models
     python -m src.finpulse.main ml train --input workbook.xlsx --bump minor
     
     # Run ML inference
     python -m src.finpulse.main ml infer --input workbook.xlsx
"""

import sys

from .ui.interactive import run_interactive_mode
from .ui.cli import run_cli_mode


def main() -> None:
    """Main entry point for FinPulse.
    
    Detects whether to run in interactive mode (no arguments) or
    CLI mode (with arguments) and delegates to the appropriate handler.
    """
    if len(sys.argv) == 1:
        run_interactive_mode()
    else:
        run_cli_mode()


if __name__ == "__main__":
    main()
