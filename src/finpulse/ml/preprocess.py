"""
Handles preprocessing of transaction data for model training and inference.

Responsibilities:
 - Load the 'Details' worksheet from the Excel workbook
 - Extract relevant columns (Transaction Description, Automated Trans. Category, Transaction Type, Category, Subcategory)
 - Split labeled (for training) and unlabeled (for inference) datasets
 - Clean and normalize text fields
"""

import pandas as pd
from typing import Tuple


def load_and_prepare_details(xlsx_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the Details worksheet and splits into labeled and unlabeled datasets.
    """
    df = pd.read_excel(xlsx_path, sheet_name="Details")

    # Normalize column names to avoid mismatch
    df.columns = [col.strip() for col in df.columns]

    # Ensure required columns exist
    required_cols = ["Transaction Description", "Automated Trans. Category", "Transaction Type", "Category", "Subcategory"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column missing: {col}")

    # Clean and unify text for description/category/type columns
    for col in ["Transaction Description", "Automated Trans. Category", "Transaction Type"]:
        df[col] = df[col].astype(str).fillna("").str.lower().str.strip()

    # Separate labeled vs unlabeled rows
    labeled_df = df[df["Category"].notna() & df["Subcategory"].notna()].copy()
    unlabeled_df = df[df["Category"].isna() | df["Subcategory"].isna()].copy()

    return labeled_df, unlabeled_df
