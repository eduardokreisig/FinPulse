"""
Base model class with common functionality for ML models.
"""

import joblib
import os
from abc import ABC, abstractmethod


class BaseModel(ABC):
    """Base class for ML models with common save/load functionality."""
    
    def __init__(self):
        self.model = None
    
    @abstractmethod
    def _create_model(self):
        """Create the specific model instance. Must be implemented by subclasses."""
        pass
    
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