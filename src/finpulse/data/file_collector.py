"""File collection and discovery utilities."""

import logging
from pathlib import Path
from typing import List

from ..utils.path_utils import validate_path


def collect_files_case_insensitive(pattern: str) -> List[Path]:
    """Collect files matching pattern with case-insensitive matching."""
    base = Path(pattern)
    # Validate the base pattern path
    try:
        base = validate_path(base)
    except ValueError as e:
        logging.warning(f"Invalid file pattern {pattern}: {e}")
        return []
    
    exts_ok = {".csv", ".txt", ".ofx", ".qfx"}
    if base.is_dir():
        return [validate_path(p) for p in base.iterdir() if p.is_file() and p.suffix.lower() in exts_ok]
    
    parent = base.parent if base.parent != Path("") else Path(".")
    name = base.name
    hits = []
    
    try:
        if any(ch in name for ch in "*?["):
            try:
                for p in parent.glob("*"):
                    if p.is_file() and p.suffix.lower() in exts_ok:
                        hits.append(p)
            except (OSError, PermissionError) as e:
                logging.warning(f"Failed to glob files in {parent}: {e}")
        else:
            if parent.exists():
                for p in parent.iterdir():
                    if p.name.lower() == name.lower():
                        try:
                            hits.append(validate_path(p))
                        except ValueError as e:
                            logging.warning(f"Skipping invalid path {p}: {e}")
    except (OSError, FileNotFoundError, PermissionError) as e:
        logging.warning(f"Failed to collect files from pattern {pattern}: {e}")
    
    if not hits:
        try:
            hits = list(parent.glob(name))
        except (OSError, PermissionError) as e:
            logging.warning(f"Failed to glob pattern {name} in {parent}: {e}")
    
    # Validate all collected paths
    validated_hits = []
    for p in hits:
        if p.suffix.lower() in exts_ok:
            try:
                validated_hits.append(validate_path(p))
            except ValueError as e:
                logging.warning(f"Skipping invalid path {p}: {e}")
    return validated_hits