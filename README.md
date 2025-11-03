# FinPulse: Financial Data Ingestion Tool

This toolkit helps you pull exported transactions from multiple banks and append them into your existing Excel workbook with one command, while keeping per‑bank account sheets and a consolidated Details tab up to date.

## What you get
- **src/finpulse/** – modular Python package with separate modules for data processing, Excel operations, and utilities
- **src/fin_statements_ingest.py** – main entry point that uses the modular package
- **config/config.yaml** – where you define your target workbook, per‑source file globs, and column mappings
- Clean, maintainable code following Python best practices

## Prerequisites
```bash
python3 -m pip install pandas openpyxl pyyaml
```

## Folder layout
```
FinPulse/
  src/
    finpulse/                 # Main package
      __init__.py
      main.py                 # Minimal entry point
      config/
        loader.py             # Config loading
      core/
        processor.py          # Source processing logic
        runner.py             # Application orchestration
      data/
        csv_reader.py         # CSV parsing
        normalizer.py         # Data normalization
        file_collector.py     # File discovery
      excel/
        workbook.py           # Excel utilities
        sheet_inserter.py     # Row insertion
      ui/
        interactive.py        # User interaction
      utils/
        logging_utils.py      # Logging & Tee class
        path_utils.py         # Path validation
        date_utils.py         # Date parsing
    fin_statements_ingest.py  # Main entry point
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

# Or use the provided script (runs interactive mode)
./scripts/run-finance-ingest.sh
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

# Dry run to test without changes
python3 -m src.finpulse.main --config config/config.yaml --dry-run

# Direct script execution (alternative)
python src/fin_statements_ingest.py --config config/config.yaml
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
- **Data processing**: Modify `src/finpulse/data/normalizer.py` for custom cleaning, payee normalization, category mapping
- **Excel operations**: Update `src/finpulse/excel/sheet_inserter.py` for custom formatting
- **File handling**: Extend `src/finpulse/data/csv_reader.py` for new data sources
- **Core logic**: Modify `src/finpulse/core/processor.py` for source processing changes
- **Application flow**: Update `src/finpulse/core/runner.py` for orchestration changes
- **User interface**: Enhance `src/finpulse/ui/interactive.py` for better user experience
- **Utilities**: Add new utilities in `src/finpulse/utils/`
- **Configuration**: Enhance `src/finpulse/config/loader.py` for advanced config features
- **Automation**: Use the shell script with cron/launchd **(respecting your bank's terms of service)**

## Architecture
- **Modular design**: Clean separation of concerns across focused modules
- **Python best practices**: Proper package structure, type hints, error handling
- **Single responsibility**: Each module under 200 lines with clear purpose
- **Testability**: Modules can be unit tested independently
- **Maintainability**: Easy to find, modify, and extend specific functionality
- **Robust error handling**: Graceful failures with detailed logging
- **Data preservation**: Raw bank data maintained alongside normalized data
- **Flexible configuration**: YAML-based setup for easy bank addition