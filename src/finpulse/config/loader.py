"""Configuration file loading and validation."""

import logging
from pathlib import Path
from typing import Dict, Any

import yaml

from ..utils.path_utils import validate_path


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


def get_log_directory(cfg: Dict[str, Any], log_dir_arg: str = None) -> Path:
    """Get and validate log directory path."""
    if log_dir_arg or cfg.get("log_dir"):
        return validate_path(Path(log_dir_arg or cfg.get("log_dir", "")).expanduser())
    return None