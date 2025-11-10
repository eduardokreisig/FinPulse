"""
Model A - Classification predictor

Uses RandomForestClassifier to predict 'Classification' column values.
"""

import joblib
import os
from sklearn.ensemble import RandomForestClassifier


class ClassificationModel:
    def __init__(self):
        # RandomForest chosen for robustness on small-medium tabular data
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            n_jobs=-1,
            random_state=42
        )

    def train(self, X, y):
        """Train the RandomForest classifier."""
        self.model.fit(X, y)

    def predict(self, X):
        """Predict classifications."""
        return self.model.predict(X)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)
