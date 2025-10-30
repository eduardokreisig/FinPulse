"""Path validation and utilities."""

import logging
import time
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