# FinPulse: Intelligent Financial Data Ingestion Tool

This toolkit helps you pull exported transactions from multiple banks and append them into your existing Excel workbook with one command, while keeping per‑bank account sheets and a consolidated Details tab up to date. Includes machine learning models for automatic transaction categorization trained on existing labeled data.

## What you get
- **src/finpulse/** – modular Python package with separate modules for data processing, Excel operations, ML, and utilities
- **src/fin_statements_ingest.py** – main entry point that uses the modular package
- **config/config.yaml** – where you define your target workbook, per‑source file globs, column mappings, and ML configuration
- **ML categorization** – automatic Category and Subcategory prediction using trained models
- Clean, maintainable code following Python best practices

## Prerequisites

### Basic Installation
```bash
python3 -m pip install pandas openpyxl pyyaml
```

### ML Features (Optional)
```bash
python3 -m pip install -r requirements-ml.txt
```
Includes: scikit-learn, joblib, matplotlib, sentence-transformers (for S-BERT), and numpy for machine learning capabilities.

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
      ml/                     # Machine Learning subsystem
        models/               # Trained model artifacts
        metrics/              # Performance metrics
        base_model.py         # ML base classes
        model_factory.py      # Algorithm factory
        pipeline.py           # ML inference pipeline
        train.py              # Model training
        text_encoder.py       # TF-IDF/S-BERT encoding
        preprocess.py         # Data preprocessing
        config_validator.py   # ML config validation
        model_info.py         # CLI model information
        utils_model.py        # ML utilities
      ui/
        interactive.py        # User interaction
      utils/
        logging_utils.py      # Logging & Tee class
        path_utils.py         # Path validation
        date_utils.py         # Date parsing
    fin_statements_ingest.py  # Main entry point
  config/
    config.yaml             # Main configuration
    config_examples.yaml    # Configuration examples
  scripts/
    run-finance-ingest.sh
  requirements-ml.txt         # ML dependencies
  README_ML.md               # Detailed ML documentation
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
- Under `ml`, configure machine learning models:
  - `text_encoder`: "tfidf" or "sbert" for text processing
  - `category_model` & `subcategory_model`: algorithm and feature configuration
  - `rare_label_threshold`: minimum samples for category inclusion

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

**Important**: FinPulse automatically creates a timestamped copy of your original workbook before making any changes. The copy is named `<Original File name> <timestamp>.xlsx` (e.g., `FinanceWorkbook 2025 2024-01-01T12-00-00.123.xlsx`) and saved in the same directory as the original. Your original file remains untouched.

### Command Line Mode
```bash
# From the FinPulse directory
python3 -m src.finpulse.main --config config/config.yaml --start 2025-01-01 --end 2025-10-11

# Dry run to test without changes
python3 -m src.finpulse.main --config config/config.yaml --dry-run

# Direct script execution (alternative)
python src/fin_statements_ingest.py --config config/config.yaml
```
- **Automatic backup**: Creates a timestamped copy of your workbook before making changes, preserving your original file.
- The script appends only **new** rows by computing deduplication keys from date, description, and amount.
- It writes to account-specific sheets (e.g., "Chase Checkings") and updates the "Details" sheet.
- **ML categorization**: Automatically predicts Category and Subcategory for new transactions using trained models.
- Raw bank data is preserved in columns K+ for traceability.
- Your existing formulas and formatting are preserved.

## Machine Learning Features

FinPulse includes intelligent transaction categorization using two specialized ML models:

### Category Model
- **Algorithm**: Configurable (Random Forest, Logistic Regression, SVM, Naive Bayes, Decision Tree)
- **Purpose**: Predicts main transaction categories (e.g., "Food & Dining", "Transportation")
- **Features**: Transaction Description, Transaction Type
- **Training**: Uses existing labeled transactions in your workbook

### Subcategory Model  
- **Algorithm**: Configurable (same options as Category Model)
- **Purpose**: Predicts detailed subcategories (e.g., "Restaurants", "Gas Stations")
- **Features**: Transaction Description, Automated Trans. Category, Transaction Type
- **Training**: Leverages both description and predicted category for context

### ML Commands
```bash
# Train models on existing labeled data
python3 -m src.finpulse.ml.train --input "FinanceWorkbook 2025.xlsx"

# Run inference on new transactions
python3 -m src.finpulse.ml.pipeline --input "FinanceWorkbook 2025.xlsx"

# View available algorithms and parameters
python3 -m src.finpulse.ml.model_info
python3 -m src.finpulse.ml.model_info random_forest
```

### Text Encoding Options
- **TF-IDF**: Fast, lightweight, good for most use cases
- **S-BERT**: More accurate semantic understanding, requires additional dependencies

### Model Management
- **Versioning**: Each training run creates versioned model files
- **Metadata tracking**: Training notes, performance metrics, feature importance
- **Rollback support**: Easy reversion to previous model versions
- **Automatic integration**: ML predictions run automatically during data import

## Tips
- Export as **CSV** from your banks for best compatibility.
- Use interactive mode for first-time setup - it guides you through configuration.
- The tool automatically detects date, amount, and description columns.
- **Automatic backup**: Your original workbook is never modified - all changes are made to timestamped copies.
- **Mixed date formats**: When using `%m/%d/%y` format, the tool automatically handles both 2-digit (25) and 4-digit (2025) years in the same account by truncating 4-digit years to 2-digit.
- **ML training**: Re-train models whenever you add new labeled transactions to improve accuracy.
- Raw bank data is preserved in columns K+ for audit trails.
- Logging is available - check the log directory for detailed processing info.
- If you change mappings, re-run—deduplication prevents duplicates.
- Missing workbooks or input files are handled gracefully with warnings.
- After a dry run, you can choose to proceed with the real import immediately.

## ML Configuration Examples

### Basic Configuration
```yaml
ml:
  text_encoder: tfidf  # Fast, lightweight option
  category_model:
    algorithm: random_forest
    features:
      - "Transaction Description"
      - "Transaction Type"
    hyperparameters:
      n_estimators: 300
      max_depth: 20
      random_state: 42
  subcategory_model:
    algorithm: logistic_regression
    features:
      - "Transaction Description"
      - "Automated Trans. Category"
      - "Transaction Type"
    hyperparameters:
      solver: lbfgs
      max_iter: 500
      random_state: 42
  rare_label_threshold: 10
```

### Advanced Configuration (S-BERT)
```yaml
ml:
  text_encoder: sbert  # Better semantic understanding
  category_model:
    algorithm: logistic_regression
    features:
      - "Transaction Description"
      - "Transaction Type"
    hyperparameters:
      solver: lbfgs
      penalty: l2
      C: 6.0
      max_iter: 1000
      class_weight: balanced
      n_jobs: -1
      random_state: 42
  subcategory_model:
    algorithm: random_forest
    features:
      - "Transaction Description"
      - "Automated Trans. Category"
      - "Transaction Type"
    hyperparameters:
      n_estimators: 500
      max_depth: 20
      min_samples_split: 2
      min_samples_leaf: 2
      max_features: sqrt
      class_weight: balanced
      n_jobs: -1
      random_state: 42
  rare_label_threshold: 10
```

### Supported Algorithms
- **random_forest**: Robust ensemble method, handles mixed data types well
- **logistic_regression**: Fast linear model, highly interpretable results
- **svm**: Support Vector Machine, effective for high-dimensional text data
- **naive_bayes**: Probabilistic classifier, fast training and inference
- **decision_tree**: Tree-based model, highly interpretable decision paths

### Configuration Validation
- Invalid algorithms are rejected with helpful error messages
- Hyperparameters are validated against each algorithm's requirements
- Configuration is validated before training begins
- See `config/config_examples.yaml` for more configuration examples

## Extending
- **Data processing**: Modify `src/finpulse/data/normalizer.py` for custom cleaning, payee normalization, category mapping
- **Excel operations**: Update `src/finpulse/excel/sheet_inserter.py` for custom formatting
- **File handling**: Extend `src/finpulse/data/csv_reader.py` for new data sources
- **Core logic**: Modify `src/finpulse/core/processor.py` for source processing changes
- **Application flow**: Update `src/finpulse/core/runner.py` for orchestration changes
- **User interface**: Enhance `src/finpulse/ui/interactive.py` for better user experience
- **ML algorithms**: Add new algorithms to `src/finpulse/ml/model_factory.py`
- **ML features**: Extend `src/finpulse/ml/preprocess.py` for custom feature engineering
- **Text encoding**: Add new encoders to `src/finpulse/ml/text_encoder.py`
- **ML pipeline**: Customize `src/finpulse/ml/pipeline.py` for inference workflow
- **Utilities**: Add new utilities in `src/finpulse/utils/`
- **Configuration**: Enhance `src/finpulse/config/loader.py` for advanced config features
- **Automation**: Use the shell script with cron/launchd **(respecting your bank's terms of service)**

## Architecture
- **Modular design**: Clean separation of concerns across focused modules
- **Python best practices**: Proper package structure, type hints, error handling
- **Single responsibility**: Each module under 200 lines with clear purpose
- **ML subsystem**: Dedicated machine learning package with model management
- **Testability**: Modules can be unit tested independently
- **Maintainability**: Easy to find, modify, and extend specific functionality
- **Robust error handling**: Graceful failures with detailed logging
- **Data preservation**: Raw bank data maintained alongside normalized data
- **Automatic backup**: Creates timestamped copies to preserve original workbooks
- **Flexible configuration**: YAML-based setup for easy bank addition and ML tuning
- **Model versioning**: Automatic versioning and metadata tracking for ML models
- **Configurable ML**: Support for multiple algorithms and text encoders
- **Safe inference**: ML predictions only applied to timestamped copies, never original files