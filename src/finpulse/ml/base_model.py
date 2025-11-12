"""
Base model class with common functionality for ML models.
"""

import joblib
import os
from .model_factory import ModelFactory


class BaseModel:
    """Base class for ML models with common save/load functionality."""
    
    def __init__(self, algorithm: str, hyperparameters: dict = None):
        self.algorithm = algorithm
        self.hyperparameters = hyperparameters or {}
        self.model = None
    
    def _create_model(self):
        """Create model instance using factory."""
        return ModelFactory.create_model(self.algorithm, self.hyperparameters)
    
    def train(self, X, y):
        """Train the model."""
        if self.model is None:
            self.model = self._create_model()
        self.model.fit(X, y)
    
    def predict(self, X):
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        return self.model.predict(X)
    
    def save(self, path: str):
        """Save model to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
    
    def load(self, path: str):
        """Load model from disk."""
        self.model = joblib.load(path)