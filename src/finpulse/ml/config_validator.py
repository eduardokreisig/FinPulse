"""
Configuration validator for ML settings.

Validates ML configuration including algorithms, hyperparameters, and features.
"""

from .model_factory import ModelFactory, ModelValidationError


class MLConfigValidator:
    """Validates ML configuration settings."""
    
    VALID_TEXT_ENCODERS = {'tfidf', 'sbert'}
    
    @classmethod
    def validate_ml_config(cls, ml_config: dict):
        """Validate complete ML configuration."""
        errors = []
        
        # Validate text encoder
        text_encoder = ml_config.get('text_encoder', 'tfidf')
        if text_encoder not in cls.VALID_TEXT_ENCODERS:
            errors.append(f"Invalid text_encoder '{text_encoder}'. Valid options: {cls.VALID_TEXT_ENCODERS}")
        
        # Validate rare label threshold
        rare_threshold = ml_config.get('rare_label_threshold', 10)
        if not isinstance(rare_threshold, int) or rare_threshold < 1:
            errors.append("rare_label_threshold must be a positive integer")
        
        # Validate category model
        category_model = ml_config.get('category_model', {})
        category_errors = cls._validate_model_config('category_model', category_model)
        errors.extend(category_errors)
        
        # Validate subcategory model
        subcategory_model = ml_config.get('subcategory_model', {})
        subcategory_errors = cls._validate_model_config('subcategory_model', subcategory_model)
        errors.extend(subcategory_errors)
        
        if errors:
            raise ModelValidationError(f"ML configuration errors:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    @classmethod
    def _validate_model_config(cls, model_name: str, model_config: dict):
        """Validate individual model configuration."""
        errors = []
        
        if not model_config:
            return errors
        
        # Validate algorithm
        algorithm = model_config.get('algorithm')
        if not algorithm:
            errors.append(f"{model_name}: algorithm is required")
            return errors
        
        if algorithm not in ModelFactory.get_supported_algorithms():
            supported = ModelFactory.get_supported_algorithms()
            errors.append(f"{model_name}: unsupported algorithm '{algorithm}'. Supported: {supported}")
            return errors
        
        # Validate hyperparameters
        hyperparams = model_config.get('hyperparameters', {})
        if hyperparams:
            try:
                # Test model creation to validate hyperparameters
                ModelFactory.create_model(algorithm, hyperparams)
            except ModelValidationError as e:
                errors.append(f"{model_name}: {str(e)}")
            except Exception as e:
                errors.append(f"{model_name}: invalid hyperparameters - {str(e)}")
        
        # Validate features
        features = model_config.get('features', [])
        if not isinstance(features, list):
            errors.append(f"{model_name}: features must be a list")
        elif not features:
            errors.append(f"{model_name}: at least one feature is required")
        
        return errors
    
    @classmethod
    def get_model_info(cls, algorithm: str):
        """Get information about a specific algorithm."""
        try:
            valid_params = ModelFactory.get_valid_parameters(algorithm)
            return {
                'algorithm': algorithm,
                'valid_parameters': valid_params,
                'description': cls._get_algorithm_description(algorithm)
            }
        except ModelValidationError:
            return None
    
    @classmethod
    def _get_algorithm_description(cls, algorithm: str):
        """Get description for an algorithm."""
        descriptions = {
            'random_forest': 'Ensemble method using multiple decision trees. Good for tabular data.',
            'logistic_regression': 'Linear model for classification. Fast and interpretable.',
            'svm': 'Support Vector Machine. Effective for high-dimensional data.',
            'naive_bayes': 'Probabilistic classifier based on Bayes theorem. Fast and simple.',
            'decision_tree': 'Tree-based model. Highly interpretable but prone to overfitting.'
        }
        return descriptions.get(algorithm, 'No description available')