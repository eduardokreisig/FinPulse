# FinPulse: Financial Data Ingestion Tool

This toolkit helps you pull exported transactions from multiple banks and append them into your existing Excel workbook with one command, while keeping per‑bank account sheets and a consolidated Details tab up to date.

## What you get
- **src/finpulse/main.py** – reads your bank exports (CSV), normalizes columns, de‑dupes, appends into per‑bank account sheets, and updates a **Details** tab.
- **config/config.yaml** – where you define your target workbook, per‑source file globs, and column mappings.
- Modular Python package with separate modules for data processing, Excel operations, and utilities.

## Prerequisites
```bash
python3 -m pip install pandas openpyxl pyyaml
```

## Folder layout (example)
```
FinPulse/
  src/
    finpulse/
      main.py
      config/
        loader.py
      data/
        csv_reader.py
        normalizer.py
      excel/
        sheet_inserter.py
      utils/
  config/
    config.yaml
  scripts/
    run-finance-ingest.sh
../Inputs/                    # Bank export files
  BECU - Member Shared Savings/
    2025-01-statement.csv
  Chase - Checkings/
    2025-01-activity.csv
../FinanceWorkbook 2025.xlsx  # Your target workbook
```

## Configure
Edit **config/config.yaml**:
- `target_workbook`: path to your actual Excel file
- `details_sheet`: name of consolidated sheet (default: "Details")
- `log_dir`: optional logging directory
- Under `sources`, add one entry per account:
  - `bank_label` & `account_label`: for identification
  - `account_sheet`: target Excel sheet name
  - `files`: glob(s) pointing to your exported files
  - `auto_raw_from_sheet: true`: auto-detect raw columns from Excel
  - `date_col`, `description_col`: explicit column mappings
  - `debit_col` & `credit_col`: for separate debit/credit columns
  - `date_format`: specify date parsing format (e.g., "%m/%d/%Y")

## Run

### Interactive Mode (Recommended)
```bash
# Interactive setup with prompts
python3 -m src.finpulse.main
```
This will prompt you for:
- Config file location (default: config/config.yaml)
- Finance workspace folder
- Finance workbook filename
- Inputs folder location
- Logs folder location
- Start/end dates for import
- Whether to proceed with real import after dry run

### Command Line Mode
```bash
# From the FinPulse directory
python3 -m src.finpulse.main --config config/config.yaml --start 2025-01-01 --end 2025-10-11

# Or use the provided script
./scripts/run-finance-ingest.sh

# Dry run to test without changes
python3 -m src.finpulse.main --config config/config.yaml --dry-run
```
- The script appends only **new** rows by computing deduplication keys from date, description, and amount.
- It writes to account-specific sheets (e.g., "Chase Checkings") and updates the "Details" sheet.
- Raw bank data is preserved in columns K+ for traceability.
- Your existing formulas and formatting are preserved.

## Tips
- Export as **CSV** from your banks for best compatibility.
- Use interactive mode for first-time setup - it guides you through configuration.
- The tool automatically detects date, amount, and description columns.
- Raw bank data is preserved in columns K+ for audit trails.
- Logging is available - check the log directory for detailed processing info.
- If you change mappings, re-run—deduplication prevents duplicates.
- Missing workbooks or input files are handled gracefully with warnings.
- After a dry run, you can choose to proceed with the real import immediately.

## Extending
- Add custom cleaning in `src/finpulse/data/normalizer.py` - e.g., payee normalization, category mapping.
- Modify Excel operations in `src/finpulse/excel/sheet_inserter.py` for custom formatting.
- Add new data sources by extending `src/finpulse/data/csv_reader.py`.
- For automation, use the provided shell script with cron/launchd **(respecting your bank's terms of service)**.

## Architecture
- **Modular design**: Separate concerns (config, data, Excel, utils)
- **Robust error handling**: Graceful failures with detailed logging
- **Data preservation**: Raw bank data maintained alongside normalized data
- **Flexible configuration**: YAML-based setup for easy bank addition