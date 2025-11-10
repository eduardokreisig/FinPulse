"""
Handles model training, evaluation, and versioning.

Workflow:
 1. Load labeled data from workbook
 2. Encode text features using configured encoder (TF-IDF or S-BERT)
 3. Train Model A (Classification) and Model B (Type)
 4. Perform K-fold cross-validation
 5. Save models, encoder, and metadata
"""

from datetime import datetime
from pathlib import Path

import yaml
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import KFold

from .model_classification import ClassificationModel
from .model_type import TypeModel
from .preprocess import load_and_prepare_details
from .text_encoder import TextEncoder
from .utils_model import bump_model_version, save_metadata


def evaluate_model_kfold(model, X, y, k=5):
    """Perform k-fold cross-validation on a model."""
    if not hasattr(model, 'train') or not hasattr(model, 'predict'):
        raise ValueError("Model must have train and predict methods")
    if k < 2 or k > 20:
        raise ValueError("k must be between 2 and 20")
    
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    accuracies, f1_scores = [], []
    
    for train_idx, test_idx in kf.split(X):
        try:
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model.train(X_train, y_train)
            preds = model.predict(X_test)
            accuracies.append(accuracy_score(y_test, preds))
            f1_scores.append(f1_score(y_test, preds, average="macro"))
        except Exception as e:
            import logging
            logging.warning(f"K-fold iteration failed: {e}")
            continue
    
    return accuracies, f1_scores


def train_models(cfg_path: str, xlsx_path: str, bump_type: str = "minor", notes: str = ""):
    """Train both ML models and save artifacts + metadata."""
    # Validate inputs
    if not isinstance(cfg_path, str) or not cfg_path.strip():
        raise ValueError("cfg_path must be a non-empty string")
    if not isinstance(xlsx_path, str) or not xlsx_path.strip():
        raise ValueError("xlsx_path must be a non-empty string")
    if bump_type not in ["major", "minor", "patch"]:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")
    
    cfg_path = Path(cfg_path).resolve()
    xlsx_path = Path(xlsx_path).resolve()
    
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Excel file not found: {xlsx_path}")
    
    # Load config safely
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML config file: {e}")
    except Exception as e:
        raise IOError(f"Failed to read config file: {e}")

    ml_cfg = cfg.get("ml", {})
    encoder_type = ml_cfg.get("text_encoder", "tfidf")
    rare_thresh = ml_cfg.get("rare_label_threshold", 10)

    print(f"Loading data from {xlsx_path}...")
    try:
        labeled_df, _ = load_and_prepare_details(str(xlsx_path))
        if labeled_df.empty:
            raise ValueError("No labeled data found in the workbook")
    except Exception as e:
        raise RuntimeError(f"Failed to load training data: {e}")

    # Combine columns for text input
    text_features = (
            labeled_df["Transaction Description"]
            + " "
            + labeled_df["Automated Trans. Category"].fillna("")
            + " "
            + labeled_df["Transaction Type"].fillna("")
    )

    try:
        encoder = TextEncoder(method=encoder_type)
        encoder.fit(text_features)
        X = encoder.transform(text_features)
    except Exception as e:
        raise RuntimeError(f"Text encoding failed: {e}")

    # Prepare Y labels
    y_class = labeled_df["Classification"]
    y_type = labeled_df["Type"]

    # Initialize models
    try:
        model_a = ClassificationModel()
        model_b = TypeModel()

        # K-fold evaluation
        print("\nPerforming 5-fold cross-validation...")
        acc_a, f1_a = evaluate_model_kfold(model_a, X, y_class)
        acc_b, f1_b = evaluate_model_kfold(model_b, X, y_type)
    except Exception as e:
        raise RuntimeError(f"Model training/evaluation failed: {e}")

    # Train final models on full dataset
    try:
        final_model_a = ClassificationModel()  # Fresh instance for final training
        final_model_b = TypeModel()  # Fresh instance for final training
        final_model_a.train(X, y_class)
        final_model_b.train(X, y_type)
    except Exception as e:
        raise RuntimeError(f"Final model training failed: {e}")

    # Save artifacts
    try:
        # Secure path handling to prevent path traversal
        base_dir = Path(__file__).parent.resolve()
        models_dir = base_dir / "models"
        if not str(models_dir).startswith(str(base_dir)):
            raise ValueError("Invalid models directory path")
        models_dir.mkdir(exist_ok=True)
        
        metadata_file = models_dir / "metadata.yaml"
        if not str(metadata_file).startswith(str(models_dir)):
            raise ValueError("Invalid metadata file path")
        version_str = bump_model_version(metadata_file, bump_type)

        print(f"\nSaving models version {version_str}...")
        # Validate filenames to prevent path traversal
        safe_version = ''.join(c for c in version_str if c.isalnum() or c in '.-_')
        if safe_version != version_str:
            raise ValueError(f"Invalid version string: {version_str}")
            
        encoder_file = models_dir / f"text_encoder_v{safe_version}.joblib"
        model_a_file = models_dir / f"classification_v{safe_version}.joblib"
        model_b_file = models_dir / f"type_v{safe_version}.joblib"
        
        # Ensure files are within models directory
        for file_path in [encoder_file, model_a_file, model_b_file]:
            if not str(file_path.resolve()).startswith(str(models_dir.resolve())):
                raise ValueError(f"Invalid file path: {file_path}")
        
        encoder.save(str(encoder_file))
        final_model_a.save(str(model_a_file))
        final_model_b.save(str(model_b_file))
    except Exception as e:
        raise RuntimeError(f"Failed to save models: {e}")

    # Metadata - compute metrics efficiently
    acc_a_mean = sum(acc_a) / len(acc_a) if acc_a else 0.0
    f1_a_mean = sum(f1_a) / len(f1_a) if f1_a else 0.0
    acc_b_mean = sum(acc_b) / len(acc_b) if acc_b else 0.0
    f1_b_mean = sum(f1_b) / len(f1_b) if f1_b else 0.0
    
    meta = {
        "version": version_str,
        "trained_on": datetime.now().isoformat(),
        "encoder": encoder_type,
        "model_a": {"algorithm": "random_forest", "accuracy": acc_a_mean, "f1_macro": f1_a_mean},
        "model_b": {"algorithm": "logistic_regression", "accuracy": acc_b_mean, "f1_macro": f1_b_mean},
        "evaluation": {"validation_strategy": "kfold", "k": 5},
        "training_data": {"total_rows": len(labeled_df), "source_file": str(xlsx_path)},
        "notes": str(notes)[:500],  # Limit notes length
    }

    # Save metadata
    try:
        metadata_path = models_dir / "metadata.yaml"
        if not str(metadata_path.resolve()).startswith(str(models_dir.resolve())):
            raise ValueError("Invalid metadata path")
        save_metadata(metadata_path, meta)
    except Exception as e:
        raise RuntimeError(f"Failed to save metadata: {e}")

    print("\n✅ Training complete. Models and metadata saved.")
