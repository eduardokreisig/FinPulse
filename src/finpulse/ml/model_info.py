"""
Utility to display information about available ML models and their parameters.

This module is used internally by the CLI. Use the main CLI instead:
    python -m src.finpulse.main ml --help
"""

import sys
from .config_validator import MLConfigValidator
from .model_factory import ModelFactory


def print_algorithm_info(algorithm: str):
    """Print detailed information about a specific algorithm."""
    info = MLConfigValidator.get_model_info(algorithm)
    if not info:
        print(f"❌ Unknown algorithm: {algorithm}")
        return
    
    print(f"\n📊 {algorithm.upper()}")
    print("=" * (len(algorithm) + 4))
    print(f"Description: {info['description']}")
    print(f"\nValid hyperparameters:")
    for param in info['valid_parameters']:
        print(f"  - {param}")


def print_all_algorithms():
    """Print information about all supported algorithms."""
    algorithms = ModelFactory.get_supported_algorithms()
    
    print("🤖 FinPulse ML - Supported Algorithms")
    print("=" * 40)
    
    for algorithm in algorithms:
        print_algorithm_info(algorithm)
        print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1:
        algorithm = sys.argv[1].lower()
        print_algorithm_info(algorithm)
    else:
        print_all_algorithms()