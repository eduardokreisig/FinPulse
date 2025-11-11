"""
Handles ML inference workflow after data ingestion.

Responsibilities:
 - Load trained models and encoder
 - Perform inference for unlabeled rows
 - Write predictions into Classification (K) and Type (L) columns
 - Log summary statistics
"""

import pandas as pd
import yaml
import joblib
from pathlib import Path
from .preprocess import load_and_prepare_details


def run_ml_pipeline(cfg, xlsx_path: str):
    """Executes ML inference on timestamped workbook."""
    print("\n🔍 Starting FinPulse ML inference pipeline...")

    models_dir = Path(__file__).parent / "models"
    metadata_path = models_dir / "metadata.yaml"

    # Check for trained models
    if not metadata_path.exists():
        print("⚠️ No trained models found. Please run 'finpulse ml train' first.")
        return

    with open(metadata_path, "r") as f:
        meta = yaml.safe_load(f)
    version = meta["version"]

    # Check all required model files exist
    required_files = [
        models_dir / f"text_encoder_v{version}.joblib",
        models_dir / f"classification_v{version}.joblib",
        models_dir / f"type_v{version}.joblib",
    ]
    missing = [f.name for f in required_files if not f.exists()]
    if missing:
        print(f"⚠️ Missing model files: {', '.join(missing)}. Re-train using 'finpulse ml train'.")
        return

    # Load models and encoder
    encoder = joblib.load(models_dir / f"text_encoder_v{version}.joblib")
    model_a = joblib.load(models_dir / f"classification_v{version}.joblib")
    model_b = joblib.load(models_dir / f"type_v{version}.joblib")

    # Load workbook
    labeled_df, unlabeled_df = load_and_prepare_details(xlsx_path)
    df = pd.read_excel(xlsx_path, sheet_name="Details")

    # Filter unlabeled
    mask_unlabeled = df["Classification"].isna() | df["Type"].isna()
    df_unlabeled = df[mask_unlabeled].copy()

    if df_unlabeled.empty:
        print("✅ No unlabeled transactions found. Nothing to predict.")
        return

    # Combine text features
    X_unlabeled_text = (
        df_unlabeled["Transaction Description"].astype(str).fillna("") + " " +
        df_unlabeled["Automated Trans. Category"].astype(str).fillna("") + " " +
        df_unlabeled["Transaction Type"].astype(str).fillna("")
    ).str.lower()

    X_unlabeled = encoder.transform(X_unlabeled_text)

    # Predict classifications and types
    preds_class = model_a.predict(X_unlabeled)
    preds_type = model_b.predict(X_unlabeled)

    df.loc[mask_unlabeled, "Classification"] = preds_class
    df.loc[mask_unlabeled, "Type"] = preds_type

    # Save results preserving formatting
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path)
    ws = wb["Details"]
    
    # Find column indices
    col_class = col_type = None
    for c in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=c).value
        if header == "Classification":
            col_class = c
        elif header == "Type":
            col_type = c
    
    # Update only the prediction cells
    unlabeled_indices = df_unlabeled.index
    for i, (pred_class, pred_type) in enumerate(zip(preds_class, preds_type)):
        row_idx = unlabeled_indices[i] + 2  # +2 for 1-based indexing and header
        if col_class:
            ws.cell(row=row_idx, column=col_class).value = pred_class
        if col_type:
            ws.cell(row=row_idx, column=col_type).value = pred_type
    
    wb.save(xlsx_path)
    wb.close()

    print(f"✅ ML predictions written to '{Path(xlsx_path).name}'.")
    print(f"   Classification filled by ML: {len(preds_class)} rows")
    print(f"   Type filled by ML: {len(preds_type)} rows")
