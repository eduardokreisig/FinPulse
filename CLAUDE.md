# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements-ml.txt

# Run (interactive menu, no arguments)
python -m src.finpulse.main

# Ingest transactions
python -m src.finpulse.main ingest --config config/config.yaml --start 2025-01-01 --end 2025-12-31

# Dry run (preview without writing)
python -m src.finpulse.main ingest --config config/config.yaml --dry-run

# Train ML models
python -m src.finpulse.main ml train --input "FinanceWorkbook 2025.xlsx" --bump minor --notes "Added Q1 data"

# Run ML inference
python -m src.finpulse.main ml infer --input "FinanceWorkbook 2025.xlsx"

# CLI help
python -m src.finpulse.main --help
python -m src.finpulse.main ingest --help
python -m src.finpulse.main ml train --help
```

## Architecture

FinPulse ingests bank transaction CSV files and writes them into an Excel finance workbook, with optional ML-based transaction categorization.

### Entry Point & Mode Dispatch

`src/finpulse/main.py` detects whether arguments are present: no args → interactive menu (`ui/interactive.py`), any args → CLI parsing (`ui/cli.py`). Both modes ultimately call `core/runner.py:run_application()`.

### Data Ingestion Flow

```
runner.run_application()
  └─ Creates timestamped copy of original workbook (never modifies original)
  └─ runner.run_processing()
       └─ For each source in config["sources"]:
            └─ processor.process_source()
                 ├─ data/csv_reader.py  → loads CSVs per file (returns list of DataFrames)
                 ├─ data/normalizer.py  → auto-detects date/amount/description columns
                 └─ excel/sheet_inserter.py → deduplicates + inserts into:
                      ├─ per-account sheet (e.g., "Chase Checking")
                      └─ "Details" sheet (consolidated view)
  └─ (optional) ml/pipeline.run_ml_pipeline() → fills unlabeled Category/Subcategory cells
```

**Key behavior**: Cumulative deduplication keys are built across all sources during a single run, preventing cross-source duplicate rows.

### ML Subsystem

The ML layer (`src/finpulse/ml/`) is entirely optional — it uses lazy imports throughout, so base ingestion works without ML dependencies.

- **Training** (`ml/train.py`): Loads labeled rows from the `Details` sheet → fits separate `TextEncoder` instances per model → 5-fold CV → saves final models trained on full dataset
- **Inference** (`ml/pipeline.py`): Loads active version from `metadata.yaml` → transforms unlabeled rows → writes predictions back to `Category`/`Subcategory` columns in the workbook
- **Models**: `BaseModel` wraps any sklearn estimator; `ModelFactory` creates them from config strings (`random_forest`, `logistic_regression`, `svm`, `naive_bayes`, `decision_tree`)
- **Text encoding**: `TextEncoder` supports TF-IDF (default) or S-BERT. Each model (category, subcategory) gets its own encoder fitted on its specific feature columns
- **Versioning**: Each training run bumps `src/finpulse/ml/models/metadata.yaml` (major/minor/patch); old metadata is archived to `models/history/`; `.joblib` files are named `category_vX.Y.Z.joblib` etc.

### Configuration

`config/config.yaml` (user-created; see `config/config_examples.yaml` for the ML section). Key top-level keys:
- `target_workbook`: path to the Excel finance workbook
- `details_sheet`: name of the consolidated sheet (default: `"Details"`)
- `log_dir`: directory for log files
- `sources`: dict of named bank sources, each with:
  - `files`: glob patterns for CSV inputs
  - `account_sheet`: target Excel sheet name
  - `bank_label`, `account_label`: labels written into the workbook
  - Column mapping config: `date_col`, `description_col`, `amount_col`, `debit_col`, `credit_col`, `columns` (rename map)
  - `auto_raw_from_sheet`: read extra columns from the sheet header automatically
  - `sign_from`: optional debit/credit sign inference from a type column
- `ml`: ML config (algorithms, features, hyperparameters, `text_encoder`, `rare_label_threshold`)

### Interactive Mode

`ui/interactive.py` implements low-level input helpers (`get_user_input`, `get_yes_no`, `get_choice_input`) built on a `UserCancelledError` pattern — Ctrl+C/EOF raises `UserCancelledError` instead of crashing. Warning cases re-prompt rather than cancel the operation.

The 5-option menu maps to: (1) Ingest + Inference, (2) Ingest Only, (3) Inference Only, (4) Model Retraining, (5) Help.

### Module Summary

| Module | Responsibility |
|--------|---------------|
| `core/runner.py` | Orchestration, log setup, timestamped copy creation, ML trigger |
| `core/processor.py` | Per-source processing loop, cumulative key management |
| `data/csv_reader.py` | CSV loading with glob pattern expansion |
| `data/normalizer.py` | Column auto-detection (date/amount/description), sign normalization |
| `data/file_collector.py` | File collection utilities |
| `excel/sheet_inserter.py` | Dedup + insert into account/details sheets |
| `excel/workbook.py` | Workbook utilities |
| `ml/train.py` | K-fold training, artifact saving |
| `ml/pipeline.py` | Inference on workbook Details sheet |
| `ml/base_model.py` | Sklearn model wrapper |
| `ml/model_factory.py` | Creates models from string names |
| `ml/text_encoder.py` | TF-IDF / S-BERT fitting and transform |
| `ml/preprocess.py` | Splits Details sheet into labeled/unlabeled DataFrames |
| `ml/utils_model.py` | Version bumping, metadata save/archive |
| `ml/config_validator.py` | ML config validation |
| `utils/path_utils.py` | Path validation, timestamped copy creation |
| `utils/date_utils.py` | Robust date parsing, date-likeness heuristics |
| `utils/logging_utils.py` | `Tee` (stdout + file), log file naming |