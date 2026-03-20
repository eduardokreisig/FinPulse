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

import argparse
import sys
import traceback

from .core.runner import run_application
from .ui.interactive import run_interactive_mode


def main() -> None:
    """Main entry point for FinPulse CLI.
    
    Parses command-line arguments and dispatches to appropriate handlers.
    Supports both explicit subcommands and backward-compatible default import.
    """
    
    # =========================================================================
    # Main Parser Setup
    # =========================================================================
    parser = argparse.ArgumentParser(
        prog='finpulse',
        description='FinPulse: Intelligent Financial Data Ingestion and ML Tool',
        epilog='For detailed help on a command, use: python -m src.finpulse.main <command> --help',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subcommands (ingest, ml)
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='Available commands (use <command> --help for details)',
        help='Command to execute'
    )
    
    # =========================================================================
    # INGEST Command - Process bank transaction data
    # =========================================================================
    ingest_parser = subparsers.add_parser(
        'ingest',
        help='Ingest and process bank transaction data',
        description='Ingest bank transaction CSV files into Excel workbook with deduplication and ML categorization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  # Interactive mode (recommended for first-time setup)
  python -m src.finpulse.main ingest
  
  # Specify date range
  python -m src.finpulse.main ingest --start 2025-01-01 --end 2025-12-31
  
  # Dry run to preview changes
  python -m src.finpulse.main ingest --dry-run
  
  # Custom paths
  python -m src.finpulse.main ingest --workspace /path/to/finance --workbook "FinanceWorkbook 2025.xlsx"'''
    )
    
    ingest_parser.add_argument(
        '--config',
        metavar='PATH',
        help='Path to config YAML file (default: config/config.yaml)'
    )
    ingest_parser.add_argument(
        '--start',
        metavar='DATE',
        help='Start date for ingestion in YYYY-MM-DD format (e.g., 2025-01-01)'
    )
    ingest_parser.add_argument(
        '--end',
        metavar='DATE',
        help='End date for ingestion in YYYY-MM-DD format (e.g., 2025-12-31)'
    )
    ingest_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying the workbook'
    )
    ingest_parser.add_argument(
        '--log-dir',
        metavar='PATH',
        help='Directory for log files (default: from config or ../FinPulseImportLogs)'
    )
    ingest_parser.add_argument(
        '--workspace',
        metavar='PATH',
        help='Finance workspace folder containing workbook (interactive mode only)'
    )
    ingest_parser.add_argument(
        '--workbook',
        metavar='FILENAME',
        help='Finance workbook filename (interactive mode only)'
    )
    ingest_parser.add_argument(
        '--inputs',
        metavar='PATH',
        help='Inputs folder containing bank CSV files (interactive mode only)'
    )
    
    # =========================================================================
    # ML Command Group - Machine learning operations
    # =========================================================================
    ml_parser = subparsers.add_parser(
        'ml',
        help='Machine learning operations for transaction categorization',
        description='Train models or run inference for automatic transaction categorization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Available ML commands:
  train    Train category and subcategory models on labeled data
  infer    Run ML inference to predict categories for transactions

Examples:
  # Train models with interactive prompts
  python -m src.finpulse.main ml train --input "FinanceWorkbook 2025.xlsx"
  
  # Train with command-line parameters
  python -m src.finpulse.main ml train --input workbook.xlsx --bump minor --notes "Added Q1 data"
  
  # Run inference
  python -m src.finpulse.main ml infer --input "FinanceWorkbook 2025.xlsx"'''
    )
    
    ml_subparsers = ml_parser.add_subparsers(
        dest='ml_command',
        title='ML commands',
        description='Machine learning operations',
        help='ML operation to perform'
    )
    
    # -------------------------------------------------------------------------
    # ML TRAIN - Train categorization models
    # -------------------------------------------------------------------------
    train_parser = ml_subparsers.add_parser(
        'train',
        help='Train ML models on labeled transaction data',
        description='Train category and subcategory models using existing labeled transactions in your workbook',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  # Interactive mode (prompts for notes and version bump)
  python -m src.finpulse.main ml train --input "FinanceWorkbook 2025.xlsx" --interactive
  
  # Non-interactive with all parameters
  python -m src.finpulse.main ml train --input workbook.xlsx --bump minor --notes "Added 500 new transactions"
  
  # Major version bump for algorithm changes
  python -m src.finpulse.main ml train --input workbook.xlsx --bump major --notes "Switched to S-BERT encoder"'''
    )
    
    train_parser.add_argument(
        '--input',
        required=True,
        metavar='PATH',
        help='Path to Excel workbook with labeled transaction data (required)'
    )
    train_parser.add_argument(
        '--config',
        default='config/config.yaml',
        metavar='PATH',
        help='Path to config file with ML settings (default: config/config.yaml)'
    )
    train_parser.add_argument(
        '--bump',
        choices=['major', 'minor', 'patch'],
        default='minor',
        metavar='TYPE',
        help='Version bump type: major (algorithm change), minor (new data), patch (bug fix) (default: minor)'
    )
    train_parser.add_argument(
        '--notes',
        default='',
        metavar='TEXT',
        help='Training notes describing changes or improvements (default: empty)'
    )
    train_parser.add_argument(
        '--interactive',
        action='store_true',
        help='Prompt for notes and bump type interactively'
    )
    train_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed training progress and diagnostics'
    )
    
    # -------------------------------------------------------------------------
    # ML INFER - Run inference on transactions
    # -------------------------------------------------------------------------
    infer_parser = ml_subparsers.add_parser(
        'infer',
        help='Run ML inference to categorize transactions',
        description='Apply trained ML models to predict categories and subcategories for unlabeled transactions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  # Run inference on workbook
  python -m src.finpulse.main ml infer --input "FinanceWorkbook 2025.xlsx"
  
  # Use custom config
  python -m src.finpulse.main ml infer --input workbook.xlsx --config custom_config.yaml'''
    )
    
    infer_parser.add_argument(
        '--input',
        required=True,
        metavar='PATH',
        help='Path to Excel workbook with transactions to categorize (required)'
    )
    infer_parser.add_argument(
        '--config',
        default='config/config.yaml',
        metavar='PATH',
        help='Path to config file with ML settings (default: config/config.yaml)'
    )
    infer_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed inference progress and predictions'
    )
    
    # =========================================================================
    # Parse Arguments and Dispatch
    # =========================================================================
    
    # Check if running in interactive mode (no arguments provided)
    if len(sys.argv) == 1:
        run_interactive_mode()
        return
    
    args = parser.parse_args()
    
    # If no command specified, default to ingest for backward compatibility
    if args.command is None:
        args.command = 'ingest'
    
    # -------------------------------------------------------------------------
    # Handle ML Commands
    # -------------------------------------------------------------------------
    if args.command == 'ml':
        # Check if ML subcommand was provided
        if args.ml_command is None:
            ml_parser.print_help()
            sys.exit(1)
        
        try:
            # ML TRAIN
            if args.ml_command == 'train':
                from .ml.train import train_models
                
                # Get notes and bump type (interactive or from args)
                if args.interactive:
                    from .ui.interactive import get_ml_training_config
                    notes, bump_type = get_ml_training_config()
                else:
                    notes = args.notes
                    bump_type = args.bump
                
                if args.verbose:
                    print(f"Training models with:")
                    print(f"  Input: {args.input}")
                    print(f"  Config: {args.config}")
                    print(f"  Bump: {bump_type}")
                    print(f"  Notes: {notes}")
                    print()
                
                train_models(args.config, args.input, bump_type, notes)
                return
            
            # ML INFER
            elif args.ml_command == 'infer':
                from .ml.pipeline import run_ml_pipeline
                from .config.loader import load_config
                
                if args.verbose:
                    print(f"Running inference with:")
                    print(f"  Input: {args.input}")
                    print(f"  Config: {args.config}")
                    print()
                
                cfg = load_config(args.config)
                run_ml_pipeline(cfg, args.input)
                return
                
        except ImportError as e:
            print(f"❌ Import Error: {e}")
            print("\nMake sure ML dependencies are installed:")
            print("  pip install -r requirements-ml.txt")
            sys.exit(1)
            
        except FileNotFoundError as e:
            print(f"❌ File Not Found: {e}")
            sys.exit(1)
            
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            sys.exit(1)
            
        except Exception as e:
            print(f"❌ ML operation failed: {e}")
            if args.verbose:
                print("\nFull traceback:")
                traceback.print_exc()
            sys.exit(1)
    
    # -------------------------------------------------------------------------
    # Handle INGEST Command (default)
    # -------------------------------------------------------------------------
    try:
        run_application(args)
    except Exception as e:
        print(f"❌ Ingest operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()