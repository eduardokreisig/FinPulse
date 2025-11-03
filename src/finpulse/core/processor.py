"""Core data processing logic."""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
from openpyxl import load_workbook

from ..data.csv_reader import load_inputs_for_source
from ..data.normalizer import normalize
from ..excel.sheet_inserter import insert_into_account_sheet, insert_into_details


def process_source(src_name: str, scfg: dict, xlsx: Path, details_sheet: str, args) -> Tuple[int, int, int, int, int]:
    """Process a single data source."""
    print(f"\n=== Source: {src_name} ===")
    df_in = load_inputs_for_source(scfg)
    print(f"  df_in rows: {len(df_in)}")

    if df_in.empty:
        # Still count existing records even if no new data to ingest
        account_sheet = scfg.get("account_sheet")
        if account_sheet and xlsx.exists():
            try:
                wb = load_workbook(xlsx, read_only=True)
                if account_sheet in wb.sheetnames:
                    ws = wb[account_sheet]
                    # Count non-empty rows (skip header)
                    existing_count = 0
                    for row_idx in range(2, ws.max_row + 1):
                        # Check if row has any data
                        has_data = False
                        for col_idx in range(1, min(ws.max_column + 1, 15)):  # Check first 15 columns
                            if ws.cell(row=row_idx, column=col_idx).value:
                                has_data = True
                                break
                        if has_data:
                            existing_count += 1
                    wb.close()
                    print(f"  -> no new data, but found {existing_count} existing records")
                    return 0, 0, 0, 0, existing_count
                wb.close()
            except Exception as e:
                logging.warning(f"Failed to count existing records for {src_name}: {e}")
        return 0, 0, 0, 0, 0

    # show headers early for debugging
    print(f"  CSV headers (after parse): {list(df_in.columns)}")

    account_sheet = scfg.get("account_sheet")
    raw_map = scfg.get("raw_map")

    if scfg.get("auto_raw_from_sheet", False):
        try:
            if not xlsx.exists():
                print(f"  Warning: Workbook {xlsx} does not exist, skipping auto_raw_from_sheet")
                raw_map = {}
            else:
                wb = load_workbook(xlsx, read_only=True, data_only=False)
                if account_sheet not in wb.sheetnames:
                    wb.close()
                    print(f"  Warning: Account sheet '{account_sheet}' not found, skipping auto_raw_from_sheet")
                    raw_map = {}
                else:
                    ws = wb[account_sheet]
                    raw_map = {}
                    for c in range(11, ws.max_column + 1):
                        name = ws.cell(row=1, column=c).value
                        if isinstance(name, str) and name.strip():
                            raw_map[name.strip()] = name.strip()
                    wb.close()
        except (FileNotFoundError, PermissionError, KeyError) as e:
            logging.warning(f"Failed to load workbook for auto_raw_from_sheet: {e}")
            raw_map = {}

    print(f"  raw_map keys (K+ headers): {list(raw_map.keys()) if raw_map else 'None'}")

    norm_df = normalize(df_in, scfg)
    print(f"  normalized rows: {len(norm_df)}")

    try:
        dates = pd.to_datetime(norm_df["date"], errors="coerce")
        nat_count = dates.isna().sum()
        print(f"  date dtype: {dates.dtype}, NaT count: {nat_count} of {len(dates)}")
        if dates.notna().any():
            print(f"  date min/max: {dates.min()} .. {dates.max()}")
        norm_df["date"] = dates
    except (ValueError, TypeError) as e:
        logging.warning(f"Failed to process dates for source {src_name}: {e}")
        print(f"  Warning: Date processing failed, skipping source")
        return 0, 0, 0, 0, 0

    if args.start:
        start = pd.to_datetime(args.start)
        norm_df = norm_df[norm_df["date"] >= start]
    if args.end:
        end = pd.to_datetime(args.end)
        norm_df = norm_df[norm_df["date"] <= end]

    print(f"  rows after date filter: {len(norm_df)}")
    if norm_df.empty:
        return 0, 0, 0, 0, 0

    rows = []
    for idx, nrow in norm_df.iterrows():
        raw_payload = {}
        if raw_map:
            for sheet_header, csv_col in raw_map.items():
                raw_payload[csv_col] = df_in.loc[idx, csv_col] if csv_col in df_in.columns else None
        rows.append({
            "date": nrow["date"],
            "amount": float(nrow["amount"]),
            "description": nrow["description"],
            "__raw__": raw_payload
        })

    bank_label = scfg.get("bank_label", src_name)
    account_label = scfg.get("account_label", src_name)

    acct_added, acct_existing = insert_into_account_sheet(
        xlsx, account_sheet, bank_label, account_label, rows, raw_map=raw_map, 
        source_config=scfg, dry=args.dry_run, start_date=args.start, end_date=args.end
    )
    det_added, det_existing = insert_into_details(xlsx, details_sheet, bank_label, account_label, rows, dry=args.dry_run)
    print(f"  existing records: {acct_existing}")
    print(f"  -> per-account added: {acct_added}, details added: {det_added}")

    # Calculate deduped count (total rows - added rows)
    total_rows = len(rows)
    deduped_count = total_rows - det_added
    
    return acct_added, det_added, nat_count, deduped_count, acct_existing