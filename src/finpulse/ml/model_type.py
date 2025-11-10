"""
Model B - Type predictor

Uses Multinomial Logistic Regression to predict 'Type' column values.
"""

from sklearn.linear_model import LogisticRegression
from .base_model import BaseModel


class TypeModel(BaseModel):
    def _create_model(self):
        """Create Logistic Regression model."""
        # Multinomial Logistic Regression works well for categorical multi-class problems
        return LogisticRegression(
            multi_class="multinomial",
            solver="lbfgs",
            max_iter=500,
            n_jobs=-1,
            random_state=42
        )
