"""Path validation and utilities."""

import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


def validate_path(path: Path, allowed_base: Optional[Path] = None) -> Path:
    """Validate and resolve path, optionally checking it's within allowed base directory."""
    try:
        resolved = path.resolve(strict=False)
        if allowed_base:
            try:
                allowed_resolved = allowed_base.resolve(strict=False)
                if not str(resolved).startswith(str(allowed_resolved)):
                    raise ValueError(f"Path {path} is outside allowed directory {allowed_base}")
            except (OSError, RuntimeError) as e:
                raise ValueError(f"Cannot resolve allowed base path {allowed_base}: {e}")
        return resolved
    except (OSError, RuntimeError, ValueError) as e:
        raise ValueError(f"Invalid path {path}: {e}")


def get_timestamp(p: Path) -> str:
    """Get formatted timestamp for a file."""
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))
    except (OSError, FileNotFoundError, ValueError) as e:
        logging.warning(f"Failed to get timestamp for {p}: {e}")
        return "n/a"


def create_timestamped_copy(original_path: Path) -> Path:
    """Create a timestamped copy of the original file."""
    if not original_path.exists():
        raise FileNotFoundError(f"Original file does not exist: {original_path}")
    
    # Generate ISO 8601 timestamp with local timezone, replacing colons with hyphens for filename compatibility
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S.%f")[:-3]  # Remove last 3 digits from microseconds
    
    # Create new filename: <original_name> <timestamp>.<extension>
    stem = original_path.stem
    suffix = original_path.suffix
    new_name = f"{stem} {timestamp}{suffix}"
    copy_path = original_path.parent / new_name
    
    try:
        shutil.copy2(original_path, copy_path)
        logging.info(f"Created timestamped copy: {copy_path}")
        return copy_path
    except (OSError, PermissionError) as e:
        logging.error(f"Failed to create timestamped copy: {e}")
        raise