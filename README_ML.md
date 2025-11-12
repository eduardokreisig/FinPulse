# FinPulse Machine Learning Subsystem

## Overview
FinPulse ML adds automated inference for **Category** and **Subcategory** fields in your Finance Workbook.  
It uses small supervised models trained on rows that already contain labels.

---

## Key Features
- **CategoryModel:** Random Forest → predicts *Category*
- **SubCategoryModel:** Multinomial Logistic Regression → predicts *Subcategory*
- **TF-IDF** text encoder (default), future support for **Sentence-BERT**
- Config-driven algorithms (`config.yaml`)
- Model versioning + metadata tracking
- Safe inference (writes to timestamped copy only)
- Configurable rare-label grouping threshold (`rare_label_threshold`)

---

## Directory Layout

```
src/finpulse/ml/
├── preprocess.py           # Data loading / cleaning
├── text_encoder.py         # TF-IDF / S-BERT vectorization
├── model_category.py       # CategoryModel (Category)
├── model_subcategory.py    # SubCategoryModel (Subcategory)
├── model_type.py           # Model B (Type)
├── train.py                # K-fold training & metadata
├── pipeline.py             # Inference on Excel workbook
├── utils_model.py          # Versioning, metrics, saving
├── models/                 # Stored model artifacts
│   ├── metadata.yaml
│   └── history/
└── metrics/                # Confusion matrices
```

## Usage

### Train models
```bash
finpulse ml train --input "FinanceWorkbook 2025.xlsx"
```

You'll be prompted for:
- Notes for this run
- Version bump (major/minor/patch)

Artifacts and metadata are stored in:
```
src/finpulse/ml/models/
```

### Run inference

Inference runs automatically at the end of a "real import" when you confirm Y in:
```
Run and ingest Machine Learning predictions for Category and Subcategory columns? (Y/N)
```

Alternatively, it can be invoked manually:
```bash
finpulse ml infer --input "FinanceWorkbook 2025.xlsx"
```

### Versioning & Rollback

- Each training generates new .joblib files:
    - `category_vX.joblib`
    - `subcategory_vX.joblib`
    - `text_encoder_vX.joblib`
- `metadata.yaml` tracks active version.
- Old metadata is archived under `/history/`.
- To rollback: delete the undesired model files and revert `metadata.yaml` to a prior version.

### Config Options (config.yaml)

```
ml:
    text_encoder: tfidf           # or "sbert"
    category_model:
        algorithm: random_forest
    subcategory_model:
        algorithm: logistic_regression
    rare_label_threshold: 10
```

### Logging

During inference:
```
Category filled by ML: X rows
Subcategory filled by ML: Y rows
Type filled by ML: Y rows
```
Logs are also appended to the standard FinPulse log file.

### Best Practices

1. Re-train whenever you add new labeled data to your workbook.
2. Keep at least the last two model versions.
3. Let Google Drive back up the models/ folder.
4. Commit metadata.yaml (but not .joblib files) to Git.
5. Document notes for every training run.

### FAQ

**Q: What happens if no models are trained?**  
A: The pipeline exits gracefully with a clear warning:
```
⚠️ No trained models found. Please run 'finpulse ml train' first.
```

**Q: Can I run ML in dry-run mode?**  
A: No. ML predictions are skipped when `--dry_run` is enabled.

**Q: What about S-BERT performance?**  
A: You can switch to it anytime in `config.yaml`. Training time increases but accuracy may improve by 3–8 pp.