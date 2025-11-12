"""
CategoryModel - Category predictor

Uses RandomForestClassifier to predict 'Category' column values.
"""

from sklearn.ensemble import RandomForestClassifier
from .base_model import BaseModel


class CategoryModel(BaseModel):
    def _create_model(self):
        """Create RandomForest classifier."""
        # RandomForest chosen for robustness on small-medium tabular data
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            n_jobs=-1,
            random_state=42
        )
