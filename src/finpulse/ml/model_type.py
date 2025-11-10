"""
Model B - Type predictor

Uses Multinomial Logistic Regression to predict 'Type' column values.
"""

import joblib
import os
from sklearn.linear_model import LogisticRegression


class TypeModel:
    def __init__(self):
        # Multinomial Logistic Regression works well for categorical multi-class problems
        self.model = LogisticRegression(
            multi_class="multinomial",
            solver="lbfgs",
            max_iter=500,
            n_jobs=-1,
            random_state=42
        )

    def train(self, X, y):
        """Train the logistic regression model."""
        self.model.fit(X, y)

    def predict(self, X):
        """Predict transaction Type."""
        return self.model.predict(X)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)
