"""
Model factory for creating ML models based on configuration.

Supports multiple algorithms with configurable hyperparameters and validation.
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.tree import DecisionTreeClassifier


class ModelValidationError(Exception):
    """Raised when model configuration is invalid."""
    pass


class ModelFactory:
    """Factory for creating ML models with validation."""
    
    SUPPORTED_ALGORITHMS = {
        'random_forest': {
            'class': RandomForestClassifier,
            'valid_params': {
                'n_estimators', 'max_depth', 'min_samples_split', 'min_samples_leaf',
                'max_features', 'bootstrap', 'n_jobs', 'random_state', 'class_weight'
            }
        },
        'logistic_regression': {
            'class': LogisticRegression,
            'valid_params': {
                'penalty', 'dual', 'tol', 'C', 'fit_intercept', 'intercept_scaling',
                'class_weight', 'random_state', 'solver', 'max_iter', 'multi_class',
                'verbose', 'warm_start', 'n_jobs', 'l1_ratio'
            }
        },
        'svm': {
            'class': SVC,
            'valid_params': {
                'C', 'kernel', 'degree', 'gamma', 'coef0', 'shrinking', 'probability',
                'tol', 'cache_size', 'class_weight', 'verbose', 'max_iter',
                'decision_function_shape', 'break_ties', 'random_state'
            }
        },
        'naive_bayes': {
            'class': MultinomialNB,
            'valid_params': {
                'alpha', 'fit_prior', 'class_prior'
            }
        },
        'decision_tree': {
            'class': DecisionTreeClassifier,
            'valid_params': {
                'criterion', 'splitter', 'max_depth', 'min_samples_split',
                'min_samples_leaf', 'min_weight_fraction_leaf', 'max_features',
                'random_state', 'max_leaf_nodes', 'min_impurity_decrease',
                'class_weight', 'ccp_alpha'
            }
        }
    }
    
    @classmethod
    def create_model(cls, algorithm: str, hyperparameters: dict = None):
        """Create a model instance with validation."""
        if not algorithm:
            raise ModelValidationError("Algorithm must be specified")
        
        if algorithm not in cls.SUPPORTED_ALGORITHMS:
            supported = ', '.join(cls.SUPPORTED_ALGORITHMS.keys())
            raise ModelValidationError(
                f"Unsupported algorithm '{algorithm}'. Supported: {supported}"
            )
        
        model_info = cls.SUPPORTED_ALGORITHMS[algorithm]
        model_class = model_info['class']
        valid_params = model_info['valid_params']
        
        # Validate hyperparameters
        if hyperparameters:
            invalid_params = set(hyperparameters.keys()) - valid_params
            if invalid_params:
                raise ModelValidationError(
                    f"Invalid hyperparameters for {algorithm}: {invalid_params}. "
                    f"Valid parameters: {sorted(valid_params)}"
                )
            
            # Handle null values in YAML (converted to None)
            clean_params = {}
            for key, value in hyperparameters.items():
                if value == 'null' or value == 'None':
                    clean_params[key] = None
                else:
                    clean_params[key] = value
            
            return model_class(**clean_params)
        else:
            return model_class()
    
    @classmethod
    def get_supported_algorithms(cls):
        """Get list of supported algorithms."""
        return list(cls.SUPPORTED_ALGORITHMS.keys())
    
    @classmethod
    def get_valid_parameters(cls, algorithm: str):
        """Get valid parameters for an algorithm."""
        if algorithm not in cls.SUPPORTED_ALGORITHMS:
            raise ModelValidationError(f"Unsupported algorithm: {algorithm}")
        return sorted(cls.SUPPORTED_ALGORITHMS[algorithm]['valid_params'])