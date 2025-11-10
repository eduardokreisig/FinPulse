"""
Handles model training, evaluation, and versioning.

Workflow:
 1. Load labeled data from workbook
 2. Encode text features using configured encoder (TF-IDF or S-BERT)
 3. Train Model A (Classification) and Model B (Type)
 4. Perform K-fold cross-validation
 5. Save models, encoder, and metadata
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, f1_score

from .preprocess import load_and_prepare_details
from .text_encoder import TextEncoder
from .model_classification import ClassificationModel
from .model_type import TypeModel
from .utils_model import bump_model_version, evaluate_and_plot, save_metadata

import yaml
from datetime import datetime


def train_models(cfg_path: str, xlsx_path: str, bump_type: str = "minor", notes: str = ""):
    """Train both ML models and save artifacts + metadata."""
    # Load config
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    ml_cfg = cfg.get("ml", {})
    encoder_type = ml_cfg.get("text_encoder", "tfidf")
    rare_thresh = ml_cfg.get("rare_label_threshold", 10)

    print(f"Loading data from {xlsx_path}...")
    labeled_df, _ = load_and_prepare_details(xlsx_path)

    # Combine columns for text input
    text_features = (
            labeled_df["Transaction Description"]
            + " "
            + labeled_df["Automated Trans. Category"].fillna("")
            + " "
            + labeled_df["Transaction Type"].fillna("")
    )

    encoder = TextEncoder(method=encoder_type)
    encoder.fit(text_features)
    X = encoder.transform(text_features)

    # Prepare Y labels
    y_class = labeled_df["Classification"]
    y_type = labeled_df["Type"]

    # Initialize models
    model_a = ClassificationModel()
    model_b = TypeModel()

    # K-fold evaluation
    print("\nPerforming 5-fold cross-validation...")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    acc_a, f1_a, acc_b, f1_b = [], [], [], []

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train_a, y_test_a = y_class.iloc[train_idx], y_class.iloc[test_idx]
        y_train_b, y_test_b = y_type.iloc[train_idx], y_type.iloc[test_idx]

        model_a.train(X_train, y_train_a)
        preds_a = model_a.predict(X_test)
        acc_a.append(accuracy_score(y_test_a, preds_a))
        f1_a.append(f1_score(y_test_a, preds_a, average="macro"))

        model_b.train(X_train, y_train_b)
        preds_b = model_b.predict(X_test)
        acc_b.append(accuracy_score(y_test_b, preds_b))
        f1_b.append(f1_score(y_test_b, preds_b, average="macro"))

    # Train final models on full dataset
    model_a.train(X, y_class)
    model_b.train(X, y_type)

    # Save artifacts
    models_dir = Path(__file__).parent / "models"
    metrics_dir = Path(__file__).parent / "metrics"
    version_str = bump_model_version(models_dir / "metadata.yaml", bump_type)

    print(f"\nSaving models version {version_str}...")
    encoder.save(models_dir / f"text_encoder_v{version_str}.joblib")
    model_a.save(models_dir / f"classification_v{version_str}.joblib")
    model_b.save(models_dir / f"type_v{version_str}.joblib")

    # Metadata
    meta = {
        "version": version_str,
        "trained_on": datetime.now().isoformat(),
        "encoder": encoder_type,
        "model_a": {"algorithm": "random_forest", "accuracy": float(pd.Series(acc_a).mean()), "f1_macro": float(pd.Series(f1_a).mean())},
        "model_b": {"algorithm": "logistic_regression", "accuracy": float(pd.Series(acc_b).mean()), "f1_macro": float(pd.Series(f1_b).mean())},
        "evaluation": {"validation_strategy": "kfold", "k": 5},
        "training_data": {"total_rows": len(labeled_df), "source_file": str(xlsx_path)},
        "notes": notes,
    }

    # Save metadata
    save_metadata(models_dir / "metadata.yaml", meta)

    print("\n✅ Training complete. Models and metadata saved.")
