"""Interactive user interface for FinPulse configuration.

This module provides interactive prompts for configuring FinPulse operations:
- Data ingestion configuration
- ML training configuration  
- ML inference configuration

Organization (low-level to high-level):
1. Low-level input helpers (get_user_input, get_yes_no, get_choice_input)
2. Configuration gatherers (get_ingestion_config, get_ml_*_config)
3. Menu display (show_main_menu)
4. Private helpers (_run_ingestion, _run_ml_inference, _run_ml_training, _show_help)
5. Public entry point (run_interactive_mode)
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from ..core.runner import run_application
from ..config.loader import load_config


# =============================================================================
# Constants
# =============================================================================

HEADER_WIDTH = 60
MENU_CHOICES = ['1', '2', '3', '4', '5']
VERSION_BUMP_TYPES = ['major', 'minor', 'patch']


# =============================================================================
# Exceptions
# =============================================================================

class UserCancelledError(Exception):
    """Raised when user cancels an operation."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


# =============================================================================
# Low-Level Input Helpers
# =============================================================================

def _prompt_input(prompt_text: str) -> str:
    """Read user input and convert terminal interrupts into clean cancellations."""
    try:
        return input(prompt_text)
    except (KeyboardInterrupt, EOFError) as exc:
        raise UserCancelledError("User interrupted interactive input") from exc


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value.
    
    Args:
        prompt: The prompt to display to the user
        default: Default value if user presses Enter (optional)
    
    Returns:
        The user's input or default value
    """
    if default:
        response = _prompt_input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    return _prompt_input(f"{prompt}: ").strip()


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user.
    
    Args:
        prompt: The prompt to display to the user
        default: Default value if user presses Enter
    
    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    while True:
        response = _prompt_input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")


def get_choice_input(prompt: str, choices: list, default: str = None) -> str:
    """Get user input with validation against allowed choices.
    
    Args:
        prompt: The prompt to display to the user
        choices: List of valid choices
        default: Default value if user presses Enter (optional)
    
    Returns:
        The validated user choice
    """
    while True:
        if default:
            response = _prompt_input(f"{prompt} [{default}]: ").strip().lower()
            value = response if response else default
        else:
            value = _prompt_input(f"{prompt}: ").strip().lower()
        
        if value in choices:
            return value
        
        print(f"Invalid choice. Please enter one of: {', '.join(choices)}")


# =============================================================================
# Configuration Gatherers
# =============================================================================

def get_ingestion_config(run_inference: bool = True) -> dict:
    """Get data ingestion configuration interactively from user.
    
    Args:
        run_inference: Whether to run ML inference after ingestion (default: True)
    
    Returns:
        Dictionary with ingestion configuration including ml_inference setting
    
    Raises:
        UserCancelledError: If user cancels during validation prompts
    """
    print("\n=== FinPulse Interactive Setup ===")
    
    # Get current year for defaults
    current_year = datetime.now().year

    # Get config file
    while True:
        config_file = get_user_input("Config file path", "config/config.yaml")
        config_path = Path(config_file)
        if config_path.exists() or get_yes_no(f"Warning: Config file {config_path} does not exist. Continue anyway?", False):
            break

    # Get workspace folder
    while True:
        workspace = get_user_input("Finance workspace folder", "..")
        workspace_path = Path(workspace).resolve()
        if workspace_path.exists() or get_yes_no(f"Warning: Workspace folder {workspace_path} does not exist. Continue anyway?", False):
            break

    # Get workbook name
    while True:
        workbook_name = get_user_input("Finance workbook filename", f"FinanceWorkbook {current_year}.xlsx")
        if workbook_name.endswith('.xlsx') or get_yes_no("Warning: Workbook filename should end with .xlsx. Continue anyway?", False):
            break

    # Get inputs folder
    default_inputs = str(workspace_path / "Inputs")
    while True:
        inputs_folder = get_user_input("Inputs folder", default_inputs)
        inputs_path = Path(inputs_folder)
        if inputs_path.exists() or get_yes_no(f"Warning: Inputs folder {inputs_path} does not exist. Continue anyway?", False):
            break

    # Get logs folder
    default_logs = str(workspace_path / "FinPulseImportLogs")
    logs_folder = get_user_input("Logs folder", default_logs)

    # Get date range with current year defaults
    default_start = f"{current_year}-01-01"
    default_end = f"{current_year}-12-31"

    while True:
        start_date = get_user_input("Start date (YYYY-MM-DD)", default_start)
        if not start_date:
            break
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            break
        except ValueError:
            if get_yes_no(f"Warning: Start date '{start_date}' is not in YYYY-MM-DD format. Continue anyway?", False):
                break

    while True:
        end_date = get_user_input("End date (YYYY-MM-DD)", default_end)
        if not end_date:
            break
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            break
        except ValueError:
            if get_yes_no(f"Warning: End date '{end_date}' is not in YYYY-MM-DD format. Continue anyway?", False):
                break

    return {
        'config': config_file,
        'workspace': workspace,
        'workbook': workbook_name,
        'inputs': inputs_folder,
        'logs': logs_folder,
        'start': start_date or None,
        'end': end_date or None,
        'ml_inference': run_inference
    }


def get_ml_training_config() -> dict:
    """Get ML training configuration interactively from user.
    
    Returns:
        Dictionary with ML training configuration
    
    Raises:
        UserCancelledError: If user cancels during validation prompts
    """
    print("\n=== ML Training Configuration ===")
    
    current_year = datetime.now().year
    default_workbook = f"../FinanceWorkbook {current_year}.xlsx"
    
    while True:
        input_file = get_user_input("Excel workbook with labeled data", default_workbook)
        if input_file.endswith('.xlsx') or get_yes_no("Warning: Input file should be an Excel workbook (.xlsx). Continue anyway?", False):
            break
    
    while True:
        config_file = get_user_input("Config file path", "config/config.yaml")
        config_path = Path(config_file)
        if config_path.exists() or get_yes_no(f"Warning: Config file {config_path} does not exist. Continue anyway?", False):
            break
    
    print("\nVersion bump type:")
    print("  major - Algorithm or encoder changes")
    print("  minor - New training data (default)")
    print("  patch - Bug fixes or small adjustments")
    
    bump_type = get_choice_input(
        "Version bump type",
        choices=VERSION_BUMP_TYPES,
        default='minor'
    )
    
    notes = get_user_input("Training notes (optional)", "")
    
    return {
        'input': input_file,
        'config': config_file,
        'bump': bump_type,
        'notes': notes
    }


def get_ml_inference_config() -> dict:
    """Get ML inference configuration interactively from user.
    
    Returns:
        Dictionary with ML inference configuration
    
    Raises:
        UserCancelledError: If user cancels during validation prompts
    """
    print("\n=== ML Inference Configuration ===")
    
    current_year = datetime.now().year
    default_workbook = f"../FinanceWorkbook {current_year}.xlsx"
    
    while True:
        input_file = get_user_input("Excel workbook path", default_workbook)
        if input_file.endswith('.xlsx') or get_yes_no("Warning: Input file should be an Excel workbook (.xlsx). Continue anyway?", False):
            break
    
    while True:
        config_file = get_user_input("Config file path", "config/config.yaml")
        config_path = Path(config_file)
        if config_path.exists() or get_yes_no(f"Warning: Config file {config_path} does not exist. Continue anyway?", False):
            break
    
    return {
        'input': input_file,
        'config': config_file
    }


# =============================================================================
# Menu Display
# =============================================================================

def show_main_menu() -> int:
    """Display main menu and get user selection.
    
    Returns:
        Integer representing user's menu choice (1-5)
    """
    print("\n" + "="*HEADER_WIDTH)
    print("  FinPulse: Intelligent Financial Data Ingestion Tool")
    print("="*HEADER_WIDTH)
    print("\nWhat would you like to do?\n")
    print("  1. Data Ingestion and Inference (default)")
    print("  2. Data Ingestion Only")
    print("  3. Category and Subcategory Inference Only")
    print("  4. Model Retraining")
    print("  5. Help")
    print()
    
    while True:
        choice = _prompt_input("Enter your choice [1-5] (default: 1): ").strip()
        if not choice:
            return 1
        if choice in MENU_CHOICES:
            return int(choice)
        print(f"Invalid choice. Please enter a number between 1 and {len(MENU_CHOICES)}.")


# =============================================================================
# Private Helper Functions
# =============================================================================

def _run_ingestion(run_inference: bool, title: str) -> None:
    """Run data ingestion with or without ML inference.
    
    Args:
        run_inference: Whether to run ML inference after ingestion
        title: Display title for the operation
    
    Raises:
        UserCancelledError: If user cancels during configuration
        ImportError: If required dependencies are missing
        Exception: If ingestion fails
    """
    print(f"\n{'='*HEADER_WIDTH}\n  {title}\n{'='*HEADER_WIDTH}")
    config = get_ingestion_config(run_inference=run_inference)
    
    args = SimpleNamespace(
        config=config['config'],
        start=config['start'],
        end=config['end'],
        dry_run=False,
        log_dir=config['logs'],
        workspace=config['workspace'],
        workbook=config['workbook'],
        inputs=config['inputs'],
        ml_inference_requested=config['ml_inference']
    )
    
    run_application(args)


def _run_ml_inference() -> None:
    """Run ML inference on existing workbook.
    
    Raises:
        UserCancelledError: If user cancels during configuration
        ImportError: If ML dependencies are missing
        Exception: If ML inference fails
    """
    print(f"\n{'='*HEADER_WIDTH}\n  Category and Subcategory Inference\n{'='*HEADER_WIDTH}")
    config = get_ml_inference_config()
    
    # Lazy import - ML dependencies are optional
    from ..ml.pipeline import run_ml_pipeline
    
    print(f"\nRunning ML inference on: {config['input']}")
    cfg = load_config(config['config'])
    run_ml_pipeline(cfg, config['input'])
    print("\n✅ ML inference completed successfully")


def _run_ml_training() -> None:
    """Run ML model training.
    
    Raises:
        UserCancelledError: If user cancels during configuration
        ImportError: If ML dependencies are missing
        Exception: If model training fails
    """
    print(f"\n{'='*HEADER_WIDTH}\n  Model Retraining\n{'='*HEADER_WIDTH}")
    config = get_ml_training_config()
    
    # Lazy import - ML dependencies are optional
    from ..ml.train import train_models
    
    print(f"\nTraining models with:")
    print(f"  Input: {config['input']}")
    print(f"  Config: {config['config']}")
    print(f"  Bump: {config['bump']}")
    print(f"  Notes: {config['notes'] or '(none)'}\n")
    
    train_models(
        cfg_path=config['config'],
        xlsx_path=config['input'],
        bump_type=config['bump'],
        notes=config['notes']
    )


def _show_help() -> None:
    """Display help information."""
    print(f"\n{'='*HEADER_WIDTH}\n  FinPulse Help\n{'='*HEADER_WIDTH}")
    print("""
FinPulse is an intelligent financial data ingestion tool that helps you:
  • Import bank transaction CSV files into Excel
  • Automatically categorize transactions using ML
  • Maintain per-account sheets and consolidated details
  • Deduplicate transactions across imports
  • Train and improve ML models over time

INTERACTIVE MODE OPTIONS:

  1. Data Ingestion and Inference (default)
     Import bank transactions from CSV files and apply ML predictions to
     automatically categorize transactions. This is the most common workflow.

  2. Data Ingestion Only
     Import bank transactions from CSV files without applying ML predictions.
     Use this when you want to manually categorize transactions later.

  3. Category and Subcategory Inference Only
     Apply ML predictions to existing transactions in your workbook without
     importing new data. Use this to categorize previously imported transactions.

  4. Model Retraining
     Train ML models on your labeled transaction data to improve prediction
     accuracy. Run this whenever you've added new labeled transactions.

  5. Help
     Show this help information.

COMMAND-LINE INTERFACE:

  For automation and scripting, you can use the command-line interface:
  
  Data Ingestion:
    python -m src.finpulse.main ingest --config config.yaml --start 2025-01-01
  
  ML Training:
    python -m src.finpulse.main ml train --input workbook.xlsx --bump minor
  
  ML Inference:
    python -m src.finpulse.main ml infer --input workbook.xlsx

CONFIGURATION:

  Edit config/config.yaml to define:
  • Target workbook path
  • Bank account sources and file patterns
  • Column mappings for each bank
  • ML model settings (algorithms, features, hyperparameters)

DOCUMENTATION:

  See README.md for detailed documentation
  See README_ML.md for ML-specific documentation
  See config/config_examples.yaml for configuration examples

FOR HELP ON CLI OPTIONS:

  python -m src.finpulse.main --help
  python -m src.finpulse.main ingest --help
  python -m src.finpulse.main ml --help
  python -m src.finpulse.main ml train --help
  python -m src.finpulse.main ml infer --help
""")
    sys.exit(0)


# =============================================================================
# Public Entry Point
# =============================================================================

def run_interactive_mode() -> None:
    """Run FinPulse in interactive mode with menu.
    
    Displays menu, gets user choice, and executes the selected operation.
    This is the main entry point that handles all exceptions and exits appropriately.
    """
    try:
        choice = show_main_menu()
        
        handlers = {
            1: lambda: _run_ingestion(True, "Data Ingestion and Inference"),
            2: lambda: _run_ingestion(False, "Data Ingestion Only"),
            3: _run_ml_inference,
            4: _run_ml_training,
            5: _show_help
        }
        
        handlers[choice]()
        
    except UserCancelledError as e:
        print(f"\nOperation cancelled: {e}")
        sys.exit(130)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements-ml.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        traceback.print_exc()
        sys.exit(1)
