"""Excel sheet insertion operations."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from openpyxl.formula.translate import Translator


from ..utils.date_utils import DATE_SEARCH_PATTERN, to_iso_dateish
from .workbook import (
    copy_row_styles, find_insert_index, header_map, header_to_index,
    load_workbook_safe, save_workbook_safe, should_skip_write
)


def copy_formulas_to_row(ws, src_row: int, dst_row: int, max_col: int = None) -> None:
    """Copy and translate formulas from source row to destination row."""
    max_col = max_col or ws.max_column
    for c in range(1, max_col + 1):
        src = ws.cell(row=src_row, column=c)
        dst = ws.cell(row=dst_row, column=c)
        if isinstance(src.value, str) and src.value.startswith("="):
            try:
                # Only translate if it's a simple formula, skip complex ones
                if len(src.value) < 100 and not any(x in src.value.upper() for x in ['INDIRECT', 'OFFSET', 'INDEX']):
                    dst.value = Translator(src.value, origin=src.coordinate).translate_formula(dst.coordinate)
                else:
                    # For complex formulas, just copy as-is to avoid corruption
                    dst.value = src.value
            except (AttributeError, ValueError, KeyError, TypeError) as e:
                # If translation fails, copy the original formula
                dst.value = src.value
                logging.debug(f"Skipped formula translation for {src.coordinate}: {e}")


def calculate_amount_from_withdrawals_deposits(w_amt: float, d_amt: float) -> float:
    """Calculate net amount from withdrawal and deposit amounts."""
    # With negative withdrawals format: just return whichever is non-zero
    w_amt = float(w_amt or 0.0)
    d_amt = float(d_amt or 0.0)
    return w_amt if w_amt != 0.0 else d_amt


def build_dedup_key(bank: str, account: str, date, description: str, amount: float) -> tuple:
    """Build standardized deduplication key."""
    return (str(bank), str(account), date, norm_key(description), round(float(amount), 2))


def norm_key(s: Optional[str]) -> str:
    """Normalize key for comparison."""
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


def fix_shifted_formulas(ws, col_acc_period: int) -> None:
    """Fix formulas that were incorrectly shifted by Excel's automatic adjustment."""
    if not col_acc_period:
        return
    
    for row_idx in range(2, ws.max_row + 1):
        cell = ws.cell(row=row_idx, column=col_acc_period)
        if isinstance(cell.value, str) and cell.value.startswith("="):
            # Look for DATE formulas with cell references
            pattern = r'=DATE\(YEAR\(C(\d+)\),\s*MONTH\(C(\d+)\),\s*1\)'
            match = re.match(pattern, cell.value)
            if match:
                ref_row1, ref_row2 = int(match.group(1)), int(match.group(2))
                # If both references point to the same row but not the current row, fix it
                if ref_row1 == ref_row2 and ref_row1 != row_idx:
                    corrected_formula = f"=DATE(YEAR(C{row_idx}), MONTH(C{row_idx}), 1)"
                    cell.value = corrected_formula


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
        
        # Skip empty rows
        if not any([b, a, d]):
            continue
            
        if hasattr(d, "date"):
            d = d.date()
        desc = norm_key(ws.cell(row=row_idx, column=col_desc).value)
        # Get amount for deduplication key
        w_amt = ws.cell(row=row_idx, column=col_w).value or 0.0
        d_amt = ws.cell(row=row_idx, column=col_d).value or 0.0
        amt = calculate_amount_from_withdrawals_deposits(w_amt, d_amt)
        existing_keys.add(build_dedup_key(b, a, d, desc, amt))

    rows_sorted = sorted(rows, key=lambda r: (bank_label, account_label, r["date"]))
    added = 0
    
    for row_data in rows_sorted:
        dkey = row_data["date"].date() if hasattr(row_data["date"], "date") else row_data["date"]
        amt = float(row_data["amount"] or 0.0)
        key = build_dedup_key(bank_label, account_label, dkey, row_data["description"], amt)
        if key in existing_keys:
            continue

        if dry:
            added += 1
            continue

        ins_at = find_insert_index(ws, (bank_label, account_label, dkey), h["Bank"], h["Account"], h["Date"])
        ws.insert_rows(ins_at, 1)
        src_row = ins_at - 1 if ins_at > 2 else ins_at + 1
        copy_row_styles(ws, src_row, ins_at)
        
        # Copy formulas from source row
        copy_formulas_to_row(ws, src_row, ins_at)

        def safe_set(ci, value):
            if ci and not should_skip_write(ws, ins_at, ci):
                ws.cell(row=ins_at, column=ci).value = value

        safe_set(col_bank, bank_label)
        safe_set(col_account, account_label)
        safe_set(col_date, dkey)
        safe_set(col_desc, row_data["description"])

        amt = float(row_data["amount"] or 0.0)
        if amt < 0:
            safe_set(col_w, amt)  # Keep negative value
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
        
        # Skip formula updates in existing rows to prevent corruption
        # Excel will automatically adjust most formulas when rows are inserted

    # Fix any formulas that were incorrectly shifted by Excel
    if not dry and added > 0:
        fix_shifted_formulas(ws, col_acc_period)
        save_workbook_safe(wb, validated_xlsx)
    elif not dry:
        save_workbook_safe(wb, validated_xlsx)
    return added


def insert_into_account_sheet(xlsx_path: Path, sheet_name: str, bank_label: str, account_label: str,
                             rows: List[Dict[str, Any]], raw_map: Optional[Dict[str, str]], 
                             source_config: Optional[Dict[str, Any]] = None, dry: bool = False) -> int:
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

    # Build existing dedupe keys using YAML config or fallback to hardcoded priority
    chosen = None
    
    # Try YAML-configured columns first
    if source_config:
        date_col = source_config.get("date_col")
        desc_col = source_config.get("description_col")
        
        if date_col and desc_col and date_col in raw_cols_indices and desc_col in raw_cols_indices:
            # Check for amount vs debit/credit
            if "Amount" in raw_cols_indices:
                chosen = [date_col, desc_col, "Amount"]
            elif source_config.get("debit_col") and source_config.get("credit_col"):
                debit_col = source_config.get("debit_col")
                credit_col = source_config.get("credit_col")
                if debit_col in raw_cols_indices and credit_col in raw_cols_indices:
                    chosen = [date_col, desc_col, debit_col, credit_col]
    
    # Fallback to hardcoded priority if YAML config didn't work
    if not chosen:
        prefer = [
            ["Date", "Description", "Amount"],
            ["Date", "Description", "Debit", "Credit"],
            ["Posting Date", "Description", "Amount"],
            ["Posting Date", "Description", "Debit", "Credit"],
            ["Post Date", "Description", "Amount"],
            ["Post Date", "Description", "Debit", "Credit"],
        ]
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
            elif n in ["Debit", "Credit"]:
                # For existing Debit/Credit, use the actual value or 0
                key_parts.append(str(float(cell_val or 0)))
            else:
                key_parts.append(norm_key(cell_val))
        return tuple(key_parts)

    existing = set()
    if chosen:
        for row_index in range(2, ws.max_row + 1):
            existing.add(existing_key(row_index))

    # Find actual last row with data
    last_data_row = 1
    for r_idx in range(ws.max_row, 1, -1):
        bank_val = ws.cell(row=r_idx, column=col_bank).value if col_bank else None
        account_val = ws.cell(row=r_idx, column=col_account).value if col_account else None
        if bank_val or account_val:
            last_data_row = r_idx
            break
    
    # Find a row with formulas to copy from
    formula_source_row = last_data_row
    for r_idx in range(last_data_row, 1, -1):
        has_formula = False
        for c in range(1, min(11, ws.max_column + 1)):
            c_val = ws.cell(row=r_idx, column=c).value
            if isinstance(c_val, str) and c_val.startswith("="):
                has_formula = True
                break
        if has_formula:
            formula_source_row = r_idx
            break

    added = 0
    for row_data in rows:
        key = None
        if chosen and raw_map and all(col in raw_map for col in chosen):
            row_key_parts = []
            for n in chosen:
                if DATE_SEARCH_PATTERN.search(n):
                    row_key_parts.append(pd.to_datetime(row_data["date"]).strftime("%Y-%m-%d"))
                elif "description" in n.lower():
                    row_key_parts.append(norm_key(row_data["description"]))
                elif n in ["Debit", "Credit"]:
                    # For Debit/Credit, use the normalized amount
                    if n == "Debit" and row_data["amount"] < 0:
                        row_key_parts.append(str(float(row_data["amount"])))
                    elif n == "Credit" and row_data["amount"] >= 0:
                        row_key_parts.append(str(float(row_data["amount"])))
                    else:
                        row_key_parts.append("0.0")
                else:
                    row_key_parts.append(norm_key(row_data.get("__raw__", {}).get(raw_map[n], "")))
            key = tuple(row_key_parts)
        if key and key in existing:
            continue

        if dry:
            added += 1
            continue

        # Insert after last data row
        ins_at = last_data_row + 1
        ws.insert_rows(ins_at, 1)
        
        # Copy styles and formulas from a row that has formulas
        copy_row_styles(ws, formula_source_row, ins_at)
        copy_formulas_to_row(ws, formula_source_row, ins_at, min(ws.max_column, 10))
        
        last_data_row = ins_at  # Update for next insertion

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

        added += 1

    if not dry:
        save_workbook_safe(wb, validated_xlsx)
    return added