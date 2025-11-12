"""Interactive user interface for FinPulse configuration."""

import sys
from datetime import datetime
from pathlib import Path


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value."""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    return input(f"{prompt}: ").strip()


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")


def get_interactive_config():
    """Get configuration interactively from user."""
    print("\n=== FinPulse Interactive Setup ===")
    
    # Get current year for defaults
    current_year = datetime.now().year

    # Get config file
    config_file = get_user_input("Config file path", "config/config.yaml")
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"Warning: Config file {config_path} does not exist")
        if not get_yes_no("Continue anyway?", False):
            sys.exit(1)

    # Get workspace folder
    workspace = get_user_input("Finance workspace folder", "..")
    workspace_path = Path(workspace).resolve()

    # Get workbook name
    workbook_name = get_user_input("Finance workbook filename", f"FinanceWorkbook {current_year}.xlsx")

    # Get inputs folder
    default_inputs = str(workspace_path / "Inputs")
    inputs_folder = get_user_input("Inputs folder", default_inputs)

    # Get logs folder
    default_logs = str(workspace_path / "FinPulseImportLogs")
    logs_folder = get_user_input("Logs folder", default_logs)

    # Get date range with current year defaults
    default_start = f"{current_year}-01-01"
    default_end = f"{current_year}-12-31"

    start_date = get_user_input("Start date (YYYY-MM-DD)", default_start)
    end_date = get_user_input("End date (YYYY-MM-DD)", default_end)
    
    # ML inference preference
    ml_inference = get_yes_no("Apply ML predictions to fill missing Category and Subcategory values?\nYes (default) / No", True)

    return {
        'config': config_file,
        'workspace': workspace,
        'workbook': workbook_name,
        'inputs': inputs_folder,
        'logs': logs_folder,
        'start': start_date if start_date else None,
        'end': end_date if end_date else None,
        'ml_inference': ml_inference
    }


def get_ml_training_config():
    """Get ML training configuration interactively from user."""
    notes = get_user_input("Training notes (optional)", "")
    bump_type = get_user_input("Version bump type (major/minor/patch)", "minor")
    return notes, bump_type