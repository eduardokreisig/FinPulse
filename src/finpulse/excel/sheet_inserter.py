"""Excel sheet insertion operations."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from openpyxl.formula.translate import Translator

from ..data.normalizer import clean_string
from ..utils.date_utils import DATE_SEARCH_PATTERN, to_iso_dateish
from .workbook import (
    copy_row_styles, find_insert_index, header_map, header_to_index,
    load_workbook_safe, save_workbook_safe, should_skip_write
)


def norm_key(s: Optional[str]) -> str:
    """Normalize key for comparison."""
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


def insert_into_details(xlsx_path: Path, sheet_name: str, bank_label: str, 
                       account_label: str, rows: List[Dict[str, Any]], dry: bool = False) -> int:
    """Insert rows into the Details sheet."""
    if not rows:
        return 0
    
    wb, validated_xlsx = load_workbook_safe(xlsx_path)
    
    if sheet_name not in wb.sheetnames:
        wb.close()
        raise RuntimeError(f"Sheet '{sheet_name}' not found")
    
    ws = wb[sheet_name]
    h = header_map(ws)

    col_bank = h.get("Bank")
    col_account = h.get("Account")
    col_date = h.get("Date")
    col_desc = h.get("Transaction Description")
    col_w = h.get("Withdrawals")
    col_d = h.get("Deposits")
    col_type = h.get("Transaction Type")
    col_acc_period = h.get("Accrual period")
    col_rev = h.get("Reviewed by Eduardo")
    col_notes = h.get("Notes")
    col_type_manual = h.get("Type")

    existing_keys = set()
    for row_idx in range(2, ws.max_row + 1):
        b = (ws.cell(row=row_idx, column=col_bank).value or "")
        a = (ws.cell(row=row_idx, column=col_account).value or "")
        d = ws.cell(row=row_idx, column=col_date).value
        if hasattr(d, "date"):
            d = d.date()
        desc = norm_key(ws.cell(row=row_idx, column=col_desc).value)
        existing_keys.add((str(b), str(a), d, desc))

    rows_sorted = sorted(rows, key=lambda r: (bank_label, account_label, r["date"]))
    added = 0
    
    for row_data in rows_sorted:
        dkey = row_data["date"].date() if hasattr(row_data["date"], "date") else row_data["date"]
        key = (bank_label, account_label, dkey, norm_key(row_data["description"]))
        if key in existing_keys:
            continue

        if dry:
            added += 1
            continue

        ins_at = find_insert_index(ws, (bank_label, account_label, dkey), h["Bank"], h["Account"], h["Date"])
        ws.insert_rows(ins_at, 1)
        src_row = ins_at - 1 if ins_at > 2 else ins_at + 1
        copy_row_styles(ws, src_row, ins_at)

        def safe_set(ci, value):
            if ci and not should_skip_write(ws, ins_at, ci):
                ws.cell(row=ins_at, column=ci).value = value

        safe_set(col_bank, bank_label)
        safe_set(col_account, account_label)
        safe_set(col_date, dkey)
        safe_set(col_desc, row_data["description"])

        amt = float(row_data["amount"] or 0.0)
        if amt < 0:
            safe_set(col_w, abs(amt))
            safe_set(col_d, 0.0)
            safe_set(col_type, "Withdrawal")
        else:
            safe_set(col_w, 0.0)
            safe_set(col_d, amt)
            safe_set(col_type, "Deposit")

        if col_acc_period and hasattr(dkey, "replace") and not should_skip_write(ws, ins_at, col_acc_period):
            ws.cell(row=ins_at, column=col_acc_period).value = dkey.replace(day=1)
        if col_rev and not should_skip_write(ws, ins_at, col_rev):
            ws.cell(row=ins_at, column=col_rev).value = "No"
        if col_notes and not should_skip_write(ws, ins_at, col_notes):
            ws.cell(row=ins_at, column=col_notes).value = None
        if col_type_manual and not should_skip_write(ws, ins_at, col_type_manual):
            ws.cell(row=ins_at, column=col_type_manual).value = None

        added += 1
        existing_keys.add(key)

    if not dry:
        save_workbook_safe(wb, validated_xlsx)
    return added


def insert_into_account_sheet(xlsx_path: Path, sheet_name: str, bank_label: str, account_label: str,
                             rows: List[Dict[str, Any]], raw_map: Optional[Dict[str, str]], dry: bool = False) -> int:
    """Insert rows into account-specific sheet."""
    if not rows:
        return 0
    
    wb, validated_xlsx = load_workbook_safe(xlsx_path)
    
    if sheet_name not in wb.sheetnames:
        wb.close()
        raise RuntimeError(f"Sheet '{sheet_name}' not found")
    
    ws = wb[sheet_name]
    h = header_to_index(ws)

    col_bank = h.get("Bank")
    col_account = h.get("Account")

    raw_cols_indices = {}
    for c in range(11, ws.max_column + 1):
        name = ws.cell(row=1, column=c).value
        if isinstance(name, str) and name.strip():
            raw_cols_indices[name.strip()] = c

    # Build existing dedupe keys using best available K+ trio
    prefer = [
        ["Date", "Description", "Amount"],
        ["Posting Date", "Description", "Amount"],
        ["Post Date", "Description", "Amount"],
    ]
    chosen = None
    for group in prefer:
        if all(n in raw_cols_indices for n in group):
            chosen = group
            break

    def existing_key(row_idx: int):
        key_parts = []
        for n in chosen or []:
            cell_val = ws.cell(row=row_idx, column=raw_cols_indices[n]).value
            if DATE_SEARCH_PATTERN.search(n):
                key_parts.append(to_iso_dateish(cell_val))
            else:
                key_parts.append(norm_key(cell_val))
        return tuple(key_parts)

    existing = set()
    if chosen:
        for row_index in range(2, ws.max_row + 1):
            existing.add(existing_key(row_index))

    added = 0
    for row_data in rows:
        key = None
        if chosen and raw_map and all(col in raw_map for col in chosen):
            row_key_parts = []
            for n in chosen:
                if DATE_SEARCH_PATTERN.search(n):
                    row_key_parts.append(pd.to_datetime(row_data["date"]).strftime("%Y-%m-%d"))
                else:
                    row_key_parts.append(norm_key(row_data.get("__raw__", {}).get(raw_map[n], "")))
            key = tuple(row_key_parts)
        if key and key in existing:
            continue

        if dry:
            added += 1
            continue

        ins_at = ws.max_row + 1
        ws.insert_rows(ins_at, 1)
        src_row = ins_at - 1 if ins_at > 2 else ins_at + 1
        copy_row_styles(ws, src_row, ins_at)

        # copy formulas only for A..J
        for c in range(1, min(ws.max_column, 10) + 1):
            src = ws.cell(row=src_row, column=c)
            dst = ws.cell(row=ins_at, column=c)
            if isinstance(src.value, str) and src.value.startswith("="):
                try:
                    dst.value = Translator(src.value, origin=src.coordinate).translate_formula(dst.coordinate)
                except (AttributeError, ValueError, KeyError) as e:
                    logging.warning(f"Failed to translate formula: {e}")

        if isinstance(col_bank, int) and not should_skip_write(ws, ins_at, col_bank):
            ws.cell(row=ins_at, column=col_bank).value = bank_label
        if isinstance(col_account, int) and not should_skip_write(ws, ins_at, col_account):
            ws.cell(row=ins_at, column=col_account).value = account_label

        for sheet_header, csv_col in (raw_map or {}).items():
            ci = raw_cols_indices.get(sheet_header)
            if not ci:
                continue
            cell_value = row_data.get("__raw__", {}).get(csv_col)
            if DATE_SEARCH_PATTERN.search(sheet_header):
                try:
                    cell_value = pd.to_datetime(cell_value).date()
                except (ValueError, TypeError):
                    pass
            if not should_skip_write(ws, ins_at, ci):
                ws.cell(row=ins_at, column=ci).value = cell_value

        if key:
            existing.add(key)
        added += 1

    if not dry:
        save_workbook_safe(wb, validated_xlsx)
    return added