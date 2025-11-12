"""
Utility functions for:
 - Model version bumping
 - Metrics computation
 - Confusion matrix plotting
 - Safe metadata persistence
"""

import os
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import yaml
from packaging import version
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, accuracy_score, f1_score


def bump_model_version(metadata_path: Path, bump_type: str = "minor") -> str:
    """Increment semantic version number for new training runs."""
    if not metadata_path.exists():
        return "1.0.0"

    with open(metadata_path, "r") as f:
        meta = yaml.safe_load(f)

    current = version.parse(meta.get("version", "1.0.0"))

    if bump_type == "major":
        new_ver = f"{current.major + 1}.0.0"
    elif bump_type == "minor":
        new_ver = f"{current.major}.{current.minor + 1}.0"
    else:
        new_ver = f"{current.major}.{current.minor}.{current.micro + 1}"

    return new_ver


def evaluate_and_plot(y_true, y_pred, label: str, output_dir: Path, version_str: str):
    """Compute accuracy, F1-score, and confusion matrix; save results."""
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")

    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap="Blues")
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / f"confusion_matrix_{label}_v{version_str}.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()

    return acc, f1, str(plot_path)


def save_metadata(metadata_path: Path, data: dict):
    """Write metadata.yaml and archive previous one in history/."""
    os.makedirs(metadata_path.parent / "history", exist_ok=True)
    if metadata_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived = metadata_path.parent / "history" / f"metadata_{timestamp}.yaml"
        os.rename(metadata_path, archived)
    with open(metadata_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)