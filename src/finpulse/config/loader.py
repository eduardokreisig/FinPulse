"""Configuration file loading and validation."""

import logging
from pathlib import Path
from typing import Dict, Any

import yaml

from ..utils.path_utils import validate_path

# loader.py lives at src/finpulse/config/loader.py — 3 levels up is the project root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate configuration file."""
    try:
        validated_path = validate_path(Path(config_path))
        cfg = yaml.safe_load(validated_path.read_text())
        return cfg
    except (FileNotFoundError, PermissionError, yaml.YAMLError, ValueError) as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        raise


def get_target_workbook_path(cfg: Dict[str, Any]) -> Path:
    """Get and validate target workbook path from config."""
    try:
        return validate_path(Path(cfg["target_workbook"]).expanduser())
    except (KeyError, ValueError) as e:
        logging.error(f"Invalid target_workbook in config: {e}")
        raise


def get_log_directory(cfg: Dict[str, Any], log_dir_arg: str = None) -> Path | None:
    """Get and validate log directory path."""
    if log_dir_arg or cfg.get("log_dir"):
        try:
            return validate_path(Path(log_dir_arg or cfg.get("log_dir", "")).expanduser())
        except (ValueError, OSError) as e:
            # If path validation fails, try to create a simple Path without validation
            logging.warning(f"Path validation failed, using simple path: {e}")
            return Path(log_dir_arg or cfg.get("log_dir", "")).expanduser().resolve()
    return None


def load_details_sheet(cfg: Dict[str, Any]) -> str:
    """Load details sheet name from config."""
    try:
        return cfg["details_sheet"]
    except KeyError:
        raise ValueError("Missing required config key: details_sheet")


def load_workbook_columns(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Load and validate workbook column name configuration. Raises if any key is missing."""
    try:
        columns = cfg["workbook"]["columns"]
    except KeyError as e:
        raise ValueError(f"Missing required config section: workbook.columns (key {e})")

    required_keys = [
        "bank", "account", "date", "description", "withdrawals", "deposits",
        "transaction_type", "accrual_period", "human_verified", "notes",
        "category", "subcategory", "automated_category",
    ]
    missing = [k for k in required_keys if k not in columns]
    if missing:
        raise ValueError(f"Missing required workbook.columns config keys: {missing}")

    return columns


def load_transaction_type_labels(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Load and validate transaction type label configuration. Raises if any key is missing."""
    try:
        labels = cfg["workbook"]["transaction_type_labels"]
    except KeyError as e:
        raise ValueError(f"Missing required config section: workbook.transaction_type_labels (key {e})")

    required_keys = ["withdrawal", "deposit"]
    missing = [k for k in required_keys if k not in labels]
    if missing:
        raise ValueError(f"Missing required workbook.transaction_type_labels config keys: {missing}")

    return labels


def load_ml_paths(cfg: Dict[str, Any]) -> tuple[Path, str]:
    """Load and validate ML model path configuration. Raises if any key is missing.
    Relative paths are resolved against the project root, not cwd."""
    try:
        ml_cfg = cfg["ml"]
        models_dir_cfg = Path(ml_cfg["models_dir"])
        metadata_file = ml_cfg["metadata_file"]
    except KeyError as e:
        raise ValueError(f"Missing required config key: ml.{e}")

    models_dir = models_dir_cfg if models_dir_cfg.is_absolute() else (_PROJECT_ROOT / models_dir_cfg).resolve()
    return models_dir, metadata_file