"""
SubCategoryModel - Subcategory predictor

Uses Multinomial Logistic Regression to predict 'Subcategory' column values.
"""

from sklearn.linear_model import LogisticRegression
from .base_model import BaseModel


class SubCategoryModel(BaseModel):
    def _create_model(self):
        """Create Logistic Regression model."""
        # Logistic Regression works well for categorical multi-class problems
        return LogisticRegression(
            solver="lbfgs",
            max_iter=500,
            n_jobs=-1,
            random_state=42
        )
