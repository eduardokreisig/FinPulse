"""Main application runner and orchestration."""

import sys
import traceback
from pathlib import Path

from .processor import process_source
from ..config.loader import get_log_directory, load_config
from ..ui.interactive import get_interactive_config, get_yes_no
from ..utils.logging_utils import Tee, setup_logging, utc_log_name
from ..utils.path_utils import create_timestamped_copy, get_timestamp


def setup_log_file(log_dir: Path, is_dry_run: bool):
    """Setup log file if log directory is specified."""
    if not log_dir:
        return None, None, None

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logfile = log_dir / utc_log_name(is_dry_run)
        log_fp = open(logfile, "w", encoding="utf-8")
        orig_stdout = sys.stdout
        tee = Tee(orig_stdout, log_fp)
        sys.stdout = tee
        print(f"[logging to] {logfile}")
        return log_fp, orig_stdout, tee
    except (OSError, PermissionError) as e:
        print(f"Failed to setup logging to {log_dir}: {e}")
        raise


def update_config_with_interactive(cfg: dict, interactive_config: dict):
    """Update configuration with interactive inputs."""
    workspace_path = Path(interactive_config['workspace']).resolve()
    cfg['target_workbook'] = str(workspace_path / interactive_config['workbook'])
    cfg['log_dir'] = interactive_config['logs']

    # Update source file paths to use new inputs folder
    inputs_path = Path(interactive_config['inputs'])
    for src_name, src_cfg in cfg.get('sources', {}).items():
        if 'files' in src_cfg:
            # Replace the base path in file globs
            updated_files = []
            for file_pattern in src_cfg['files']:
                # Extract the relative part after 'Inputs'
                pattern_path = Path(file_pattern)
                if 'Inputs' in pattern_path.parts:
                    inputs_idx = pattern_path.parts.index('Inputs')
                    relative_part = Path(*pattern_path.parts[inputs_idx+1:])
                    new_pattern = inputs_path / relative_part
                    updated_files.append(str(new_pattern))
                else:
                    updated_files.append(file_pattern)
            src_cfg['files'] = updated_files


def print_summary(sources_processed: int, sources_with_data: int, total_accounts: int, 
                 total_details: int, source_names: list, existing_counts: list, 
                 total_preexisting: int, total_deduped: int, total_nat: int):
    """Print processing summary."""
    print(f"\nSummary: {sources_processed} sources processed, {sources_with_data} had data")
    print(f"per-account added={total_accounts}, details added={total_details}")
    existing_breakdown = dict(zip(source_names, existing_counts))
    print(f"Pre-existing by account: {existing_breakdown}")
    print(f"Pre-existing rows={total_preexisting}, Deduped rows={total_deduped}, NaT (Not a Time) total={total_nat}")


def run_ml_inference_if_requested(cfg: dict, xlsx_path: str, has_new_data: bool):
    """Run ML inference if user confirms and there's new data."""
    if not has_new_data:
        return
    
    if get_yes_no("Run and ingest Machine Learning predictions for Classification and Type columns?", False):
        try:
            from ..ml.pipeline import run_ml_pipeline
            run_ml_pipeline(cfg, str(xlsx_path))
        except ImportError:
            print("⚠️ ML module not available. Skipping ML inference.")
        except Exception as e:
            print(f"⚠️ ML inference failed: {e}")


def create_working_copy(original_xlsx: Path) -> Path:
    """Create timestamped copy with error handling."""
    try:
        xlsx = create_timestamped_copy(original_xlsx)
        print(f"Working Copy: {xlsx}")
        return xlsx
    except (FileNotFoundError, OSError, PermissionError) as e:
        print(f"Error creating timestamped copy: {e}")
        if not get_yes_no("Continue with original file?", False):
            raise
        return original_xlsx


def check_discrepancies(total_accounts: int, total_details: int, source_results: list):
    """Check and report deduplication discrepancies."""
    if total_accounts != total_details:
        print(f"\nWARNING: Deduplication mismatch - per-account: {total_accounts}, details: {total_details}")
        discrepancies = [(name, acct, det) for name, acct, det in source_results if acct != det]
        if discrepancies:
            print("Accounts with discrepancies:")
            for name, acct_added, det_added in discrepancies:
                print(f"  {name}: per-account={acct_added}, details={det_added}")


def run_processing(cfg: dict, args, xlsx: Path, details_sheet: str):
    """Run the main processing loop."""
    total_details = 0
    total_accounts = 0
    total_preexisting = 0
    total_deduped = 0
    total_nat = 0
    sources_processed = 0
    sources_with_data = 0
    source_results = []
    existing_counts = []

    for src_name, scfg in cfg["sources"].items():
        sources_processed += 1
        acct_added, det_added, nat_count, deduped_count, existing_records = process_source(
            src_name, scfg, xlsx, details_sheet, args)
        total_accounts += acct_added
        total_details += det_added
        total_nat += nat_count
        total_deduped += deduped_count
        total_preexisting += existing_records
        existing_counts.append(existing_records)
        source_results.append((src_name, acct_added, det_added))
        if acct_added > 0 or det_added > 0:
            sources_with_data += 1

    source_names = list(cfg["sources"].keys())
    print_summary(sources_processed, sources_with_data, total_accounts, total_details,
                 source_names, existing_counts, total_preexisting, total_deduped, total_nat)
    
    if xlsx.exists():
        print(f"Modified (after): {get_timestamp(xlsx)}")
    
    check_discrepancies(total_accounts, total_details, source_results)
    
    return (total_accounts, total_details, total_preexisting, total_deduped, total_nat, 
            sources_processed, sources_with_data, source_results, source_names, existing_counts)


def run_application(args):
    """Main application runner."""
    setup_logging()

    # Interactive mode if no config provided
    interactive_config = None
    if not args.config:
        interactive_config = get_interactive_config()
        args.config = interactive_config['config']
        args.start = args.start or interactive_config['start']
        args.end = args.end or interactive_config['end']
        args.log_dir = args.log_dir or interactive_config['logs']

    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file '{args.config}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Override config with interactive inputs if provided
    if interactive_config:
        update_config_with_interactive(cfg, interactive_config)

    log_dir = get_log_directory(cfg, args.log_dir)
    orig_stdout = sys.stdout
    log_fp = None
    tee = None

    try:
        log_fp, orig_stdout, tee = setup_log_file(log_dir, args.dry_run)

        original_xlsx = Path(cfg['target_workbook']).expanduser().resolve()
        details_sheet = cfg.get("details_sheet", "Details")

        print(f"Original Workbook: {original_xlsx}")
        if not original_xlsx.exists():
            print(f"  exists: False  size: 0 bytes")
            print(f"  modified: n/a")
            print(f"Warning: Target workbook '{original_xlsx}' does not exist")
            if not args.dry_run and not get_yes_no("Continue anyway?", False):
                sys.exit(1)
            xlsx = original_xlsx  # Use original path if it doesn't exist
        else:
            print(f"  exists: True  size: {original_xlsx.stat().st_size} bytes")
            print(f"  modified: {get_timestamp(original_xlsx)}")
            
            # Create timestamped copy for processing
            if not args.dry_run:
                try:
                    xlsx = create_working_copy(original_xlsx)
                except Exception as e:
                    print(f"Failed to create working copy: {e}")
                    sys.exit(1)
            else:
                xlsx = original_xlsx  # Use original for dry runs

        try:
            results = run_processing(cfg, args, xlsx, details_sheet)
        except Exception as e:
            print(f"Processing failed: {e}")
            return
        
        # Run ML inference after successful processing (non-dry-run only)
        if not args.dry_run:
            run_ml_inference_if_requested(cfg, str(xlsx), results[0] > 0 or results[1] > 0)
        
        if args.dry_run:
            print("(dry-run) No changes written.")
            total_accounts, total_details = results[0], results[1]
            if total_accounts > 0 or total_details > 0:
                if get_yes_no("\nProceed with real import?", False):
                    # Create timestamped copy for real import
                    if original_xlsx.exists():
                        try:
                            xlsx = create_working_copy(original_xlsx)
                            print(f"\n=== REAL IMPORT ===")
                        except Exception as e:
                            print(f"Failed to create working copy for real import: {e}")
                            return
                    # Re-run without dry-run
                    args.dry_run = False
                    final_results = run_processing(cfg, args, xlsx, details_sheet)
                    final_accounts, final_details = final_results[0], final_results[1]
                    final_preexisting, final_deduped, final_nat = final_results[2], final_results[3], final_results[4]
                    final_source_results = final_results[7]
                    print(f"\nFinal: per-account added={final_accounts}, details added={final_details}")
                    print(f"Pre-existing rows={final_preexisting}, Deduped rows={final_deduped}, NaT (Not a Time) total={final_nat}")
                    check_discrepancies(final_accounts, final_details, final_source_results)
                    
                    # Run ML inference after successful real import
                    run_ml_inference_if_requested(cfg, str(xlsx), final_accounts > 0 or final_details > 0)
                    
                    print("Done.")
        else:
            print("Done.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        import logging
        logging.error(f"Application error: {e}")
        if hasattr(args, 'debug') and getattr(args, 'debug', False):
            print(traceback.format_exc())
        return
    finally:
        # Restore stdout first
        if tee:
            tee.close()
        sys.stdout = orig_stdout

        # Then close the log file
        if log_fp and not log_fp.closed:
            try:
                log_fp.close()
            except (OSError, IOError):
                pass  # Ignore errors during cleanup