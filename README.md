
# Bank → Excel Ingest: Quick Start

This toolkit helps you pull exported transactions from multiple banks and append them into your existing Excel workbook with one command, while keeping per‑bank raw tabs and a consolidated tab up to date.

## What you get
- **bank_ingest.py** – reads your bank exports (CSV/OFX/QFX), normalizes columns, de‑dupes, appends into per‑bank *Raw* tabs, and rebuilds a **Consolidated** tab.
- **config.yaml** – where you define your target workbook, per‑bank file globs, and column mappings.
- **FinanceWorkbook_template.xlsx** – optional starter workbook with example tabs; you can point the config to your own workbook instead.

## Prereqs
```bash
python3 -m pip install pandas openpyxl ofxparse pyyaml
```
(`ofxparse` is optional—only if you plan to ingest OFX/QFX.)

## Folder layout (example)
```
project/
  bank_ingest.py
  config.yaml
  inputs/
    checking_us/2025-10-checking.csv
    creditcard_abc/2025-10-cc.csv
  FinanceWorkbook_template.xlsx   # or your own workbook
```

## Configure
Edit **config.yaml**:
- `target_workbook`: path to your actual Excel file.
- Under `banks`, add one entry per institution:
  - `files`: glob(s) pointing to your exported files
  - `columns`: map your file’s headers to normalized names: `date`, `amount` *or* `debit`/`credit`, `description`, `category`, `check_number`
  - If your bank exports debits as positive numbers, set `flip_sign: true`.
  - If you have separate `debit` / `credit` columns, set `debit_col` and `credit_col` accordingly.

## Run
```bash
python3 bank_ingest.py --config config.yaml --start 2025-01-01 --end 2025-10-11
```
- The script appends only **new** rows by computing a stable `transaction_id` hash (`bank|date|amount|description|check_number`).
- It writes to one raw tab per bank, e.g., `Raw - Checking_US`, and rebuilds `Consolidated` by stacking all raw tabs.
- Your *Formatted* tabs are untouched. Refresh pivots/charts in Excel if needed.

## Tips
- Export as **CSV** when possible for simplicity. OFX/QFX are supported with `ofxparse`.
- If your bank truncates descriptions in export, consider adding `source_file` to formulas/tools for traceability.
- To test safely, point `target_workbook` at a copy of your workbook.
- If you later change mapping or sign, re-run—the de‑dupe key protects against duplicates.

## Extending
- Add custom cleaning: e.g., normalize payee names, merchant category mapping, memo parsing. The best place is `normalize_dataframe()` in `bank_ingest.py`.
- If you want automatic monthly ingestion, pair this with a scheduled task (macOS `launchd`, Windows Task Scheduler, or cron) that downloads your bank exports to the `inputs/` folder **(respecting your bank’s terms of service)**.
```

