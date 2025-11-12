"""Main entry point for FinPulse financial data ingestion."""

import argparse

from .core.runner import run_application


def main() -> None:
    """Main entry point."""
    ap = argparse.ArgumentParser(
        description="FinPulse (robust CSV defaults; no YAML change needed)"
    )
    
    # Add subcommands for ML
    subparsers = ap.add_subparsers(dest='command', help='Available commands')
    
    # Main import command (default)
    import_parser = subparsers.add_parser('import', help='Import financial data (default)')
    import_parser.add_argument("--config", default=None)
    import_parser.add_argument("--start", help="YYYY-MM-DD", default=None)
    import_parser.add_argument("--end", help="YYYY-MM-DD", default=None)
    import_parser.add_argument("--dry-run", action="store_true")
    import_parser.add_argument("--log-dir", default=None)
    import_parser.add_argument("--workspace", default=None)
    import_parser.add_argument("--workbook", default=None)
    import_parser.add_argument("--inputs", default=None)
    
    # ML subcommand
    ml_parser = subparsers.add_parser('ml', help='Machine learning operations')
    ml_subparsers = ml_parser.add_subparsers(dest='ml_command', help='ML commands')
    
    # ML train
    train_parser = ml_subparsers.add_parser('train', help='Train ML models')
    train_parser.add_argument('--input', required=True, help='Input Excel workbook path')
    train_parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    
    # ML infer
    infer_parser = ml_subparsers.add_parser('infer', help='Run ML inference')
    infer_parser.add_argument('--input', required=True, help='Input Excel workbook path')
    infer_parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    
    # For backward compatibility, also accept old-style arguments
    ap.add_argument("--config", default=None)
    ap.add_argument("--start", help="YYYY-MM-DD", default=None)
    ap.add_argument("--end", help="YYYY-MM-DD", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--workspace", default=None)
    ap.add_argument("--workbook", default=None)
    ap.add_argument("--inputs", default=None)
    
    args = ap.parse_args()
    
    # Handle ML commands
    if args.command == 'ml':
        try:
            if args.ml_command == 'train':
                from .ml.train import train_models
                from .ui.interactive import get_ml_training_config
                
                notes, bump_type = get_ml_training_config()
                train_models(args.config, args.input, bump_type, notes)
                return
                
            elif args.ml_command == 'infer':
                from .ml.pipeline import run_ml_pipeline
                from .config.loader import load_config
                
                cfg = load_config(args.config)
                run_ml_pipeline(cfg, args.input)
                return
        except Exception as e:
            print(f"ML operation failed: {e}")
            return
    
    # Default to import command
    run_application(args)


if __name__ == "__main__":
    main()