"""Date parsing and conversion utilities."""

import logging
import re
from datetime import datetime
from typing import Any, Optional

import pandas as pd


# Compiled regex patterns for performance
MMDD_PATTERN = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b")
ISO_PATTERN = re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b")
MONTH_PATTERN = re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", re.IGNORECASE)
DATE_SEARCH_PATTERN = re.compile(r"date", re.IGNORECASE)
DATE_EXTRACT_PATTERNS = [
    (re.compile(r"(\d{1,2}/\d{1,2}/\d{4})"), "%m/%d/%Y"),
    (re.compile(r"(\d{1,2}/\d{1,2}/\d{2})"), "%m/%d/%y"),
    (re.compile(r"(\d{4}-\d{1,2}-\d{1,2})"), None)
]


def date_like_ratio(series: pd.Series) -> float:
    """Calculate ratio of date-like values in a pandas Series."""
    s = series.astype(str).fillna("")
    mmdd = s.str.contains(MMDD_PATTERN, na=False)
    iso = s.str.contains(ISO_PATTERN, na=False)
    monthwrd = s.str.contains(MONTH_PATTERN, na=False)
    return float((mmdd | iso | monthwrd).mean())


def robust_parse_dates(series: pd.Series, date_format: Optional[str]) -> pd.Series:
    """Parse dates with multiple fallback formats."""
    s = series.astype(str).str.strip()
    if date_format:
        try:
            # Smart year truncation: convert 4-digit years to 2-digit for %y format
            if "%y" in date_format and "%Y" not in date_format:
                s = s.str.replace(r"/(\d{2})(\d{2})$", r"/\2", regex=True)
            return pd.to_datetime(s, errors="coerce", format=date_format)
        except (ValueError, TypeError) as e:
            logging.warning(f"Failed to parse dates with format {date_format}: {e}")
            return pd.to_datetime(s, errors="coerce")
    
    try:
        dt = pd.to_datetime(s, errors="coerce")
    except (ValueError, TypeError) as e:
        logging.warning(f"Failed to parse dates: {e}")
        return pd.Series([pd.NaT] * len(s))
    
    # Use cached patterns for better performance
    for pattern, fmt in DATE_EXTRACT_PATTERNS:
        if dt.isna().mean() > 0.25:
            extracted = s.str.extract(pattern, expand=False)
            if fmt:
                dt = dt.fillna(pd.to_datetime(extracted, errors="coerce", format=fmt))
            else:
                dt = dt.fillna(pd.to_datetime(extracted, errors="coerce"))
    return dt


def try_coerce_excel_date(value: Any) -> Any:
    """Try to coerce a value to an Excel-compatible date."""
    if value is None:
        return None
    s = str(value).strip()
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%m-%d-%y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            pass
    return value


def to_iso_dateish(v: Any) -> str:
    """Convert value to ISO date string."""
    d = try_coerce_excel_date(v)
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    try:
        return str(d)
    except (ValueError, TypeError) as e:
        logging.warning(f"Failed to convert date to string: {e}")
        return ""