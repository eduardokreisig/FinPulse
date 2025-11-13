"""Data normalization and column mapping."""

from typing import List, Optional, Tuple

import pandas as pd

from ..utils.date_utils import date_like_ratio, robust_parse_dates


# Column candidates for auto-detection
DATE_CANDIDATES = ["date", "transaction date", "post date", "posted date", "posting date", "trans date"]
DESC_CANDIDATES = ["description", "details", "memo", "payee", "name", "narrative", "transaction description"]
DEBIT_CANDIDATES = ["debit", "withdrawal", "withdrawals", "outflow", "charge"]
CREDIT_CANDIDATES = ["credit", "deposit", "deposits", "inflow", "payment"]
AMOUNT_CANDIDATES = ["amount", "transaction amount", "amt"]


def clean_string(s: Optional[str]) -> str:
    """Clean and normalize string for comparison."""
    if s is None:
        return ""
    return (
        str(s)
        .replace("\ufeff", "")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
        .strip()
        .lower()
    )


def choose_col_ci(cols: List[str], candidates: List[str]) -> Optional[str]:
    """Choose column using case-insensitive matching."""
    cmap = {clean_string(c): c for c in cols}
    for cand in candidates:
        k = clean_string(cand)
        if k in cmap:
            return cmap[k]
    return None


def resolve_col(df: pd.DataFrame, declared: Optional[str], fallback_cands: List[str]) -> Tuple[str, pd.Series]:
    """Resolve column name using declared name or fallback candidates."""
    cols = list(df.columns)
    if declared:
        norm = clean_string(declared)
        for c in cols:
            if clean_string(c) == norm:
                return c, df[c]
    cand = choose_col_ci(cols, fallback_cands)
    if cand:
        return cand, df[cand]
    return cols[0], df[cols[0]]


def resolve_multiple_cols(df: pd.DataFrame, config: dict, col_mappings: dict) -> dict:
    """Resolve multiple columns at once using configuration."""
    results = {}
    # Pre-compute column mapping for efficiency
    cols = list(df.columns)
    cmap = {clean_string(c): c for c in cols}
    
    for key, (declared_key, candidates) in col_mappings.items():
        declared = config.get(declared_key)
        if declared:
            norm = clean_string(declared)
            if norm in cmap:
                col_name = cmap[norm]
                results[key] = (col_name, df[col_name])
                continue
        
        # Fallback to candidates
        found = False
        for cand in candidates:
            k = clean_string(cand)
            if k in cmap:
                col_name = cmap[k]
                results[key] = (col_name, df[col_name])
                found = True
                break
        
        if not found and cols:
            results[key] = (cols[0], df[cols[0]])
    
    return results


def apply_column_mapping(df: pd.DataFrame, mapping: Optional[dict]) -> pd.DataFrame:
    """Apply column name mapping if provided."""
    if not mapping:
        return df

    fixed = {}
    inv = {clean_string(k): v for k, v in mapping.items()}
    for c in df.columns:
        k = clean_string(c)
        if k in inv:
            fixed[c] = inv[k]

    return df.rename(columns=fixed) if fixed else df


def calculate_amount(df: pd.DataFrame, norm_cfg: dict, amount_col: Optional[str]) -> pd.Series:
    """Calculate amount from various column configurations."""
    if amount_col:
        return pd.to_numeric(df[amount_col], errors="coerce").fillna(0.0)

    debit = norm_cfg.get("debit_col") or choose_col_ci(list(df.columns), DEBIT_CANDIDATES)
    credit = norm_cfg.get("credit_col") or choose_col_ci(list(df.columns), CREDIT_CANDIDATES)

    if not debit and not credit:
        fallback_col = choose_col_ci(list(df.columns), AMOUNT_CANDIDATES)
        return pd.to_numeric(df.get(fallback_col, 0), errors="coerce").fillna(0.0)

    d = pd.to_numeric(df.get(debit, 0), errors="coerce").fillna(0.0)
    c = pd.to_numeric(df.get(credit, 0), errors="coerce").fillna(0.0)

    if norm_cfg.get("debit_credit_are_signed", True):
        return d + c
    else:
        return c - d


def normalize(df_in: pd.DataFrame, norm_cfg: dict) -> pd.DataFrame:
    """Normalize DataFrame columns and data types."""
    df = apply_column_mapping(df_in.copy(), norm_cfg.get("columns"))

    # Resolve columns using the new helper function
    col_mappings = {
        'date': ('date_col', DATE_CANDIDATES),
        'desc': ('description_col', DESC_CANDIDATES)
    }
    resolved = resolve_multiple_cols(df, norm_cfg, col_mappings)
    date_name, date_raw = resolved['date']
    desc_name, desc_raw = resolved['desc']
    
    # Handle automated transaction category column
    automated_cat_col = norm_cfg.get("automated_trans_cat_col")
    automated_cat_raw = None
    if automated_cat_col and automated_cat_col in df.columns:
        automated_cat_raw = df[automated_cat_col]

    # If a specific amount_col is declared, use it; else infer
    amount_col = None
    declared_amt = norm_cfg.get("amount_col")
    if declared_amt and declared_amt in df.columns:
        amount_col = declared_amt
    else:
        guess = choose_col_ci(list(df.columns), AMOUNT_CANDIDATES)
        if guess:
            amount_col = guess

    # Validate date column; if not date-like, scan all columns and pick best
    ratio = date_like_ratio(date_raw)
    if ratio < 0.30:
        best_name, best_ratio = date_name, ratio
        for c in df.columns:
            col_ratio = date_like_ratio(df[c])
            if col_ratio > best_ratio:
                best_name, best_ratio = c, col_ratio
        if best_ratio > ratio:
            date_name, date_raw, ratio = best_name, df[best_name], best_ratio

    print(
        f"  date_col picked: {date_name}; sample raw -> "
        f"{date_raw.astype(str).head(5).tolist()} (date-like={ratio:.2f})"
    )

    date_series = robust_parse_dates(date_raw, norm_cfg.get("date_format"))
    amount = calculate_amount(df, norm_cfg, amount_col)

    # Optional sign refinement
    sign_from = norm_cfg.get("sign_from")
    if sign_from and isinstance(sign_from, dict):
        col = sign_from.get("column")
        if col and col in df.columns:
            deb_kw = [k.lower() for k in sign_from.get("debit_keywords", [])]
            cre_kw = [k.lower() for k in sign_from.get("credit_keywords", [])]
            types = df[col].astype(str).str.lower().fillna("")
            mask_deb = types.apply(lambda s: any(k in s for k in deb_kw))
            mask_cre = types.apply(lambda s: any(k in s for k in cre_kw))
            amount = amount.mask(mask_deb & (amount >= 0), -amount.abs())
            amount = amount.mask(mask_cre & (amount <= 0), amount.abs())

    out = pd.DataFrame({
        "date": pd.to_datetime(date_series, errors="coerce"),
        "amount": pd.to_numeric(amount, errors="coerce").fillna(0.0).round(2),
        "description": desc_raw.astype(str).map(lambda x: " ".join(x.split())),
    })
    
    # Add automated transaction category if available
    if automated_cat_raw is not None:
        out["automated_trans_category"] = automated_cat_raw.fillna("").astype(str)
    
    out["source_file"] = df.get("__source_file", "")
    return out