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
def load_and_prepare_details(
    xlsx_path: str,
    details_sheet: str,
    columns: dict,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the Details worksheet and splits into labeled and unlabeled datasets.
    """
    c_description = columns["description"]
    c_automated_category = columns["automated_category"]
    c_transaction_type = columns["transaction_type"]
    c_category = columns["category"]
    c_subcategory = columns["subcategory"]

    df = pd.read_excel(xlsx_path, sheet_name=details_sheet)

    # Normalize column names to avoid mismatch
    df.columns = [c.strip() for c in df.columns]

    # Ensure required columns exist
    required_cols = [c_description, c_automated_category, c_transaction_type, c_category, c_subcategory]
    for col_name in required_cols:
        if col_name not in df.columns:
            raise ValueError(f"Required column missing: {col_name}")

    # Clean and unify text for description/category/type columns
    for col_name in [c_description, c_automated_category, c_transaction_type]:
        df[col_name] = df[col_name].astype(str).fillna("").str.lower().str.strip()

    # Separate labeled vs unlabeled rows
    labeled_df = df[df[c_category].notna() & df[c_subcategory].notna()].copy()
    unlabeled_df = df[df[c_category].isna() | df[c_subcategory].isna()].copy()

    return labeled_df, unlabeled_df
