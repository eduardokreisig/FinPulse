"""Command-line interface for FinPulse.

This module provides the CLI implementation for FinPulse operations:
- Argument parser setup for ingest and ML commands
- Command handlers for executing operations
- Error handling and user feedback

Organization:
1. Constants
2. Helper functions (verbose output)
3. Parser setup functions
4. Command handlers
5. Public entry point (run_cli_mode)
"""

import argparse
import sys
import traceback
from pathlib import Path

from ..core.runner import run_application
from ..config.loader import load_config
from .interactive import get_ml_training_config


# =============================================================================
# Constants
# =============================================================================

VERSION_BUMP_TYPES = ['major', 'minor', 'patch']


# =============================================================================
# Helper Functions
# =============================================================================

def _print_verbose_info(args, operation: str, **kwargs):
    """Print verbose information if verbose flag is set.
    
    Args:
        args: Parsed arguments object
        operation: Name of the operation (e.g., "Training models")
        **kwargs: Key-value pairs to display
    """
    if not getattr(args, 'verbose', False):
        return
    
    print(f"{operation} with:")
    for key, value in kwargs.items():
        print(f"  {key}: {value}")
    print()


# =============================================================================
# Parser Setup Functions
# =============================================================================

def _setup_ingest_parser(subparsers):
    """Setup argument parser for ingest command.
    
    Args:
        subparsers: Subparsers object from main parser
    
    Returns:
        Configured ingest parser
    """
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
    
    ingest_parser.add_argument('--config', metavar='PATH', help='Path to config YAML file (default: config/config.yaml)')
    ingest_parser.add_argument('--start', metavar='DATE', help='Start date for ingestion in YYYY-MM-DD format (e.g., 2025-01-01)')
    ingest_parser.add_argument('--end', metavar='DATE', help='End date for ingestion in YYYY-MM-DD format (e.g., 2025-12-31)')
    ingest_parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying the workbook')
    ingest_parser.add_argument('--log-dir', metavar='PATH', help='Directory for log files (default: from config or ../FinPulseImportLogs)')
    ingest_parser.add_argument('--workspace', metavar='PATH', help='Finance workspace folder containing workbook (interactive mode only)')
    ingest_parser.add_argument('--workbook', metavar='FILENAME', help='Finance workbook filename (interactive mode only)')
    ingest_parser.add_argument('--inputs', metavar='PATH', help='Inputs folder containing bank CSV files (interactive mode only)')
    
    return ingest_parser


def _setup_ml_parser(subparsers):
    """Setup argument parser for ML commands.
    
    Args:
        subparsers: Subparsers object from main parser
    
    Returns:
        Configured ML parser
    """
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
    
    ml_subparsers = ml_parser.add_subparsers(dest='ml_command', title='ML commands', description='Machine learning operations', help='ML operation to perform')
    
    # ML TRAIN subcommand
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
    
    train_parser.add_argument('--input', required=True, metavar='PATH', help='Path to Excel workbook with labeled transaction data (required)')
    train_parser.add_argument('--config', default='config/config.yaml', metavar='PATH', help='Path to config file with ML settings (default: config/config.yaml)')
    train_parser.add_argument('--bump', choices=VERSION_BUMP_TYPES, default='minor', metavar='TYPE', help='Version bump type: major (algorithm change), minor (new data), patch (bug fix) (default: minor)')
    train_parser.add_argument('--notes', default='', metavar='TEXT', help='Training notes describing changes or improvements (default: empty)')
    train_parser.add_argument('--interactive', action='store_true', help='Prompt for notes and bump type interactively')
    train_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed training progress and diagnostics')
    
    # ML INFER subcommand
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
    
    infer_parser.add_argument('--input', required=True, metavar='PATH', help='Path to Excel workbook with transactions to categorize (required)')
    infer_parser.add_argument('--config', default='config/config.yaml', metavar='PATH', help='Path to config file with ML settings (default: config/config.yaml)')
    infer_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed inference progress and predictions')
    
    return ml_parser


def _create_argument_parser():
    """Create and configure the main argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='finpulse',
        description='FinPulse: Intelligent Financial Data Ingestion and ML Tool',
        epilog='For detailed help on a command, use: python -m src.finpulse.main <command> --help',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', title='commands', description='Available commands (use <command> --help for details)', help='Command to execute')
    
    _setup_ingest_parser(subparsers)
    _setup_ml_parser(subparsers)
    
    return parser


# =============================================================================
# Command Handlers
# =============================================================================

def _handle_ml_train(args):
    """Handle ML training command.
    
    Args:
        args: Parsed command-line arguments
    """
    from ..ml.train import train_models
    
    if args.interactive:
        config = get_ml_training_config()
        notes = config['notes']
        bump_type = config['bump']
    else:
        notes = args.notes
        bump_type = args.bump
    
    _print_verbose_info(args, "Training models", Input=args.input, Config=args.config, Bump=bump_type, Notes=notes or '(none)')
    train_models(args.config, args.input, bump_type, notes)


def _handle_ml_infer(args):
    """Handle ML inference command.
    
    Args:
        args: Parsed command-line arguments
    """
    from ..ml.pipeline import run_ml_pipeline
    
    _print_verbose_info(args, "Running inference", Input=args.input, Config=args.config)
    cfg = load_config(args.config)
    run_ml_pipeline(cfg, args.input)


def _handle_ml_commands(args, ml_parser):
    """Handle ML command dispatch and error handling.
    
    Args:
        args: Parsed command-line arguments
        ml_parser: ML argument parser for help display
    """
    if args.ml_command is None:
        ml_parser.print_help()
        sys.exit(1)
    
    try:
        if args.ml_command == 'train':
            _handle_ml_train(args)
        elif args.ml_command == 'infer':
            _handle_ml_infer(args)
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nMake sure ML dependencies are installed:")
        print("  pip install -r requirements-ml.txt")
        sys.exit(1)
        
    except (FileNotFoundError, ValueError) as e:
        error_type = "File Not Found" if isinstance(e, FileNotFoundError) else "Configuration Error"
        print(f"❌ {error_type}: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ ML operation failed: {e}")
        print("\nTroubleshooting:")
        print("  - Verify input file exists and is a valid Excel workbook")
        print("  - Check config file for correct ML settings")
        print("  - Ensure workbook has labeled data for training")
        if getattr(args, 'verbose', False):
            print("\nFull traceback:")
            traceback.print_exc()
        sys.exit(1)


def _handle_ingest_command(args):
    """Handle ingest command with validation and error handling.
    
    Args:
        args: Parsed command-line arguments
    """
    if hasattr(args, 'config') and args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {args.config}")
            print("\nCreate a config file or use the default: config/config.yaml")
            sys.exit(1)
    
    try:
        run_application(args)
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("\nTroubleshooting:")
        print("  - Verify workbook path in config file")
        print("  - Check that input CSV files exist")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTroubleshooting:")
        print("  - Review config.yaml for syntax errors")
        print("  - Verify date formats (YYYY-MM-DD)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ingest operation failed: {e}")
        if getattr(args, 'verbose', False):
            print("\nFull traceback:")
            traceback.print_exc()
        sys.exit(1)


# =============================================================================
# Public Entry Point
# =============================================================================

def run_cli_mode() -> None:
    """Run FinPulse in CLI mode with command-line arguments.
    
    Parses command-line arguments and dispatches to appropriate handlers.
    Supports ingest and ML subcommands with full argument parsing.
    """
    parser = _create_argument_parser()
    args = parser.parse_args()
    
    if args.command is None:
        args.command = 'ingest'
    
    if args.command == 'ml':
        ml_parser = _setup_ml_parser(parser.add_subparsers(dest='_dummy'))
        _handle_ml_commands(args, ml_parser)
    else:
        _handle_ingest_command(args)
