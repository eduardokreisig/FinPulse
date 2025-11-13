"""
Provides abstraction for text vectorization:
 - TF-IDF (default)
 - Sentence-BERT (future support)

The encoder is configured via config.yaml (ml.text_encoder).
"""

from sklearn.feature_extraction.text import TfidfVectorizer
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SBERT_AVAILABLE = False
import numpy as np
import joblib
import os


class TextEncoder:
    def __init__(self, method: str = "tfidf"):
        self.method = method.lower()
        self.vectorizer = None

    def fit(self, text_series):
        """Fit encoder on text data."""
        if self.method == "tfidf":
            self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            self.vectorizer.fit(text_series)
        elif self.method == "sbert":
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
            self.vectorizer = SentenceTransformer("all-MiniLM-L6-v2")
        else:
            raise ValueError(f"Unknown encoding method: {self.method}")

    def transform(self, text_series):
        """Transform text into embeddings or TF-IDF features."""
        if self.method == "tfidf":
            return self.vectorizer.transform(text_series)
        elif self.method == "sbert":
            return np.array(self.vectorizer.encode(text_series.tolist(), show_progress_bar=False))
        else:
            raise ValueError(f"Unknown encoding method: {self.method}")

    def save(self, path: str):
        """Persist encoder to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.vectorizer, path)

    def load(self, path: str):
        """Load encoder from disk."""
        self.vectorizer = joblib.load(path)
