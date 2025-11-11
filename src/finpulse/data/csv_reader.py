"""CSV reading utilities."""

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .file_collector import collect_files_case_insensitive


def read_csv_robust(path: Path, cfg: dict) -> pd.DataFrame:
    """Read CSV with robust error handling and configuration."""
    kwargs = {
        "engine": cfg.get("csv_engine", "python"),
        "sep": cfg.get("csv_sep", ","),
        "encoding": cfg.get("encoding", "utf-8-sig"),
        "quotechar": '"',
        "doublequote": True,
        "escapechar": "\\",
        "skipinitialspace": False,
        "index_col": False,
        "on_bad_lines": cfg.get("csv_on_bad_lines", "warn"),
        "header": 0 if not cfg.get("csv_names") else 0,
    }
    
    if cfg.get("csv_dtypes") is not None:
        kwargs["dtype"] = cfg.get("csv_dtypes")
    if cfg.get("csv_usecols") is not None:
        kwargs["usecols"] = cfg.get("csv_usecols")
    if cfg.get("csv_names") is not None:
        kwargs["names"] = cfg.get("csv_names")
    
    try:
        return pd.read_csv(path, **kwargs)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        logging.error(f"Failed to read CSV file {path}: {e}")
        raise


def load_inputs_for_source(src_cfg: dict) -> pd.DataFrame:
    """Load and combine all input files for a source."""
    files = []
    for pattern in src_cfg.get("files", []):
        files.extend(collect_files_case_insensitive(pattern))
    
    print(f"  matched {len(files)} file(s)")
    for p in files:
        print(f"    - {p}")
    
    frames = []
    for p in files:
        ext = p.suffix.lower()
        if ext in [".csv", ".txt"]:
            df = read_csv_robust(p, src_cfg)
            df["__source_file"] = str(p)
            frames.append(df)
    
    if frames:
        print(f"  loaded rows: {sum(len(f) for f in frames)}")
    else:
        print("  no frames loaded")
    
    if not frames:
        return pd.DataFrame()
    
    # Filter out empty DataFrames to avoid FutureWarning
    non_empty_frames = [df for df in frames if not df.empty]
    
    if not non_empty_frames:
        return pd.DataFrame()
    
    try:
        return pd.concat(non_empty_frames, ignore_index=True)
    except (ValueError, pd.errors.InvalidIndexError) as e:
        logging.error(f"Failed to concatenate dataframes: {e}")
        raise


def load_inputs_by_file(src_cfg: dict) -> List[pd.DataFrame]:
    """Load input files separately for individual processing."""
    files = []
    for pattern in src_cfg.get("files", []):
        files.extend(collect_files_case_insensitive(pattern))
    
    print(f"  matched {len(files)} file(s)")
    for p in files:
        print(f"    - {p}")
    
    frames = []
    for p in files:
        ext = p.suffix.lower()
        if ext in [".csv", ".txt"]:
            df = read_csv_robust(p, src_cfg)
            df["__source_file"] = str(p)
            if not df.empty:
                frames.append(df)
    
    return frames