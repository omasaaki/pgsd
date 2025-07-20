"""Main entry point for PGSD application.

This module provides the main application entry point that integrates
all PGSD components including CLI, configuration, logging, and error handling.
"""

import sys
import logging
import signal
import atexit
from typing import Optional, List
from pathlib import Path

from .cli.main import CLIManager
from .utils.log_config import get_default_config
from .exceptions.base import PGSDError
from .exceptions.config import ConfigurationError
from . import __version__


# Global state for cleanup
_cleanup_callbacks = []


def register_cleanup(callback):
    """Register cleanup callback."""
    if callback not in _cleanup_callbacks:
        _cleanup_callbacks.append(callback)


def cleanup():
    """Execute all cleanup callbacks."""
    for callback in _cleanup_callbacks:
        try:
            callback()
        except Exception as e:
            try:
                print(f"Warning: Cleanup error: {e}", file=sys.stderr)
            except Exception:
                # If stderr write fails, silently continue
                pass


def signal_handler(signum, frame):
    """Handle signals gracefully."""
    try:
        print(f"\nReceived signal {signum}, shutting down...", file=sys.stderr)
    except Exception:
        pass  # If stderr write fails, continue
    
    try:
        cleanup()
    except Exception:
        pass  # If cleanup fails, still exit
    
    sys.exit(128 + signum)


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    try:
        # Signal handlers only work in main thread
        import threading
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
    except (ValueError, OSError, RuntimeError):
        # Signal setup may fail in some environments (tests, threads, etc.)
        pass


def setup_application():
    """Setup application environment."""
    # Register cleanup to run on exit
    try:
        atexit.register(cleanup)
    except Exception:
        pass  # Continue if atexit registration fails
    
    # Setup signal handlers
    try:
        setup_signal_handlers()
    except Exception:
        pass  # Continue if signal setup fails
    
    # Setup basic logging (CLI will configure detailed logging)
    try:
        log_config = get_default_config()
        log_config.level = "WARNING"
        logging.basicConfig(level=getattr(logging, log_config.level))
    except Exception:
        pass  # Continue if logging setup fails


def main(args: Optional[List[str]] = None) -> int:
    """Main application entry point.
    
    This function serves as the primary entry point for the PGSD application.
    It coordinates initialization, CLI execution, error handling, and cleanup.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Setup application environment
        setup_application()
        
        # Initialize and run CLI
        cli_manager = CLIManager()
        exit_code = cli_manager.run(args)
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # 128 + SIGINT
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2  # Configuration error exit code
        
    except PGSDError as e:
        print(f"PGSD error: {e}", file=sys.stderr)
        return 1  # General application error
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        
        # In debug mode, show full traceback
        if '--verbose' in (args or sys.argv[1:]):
            import traceback
            traceback.print_exc()
            
        return 1  # Unexpected error
        
    finally:
        # Ensure cleanup runs
        try:
            cleanup()
        except Exception:
            pass  # Don't let cleanup errors affect the exit code


def console_entry_point():
    """Entry point for console script (pgsd command).
    
    This function is called when PGSD is installed as a package and
    executed using the 'pgsd' command.
    """
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
