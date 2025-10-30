"""Main entry point for FinPulse financial data ingestion."""

import argparse
import logging
import sys
import traceback
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from .config.loader import get_log_directory, get_target_workbook_path, load_config
from .data.csv_reader import load_inputs_for_source
from .data.normalizer import normalize
from .excel.sheet_inserter import insert_into_account_sheet, insert_into_details
from .utils.logging_utils import Tee, setup_logging, utc_log_name
from .utils.path_utils import get_timestamp


def setup_log_file(log_dir: Path, is_dry_run: bool):
    """Setup log file if log directory is specified."""
    if not log_dir:
        return None, None
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logfile = log_dir / utc_log_name(is_dry_run)
        log_fp = open(logfile, "w", encoding="utf-8")
        sys.stdout = Tee(sys.stdout, log_fp)
        print(f"[logging to] {logfile}")
        return log_fp, sys.stdout
    except (OSError, PermissionError) as e:
        logging.error(f"Failed to setup logging to {log_dir}: {e}")
        raise


def process_source(src_name: str, scfg: dict, xlsx: Path, details_sheet: str, args) -> tuple[int, int]:
    """Process a single data source."""
    print(f"\n=== Source: {src_name} ===")
    df_in = load_inputs_for_source(scfg)
    print(f"  df_in rows: {len(df_in)}")
    
    if df_in.empty:
        return 0, 0

    # show headers early for debugging
    print(f"  CSV headers (after parse): {list(df_in.columns)}")

    account_sheet = scfg.get("account_sheet")
    raw_map = scfg.get("raw_map")
    
    if scfg.get("auto_raw_from_sheet", False):
        try:
            wb = load_workbook(xlsx, read_only=True, data_only=False)
            if account_sheet not in wb.sheetnames:
                wb.close()
                raise RuntimeError(f"Account sheet '{account_sheet}' not found for source '{src_name}'")
            ws = wb[account_sheet]
            raw_map = {}
            for c in range(11, ws.max_column + 1):
                name = ws.cell(row=1, column=c).value
                if isinstance(name, str) and name.strip():
                    raw_map[name.strip()] = name.strip()
            wb.close()
        except (FileNotFoundError, PermissionError, KeyError) as e:
            logging.error(f"Failed to load workbook for auto_raw_from_sheet: {e}")
            raise
    
    print(f"  raw_map keys (K+ headers): {list(raw_map.keys()) if raw_map else 'None'}")

    norm_df = normalize(df_in, scfg)
    print(f"  normalized rows: {len(norm_df)}")
    
    try:
        dates = pd.to_datetime(norm_df["date"], errors="coerce")
        print(f"  date dtype: {dates.dtype}, NaT count: {dates.isna().sum()} of {len(dates)}")
        if dates.notna().any():
            print(f"  date min/max: {dates.min()} .. {dates.max()}")
        norm_df["date"] = dates
    except (ValueError, TypeError) as e:
        logging.error(f"Failed to process dates for source {src_name}: {e}")
        return 0, 0

    if args.start:
        start = pd.to_datetime(args.start)
        norm_df = norm_df[norm_df["date"] >= start]
    if args.end:
        end = pd.to_datetime(args.end)
        norm_df = norm_df[norm_df["date"] <= end]
    
    print(f"  rows after date filter: {len(norm_df)}")
    if norm_df.empty:
        return 0, 0

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

    acct_added = insert_into_account_sheet(xlsx, account_sheet, bank_label, account_label, rows, raw_map=raw_map, dry=args.dry_run)
    det_added = insert_into_details(xlsx, details_sheet, bank_label, account_label, rows, dry=args.dry_run)
    print(f"  -> per-account added: {acct_added}, details added: {det_added}")
    
    return acct_added, det_added


def main() -> None:
    """Main entry point."""
    setup_logging()
    
    ap = argparse.ArgumentParser(description="FinPulse v5.3.17 (robust CSV defaults; no YAML change needed)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--start", help="YYYY-MM-DD", default=None)
    ap.add_argument("--end", help="YYYY-MM-DD", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-dir", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    log_dir = get_log_directory(cfg, args.log_dir)
    
    orig_stdout = sys.stdout
    log_fp = None
    
    try:
        log_fp, _ = setup_log_file(log_dir, args.dry_run)
        
        xlsx = get_target_workbook_path(cfg)
        details_sheet = cfg.get("details_sheet", "Details")

        print(f"Workbook: {xlsx}")
        print(f"  exists: {xlsx.exists()}  size: {xlsx.stat().st_size if xlsx.exists() else 0} bytes")
        print(f"  modified: {get_timestamp(xlsx)}")

        total_details = 0
        total_accounts = 0

        for src_name, scfg in cfg["sources"].items():
            acct_added, det_added = process_source(src_name, scfg, xlsx, details_sheet, args)
            total_accounts += acct_added
            total_details += det_added

        print(f"\nSummary: per-account added={total_accounts}, details added={total_details}")
        print(f"Modified (after): {get_timestamp(xlsx)}")
        if args.dry_run:
            print("(dry-run) No changes written.")
        else:
            print("Done.")
            
    except Exception as e:
        print("ERROR:", e)
        print(traceback.format_exc())
        raise
    finally:
        sys.stdout = orig_stdout
        try:
            if log_fp:
                log_fp.close()
        except (OSError, IOError) as e:
            logging.warning(f"Failed to close log file: {e}")


if __name__ == "__main__":
    main()